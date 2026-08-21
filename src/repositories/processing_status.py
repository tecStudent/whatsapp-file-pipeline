from datetime import UTC, datetime
from threading import Lock
from typing import Protocol

from redis import Redis

from src.config import Settings
from src.models.processing import ProcessingRecord, ProcessingStatus
from src.models.webhook import DocumentEvent


class ProcessingStatusStore(Protocol):
    """Persistence contract for processing state and idempotency."""

    def register_received(self, event: DocumentEvent) -> bool: ...

    def claim(self, message_id: str, task_id: str) -> bool: ...

    def update_status(
        self,
        message_id: str,
        status: ProcessingStatus,
        error: str | None = None,
    ) -> ProcessingRecord | None: ...

    def get(self, message_id: str) -> ProcessingRecord | None: ...

    def release(self, message_id: str) -> None: ...


class RedisProcessingStatusStore:
    """Redis-backed state store with atomic message registration."""

    key_prefix = "whatsapp-file-pipeline:message"

    def __init__(self, client: Redis, ttl_seconds: int) -> None:
        self.client = client
        self.ttl_seconds = ttl_seconds

    def register_received(self, event: DocumentEvent) -> bool:
        record = ProcessingRecord(message_id=event.message_id, event=event)
        created = self.client.set(
            self._key(event.message_id),
            record.model_dump_json(),
            nx=True,
            ex=self.ttl_seconds,
        )
        return bool(created)

    def claim(self, message_id: str, task_id: str) -> bool:
        claim_key = self._claim_key(message_id)
        current_task_id = self.client.get(claim_key)
        if current_task_id == task_id:
            return True
        claimed = self.client.set(
            claim_key,
            task_id,
            nx=True,
            ex=self.ttl_seconds,
        )
        return bool(claimed)

    def update_status(
        self,
        message_id: str,
        status: ProcessingStatus,
        error: str | None = None,
    ) -> ProcessingRecord | None:
        record = self.get(message_id)
        if record is None:
            return None

        updated = record.model_copy(
            update={
                "status": status,
                "error": error,
                "updated_at": datetime.now(UTC),
            }
        )
        self.client.set(self._key(message_id), updated.model_dump_json(), xx=True, keepttl=True)
        return updated

    def get(self, message_id: str) -> ProcessingRecord | None:
        raw_record = self.client.get(self._key(message_id))
        if raw_record is None:
            return None
        return ProcessingRecord.model_validate_json(raw_record)

    def release(self, message_id: str) -> None:
        self.client.delete(self._key(message_id), self._claim_key(message_id))

    def _key(self, message_id: str) -> str:
        return f"{self.key_prefix}:{message_id}"

    def _claim_key(self, message_id: str) -> str:
        return f"{self.key_prefix}-claim:{message_id}"


class InMemoryProcessingStatusStore:
    """Thread-safe test implementation of the processing store."""

    def __init__(self) -> None:
        self.records: dict[str, ProcessingRecord] = {}
        self.claims: dict[str, str] = {}
        self._lock = Lock()

    def register_received(self, event: DocumentEvent) -> bool:
        with self._lock:
            if event.message_id in self.records:
                return False
            self.records[event.message_id] = ProcessingRecord(
                message_id=event.message_id,
                event=event,
            )
            return True

    def claim(self, message_id: str, task_id: str) -> bool:
        with self._lock:
            current_task_id = self.claims.get(message_id)
            if current_task_id is None:
                self.claims[message_id] = task_id
                return True
            return current_task_id == task_id

    def update_status(
        self,
        message_id: str,
        status: ProcessingStatus,
        error: str | None = None,
    ) -> ProcessingRecord | None:
        with self._lock:
            record = self.records.get(message_id)
            if record is None:
                return None
            updated = record.model_copy(
                update={
                    "status": status,
                    "error": error,
                    "updated_at": datetime.now(UTC),
                }
            )
            self.records[message_id] = updated
            return updated

    def get(self, message_id: str) -> ProcessingRecord | None:
        return self.records.get(message_id)

    def release(self, message_id: str) -> None:
        with self._lock:
            self.records.pop(message_id, None)
            self.claims.pop(message_id, None)


def create_processing_status_store(settings: Settings) -> RedisProcessingStatusStore:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    return RedisProcessingStatusStore(client, settings.processing_status_ttl_seconds)

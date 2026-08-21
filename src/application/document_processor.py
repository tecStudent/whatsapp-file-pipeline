import logging
from collections.abc import Callable
from typing import Any

from src.models.processing import ProcessingStatus
from src.models.webhook import DocumentEvent
from src.repositories.processing_status import ProcessingStatusStore

logger = logging.getLogger(__name__)


def process_document_placeholder(event: DocumentEvent) -> None:
    """Placeholder for the media download and storage tasks that follow."""

    logger.info(
        "Document %s is ready for downstream processing (media_id=%s)",
        event.message_id,
        event.media_id,
    )


def run_document_processing(
    event_payload: dict[str, Any],
    status_store: ProcessingStatusStore,
    processor: Callable[[DocumentEvent], None] = process_document_placeholder,
    task_id: str | None = None,
) -> dict[str, str]:
    """Run one document job and record its successful state transitions."""

    event = DocumentEvent.model_validate(event_payload)
    current_record = status_store.get(event.message_id)
    if current_record is None:
        raise LookupError(f"Processing record not found for {event.message_id}")
    if current_record.status is ProcessingStatus.COMPLETED:
        return {"message_id": event.message_id, "status": ProcessingStatus.COMPLETED}
    if task_id is not None and not status_store.claim(event.message_id, task_id):
        return {"message_id": event.message_id, "status": current_record.status}

    status_store.update_status(event.message_id, ProcessingStatus.PROCESSING)
    processor(event)
    status_store.update_status(event.message_id, ProcessingStatus.COMPLETED)
    return {"message_id": event.message_id, "status": ProcessingStatus.COMPLETED}

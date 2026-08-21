from unittest.mock import Mock

from redis import Redis

from src.models.webhook import DocumentEvent
from src.repositories.processing_status import RedisProcessingStatusStore


def document_event() -> DocumentEvent:
    return DocumentEvent(
        message_id="wamid.redis-test",
        media_id="media-id",
        sender="5511999999999",
        file_name="report.csv",
        mime_type="text/csv",
    )


def test_redis_registration_is_atomic_and_expires() -> None:
    client = Mock(spec=Redis)
    client.set.return_value = True
    store = RedisProcessingStatusStore(client, ttl_seconds=3600)

    created = store.register_received(document_event())

    assert created is True
    _, value = client.set.call_args.args
    assert '"status":"RECEIVED"' in value
    assert client.set.call_args.kwargs == {"nx": True, "ex": 3600}


def test_redis_registration_reports_duplicate() -> None:
    client = Mock(spec=Redis)
    client.set.return_value = None
    store = RedisProcessingStatusStore(client, ttl_seconds=3600)

    created = store.register_received(document_event())

    assert created is False


def test_redis_claim_allows_only_one_task_id() -> None:
    client = Mock(spec=Redis)
    client.get.side_effect = [None, "task-1", "task-1"]
    client.set.side_effect = [True, None]
    store = RedisProcessingStatusStore(client, ttl_seconds=3600)

    assert store.claim("wamid.redis-test", "task-1") is True
    assert store.claim("wamid.redis-test", "task-1") is True
    assert store.claim("wamid.redis-test", "task-2") is False

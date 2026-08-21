from unittest.mock import patch

import pytest

from src.application.document_processor import run_document_processing
from src.models.processing import ProcessingStatus
from src.models.webhook import DocumentEvent
from src.repositories.processing_status import InMemoryProcessingStatusStore
from src.worker.tasks import (
    RetryingDocumentTask,
    mark_document_failed,
    process_document_task,
)


def document_event() -> DocumentEvent:
    return DocumentEvent(
        message_id="wamid.processing-test",
        media_id="media-id",
        sender="5511999999999",
        timestamp=1787263200,
        file_name="report.csv",
        mime_type="text/csv",
    )


def test_document_processing_moves_to_completed() -> None:
    event = document_event()
    store = InMemoryProcessingStatusStore()
    observed_statuses: list[ProcessingStatus] = []
    store.register_received(event)

    def processor(_: DocumentEvent) -> None:
        record = store.get(event.message_id)
        assert record is not None
        observed_statuses.append(record.status)

    result = run_document_processing(event.model_dump(mode="json"), store, processor)

    record = store.get(event.message_id)
    assert observed_statuses == [ProcessingStatus.PROCESSING]
    assert record is not None
    assert record.status is ProcessingStatus.COMPLETED
    assert result == {"message_id": event.message_id, "status": "COMPLETED"}


def test_document_processing_keeps_processing_until_retry_or_final_failure() -> None:
    event = document_event()
    store = InMemoryProcessingStatusStore()
    store.register_received(event)

    def failing_processor(_: DocumentEvent) -> None:
        raise TimeoutError("temporary failure")

    with pytest.raises(TimeoutError, match="temporary failure"):
        run_document_processing(event.model_dump(mode="json"), store, failing_processor)

    record = store.get(event.message_id)
    assert record is not None
    assert record.status is ProcessingStatus.PROCESSING


def test_celery_task_has_automatic_retry_policy() -> None:
    assert RetryingDocumentTask.autoretry_for == (Exception,)
    assert RetryingDocumentTask.retry_kwargs == {"max_retries": 5}
    assert RetryingDocumentTask.retry_backoff is True
    assert RetryingDocumentTask.retry_backoff_max == 60
    assert RetryingDocumentTask.retry_jitter is True
    assert RetryingDocumentTask.acks_late is True


def test_terminal_failure_moves_job_to_failed() -> None:
    event = document_event()
    store = InMemoryProcessingStatusStore()
    store.register_received(event)

    mark_document_failed(
        event.model_dump(mode="json"),
        RuntimeError("retries exhausted"),
        store,
    )

    record = store.get(event.message_id)
    assert record is not None
    assert record.status is ProcessingStatus.FAILED
    assert record.error == "retries exhausted"


def test_different_task_cannot_process_claimed_message() -> None:
    event = document_event()
    store = InMemoryProcessingStatusStore()
    processed_by: list[str] = []
    store.register_received(event)

    first_result = run_document_processing(
        event.model_dump(mode="json"),
        store,
        lambda _: processed_by.append("first"),
        task_id="task-1",
    )
    second_result = run_document_processing(
        event.model_dump(mode="json"),
        store,
        lambda _: processed_by.append("second"),
        task_id="task-2",
    )

    assert first_result["status"] == "COMPLETED"
    assert second_result["status"] == "COMPLETED"
    assert processed_by == ["first"]


def test_retry_of_same_task_keeps_its_claim() -> None:
    event = document_event()
    store = InMemoryProcessingStatusStore()
    store.register_received(event)

    assert store.claim(event.message_id, "task-1") is True
    assert store.claim(event.message_id, "task-1") is True
    assert store.claim(event.message_id, "task-2") is False


def test_celery_task_wrapper_processes_payload() -> None:
    event = document_event()
    store = InMemoryProcessingStatusStore()
    store.register_received(event)

    with patch("src.worker.tasks._status_store", return_value=store):
        result = process_document_task.apply(
            args=[event.model_dump(mode="json")],
            task_id="task-eager-test",
            throw=True,
        )

    assert result.result == {"message_id": event.message_id, "status": "COMPLETED"}
    assert store.get(event.message_id).status is ProcessingStatus.COMPLETED

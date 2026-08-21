import logging
from typing import Any

from celery import Task

from src.application.document_processor import run_document_processing
from src.config import get_settings
from src.models.processing import ProcessingStatus
from src.repositories.processing_status import create_processing_status_store
from src.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _status_store():
    return create_processing_status_store(get_settings())


def mark_document_failed(
    event_payload: dict[str, Any],
    exc: BaseException,
    status_store=None,
) -> None:
    message_id = event_payload.get("message_id")
    if not isinstance(message_id, str):
        return
    (status_store or _status_store()).update_status(
        message_id,
        ProcessingStatus.FAILED,
        error=str(exc),
    )


class RetryingDocumentTask(Task):
    """Celery task policy for retries and terminal failure tracking."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5}
    retry_backoff = True
    retry_backoff_max = 60
    retry_jitter = True
    acks_late = True
    reject_on_worker_lost = True

    def on_failure(
        self,
        exc: BaseException,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        if args and isinstance(args[0], dict):
            try:
                mark_document_failed(args[0], exc)
            except Exception:
                logger.exception("Could not persist terminal FAILED status")

        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    bind=True,
    base=RetryingDocumentTask,
    name="whatsapp_file_pipeline.process_document",
)
def process_document_task(self: Task, event_payload: dict[str, Any]) -> dict[str, str]:
    return run_document_processing(
        event_payload,
        _status_store(),
        task_id=self.request.id,
    )

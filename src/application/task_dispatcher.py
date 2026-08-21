from typing import Protocol

from src.models.webhook import DocumentEvent


class TaskDispatcher(Protocol):
    """Contract used by the API to enqueue document processing."""

    def enqueue(self, event: DocumentEvent) -> str: ...


class CeleryTaskDispatcher:
    def enqueue(self, event: DocumentEvent) -> str:
        from src.worker.tasks import process_document_task

        result = process_document_task.apply_async(args=[event.model_dump(mode="json")])
        return result.id

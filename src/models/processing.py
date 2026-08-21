from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.models.webhook import DocumentEvent


class ProcessingStatus(StrEnum):
    """Lifecycle states for an asynchronous document job."""

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessingRecord(BaseModel):
    """Transient processing state kept in Redis."""

    message_id: str
    status: ProcessingStatus = ProcessingStatus.RECEIVED
    event: DocumentEvent
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

from typing import Literal

from pydantic import BaseModel


class DocumentEvent(BaseModel):
    """Normalized document message extracted from a Meta webhook payload."""

    message_id: str
    media_id: str
    sender: str
    timestamp: int | None = None
    file_name: str
    mime_type: str
    sha256: str | None = None
    caption: str | None = None


class WebhookAccepted(BaseModel):
    status: Literal["accepted"] = "accepted"
    documents_received: int
    documents_queued: int
    duplicates_ignored: int

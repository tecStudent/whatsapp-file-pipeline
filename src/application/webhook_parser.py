from typing import Any

from src.models.webhook import DocumentEvent


def extract_document_events(payload: dict[str, Any]) -> list[DocumentEvent]:
    """Extract supported document messages from a WhatsApp webhook payload."""

    documents: list[DocumentEvent] = []

    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue

        for change in entry.get("changes", []):
            if not isinstance(change, dict):
                continue

            value = change.get("value", {})
            if not isinstance(value, dict):
                continue

            for message in value.get("messages", []):
                document_event = _parse_document_message(message)
                if document_event is not None:
                    documents.append(document_event)

    return documents


def _parse_document_message(message: Any) -> DocumentEvent | None:
    if not isinstance(message, dict) or message.get("type") != "document":
        return None

    document = message.get("document")
    if not isinstance(document, dict):
        return None

    message_id = message.get("id")
    media_id = document.get("id")
    sender = message.get("from")

    if not all(isinstance(value, str) and value for value in (message_id, media_id, sender)):
        return None

    return DocumentEvent(
        message_id=message_id,
        media_id=media_id,
        sender=sender,
        timestamp=_parse_timestamp(message.get("timestamp")),
        file_name=document.get("filename") or f"document-{media_id}",
        mime_type=document.get("mime_type") or "application/octet-stream",
        sha256=document.get("sha256"),
        caption=document.get("caption"),
    )


def _parse_timestamp(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


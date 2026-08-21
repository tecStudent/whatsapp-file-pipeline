import hashlib
import hmac
import json
from typing import Any

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.application.task_dispatcher import TaskDispatcher
from src.application.webhook_parser import extract_document_events
from src.config import Settings
from src.models.webhook import DocumentEvent
from src.repositories.processing_status import InMemoryProcessingStatusStore

APP_SECRET = "test-app-secret"
VERIFY_TOKEN = "test-verify-token"


class RecordingTaskDispatcher(TaskDispatcher):
    def __init__(self, should_fail: bool = False) -> None:
        self.events: list[DocumentEvent] = []
        self.should_fail = should_fail

    def enqueue(self, event: DocumentEvent) -> str:
        if self.should_fail:
            raise ConnectionError("queue unavailable")
        self.events.append(event)
        return f"task-{event.message_id}"


def create_test_client(
    dispatcher: RecordingTaskDispatcher | None = None,
) -> tuple[TestClient, InMemoryProcessingStatusStore, RecordingTaskDispatcher]:
    settings = Settings(
        _env_file=None,
        whatsapp_app_secret=APP_SECRET,
        whatsapp_verify_token=VERIFY_TOKEN,
    )
    status_store = InMemoryProcessingStatusStore()
    task_dispatcher = dispatcher or RecordingTaskDispatcher()
    application = create_app(settings, status_store, task_dispatcher)
    return TestClient(application), status_store, task_dispatcher


def document_payload() -> dict[str, Any]:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "business-account-id",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "5511999999999",
                                    "id": "wamid.test-message-id",
                                    "timestamp": "1787263200",
                                    "type": "document",
                                    "document": {
                                        "id": "media-id-123",
                                        "filename": "report.csv",
                                        "mime_type": "text/csv",
                                        "sha256": "document-sha256",
                                        "caption": "Monthly report",
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def signed_headers(raw_body: bytes) -> dict[str, str]:
    digest = hmac.new(APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={digest}",
    }


def test_webhook_verification_returns_challenge() -> None:
    client, _, _ = create_test_client()

    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": VERIFY_TOKEN,
            "hub.challenge": "challenge-value",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-value"


def test_webhook_verification_rejects_invalid_token() -> None:
    client, _, _ = create_test_client()

    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "challenge-value",
        },
    )

    assert response.status_code == 403


def test_receive_webhook_accepts_valid_document() -> None:
    client, status_store, dispatcher = create_test_client()
    raw_body = json.dumps(document_payload(), separators=(",", ":")).encode()

    response = client.post("/webhook", content=raw_body, headers=signed_headers(raw_body))

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "documents_received": 1,
        "documents_queued": 1,
        "duplicates_ignored": 0,
    }
    assert status_store.get("wamid.test-message-id").status == "RECEIVED"
    assert [event.message_id for event in dispatcher.events] == ["wamid.test-message-id"]


def test_receive_webhook_rejects_invalid_signature() -> None:
    client, _, _ = create_test_client()
    raw_body = json.dumps(document_payload()).encode()

    response = client.post(
        "/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=invalid",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid webhook signature"}


def test_receive_webhook_rejects_invalid_json() -> None:
    client, _, _ = create_test_client()
    raw_body = b"not-json"

    response = client.post("/webhook", content=raw_body, headers=signed_headers(raw_body))

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid JSON payload"}


def test_receive_webhook_ignores_non_document_messages() -> None:
    client, _, _ = create_test_client()
    payload = document_payload()
    payload["entry"][0]["changes"][0]["value"]["messages"][0] = {
        "from": "5511999999999",
        "id": "wamid.text-message-id",
        "timestamp": "1787263200",
        "type": "text",
        "text": {"body": "Hello"},
    }
    raw_body = json.dumps(payload, separators=(",", ":")).encode()

    response = client.post("/webhook", content=raw_body, headers=signed_headers(raw_body))

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "documents_received": 0,
        "documents_queued": 0,
        "duplicates_ignored": 0,
    }


def test_receive_webhook_ignores_duplicate_message_id() -> None:
    client, _, dispatcher = create_test_client()
    raw_body = json.dumps(document_payload(), separators=(",", ":")).encode()
    headers = signed_headers(raw_body)

    first_response = client.post("/webhook", content=raw_body, headers=headers)
    duplicate_response = client.post("/webhook", content=raw_body, headers=headers)

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 200
    assert duplicate_response.json() == {
        "status": "accepted",
        "documents_received": 1,
        "documents_queued": 0,
        "duplicates_ignored": 1,
    }
    assert len(dispatcher.events) == 1


def test_receive_webhook_releases_message_when_queue_is_unavailable() -> None:
    dispatcher = RecordingTaskDispatcher(should_fail=True)
    client, status_store, _ = create_test_client(dispatcher)
    raw_body = json.dumps(document_payload(), separators=(",", ":")).encode()

    response = client.post("/webhook", content=raw_body, headers=signed_headers(raw_body))

    assert response.status_code == 503
    assert response.json() == {"detail": "Processing queue is unavailable"}
    assert status_store.get("wamid.test-message-id") is None


def test_extract_document_events_normalizes_payload() -> None:
    events = extract_document_events(document_payload())

    assert len(events) == 1
    assert events[0].model_dump() == {
        "message_id": "wamid.test-message-id",
        "media_id": "media-id-123",
        "sender": "5511999999999",
        "timestamp": 1787263200,
        "file_name": "report.csv",
        "mime_type": "text/csv",
        "sha256": "document-sha256",
        "caption": "Monthly report",
    }

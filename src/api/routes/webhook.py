import hmac
import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from src.api.dependencies import (
    get_processing_status_store,
    get_request_settings,
    get_task_dispatcher,
)
from src.api.security import is_valid_meta_signature
from src.application.task_dispatcher import TaskDispatcher
from src.application.webhook_parser import extract_document_events
from src.config import Settings
from src.models.webhook import WebhookAccepted
from src.repositories.processing_status import ProcessingStatusStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("", response_class=PlainTextResponse)
async def verify_webhook(
    settings: Annotated[Settings, Depends(get_request_settings)],
    mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    verify_token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
) -> PlainTextResponse:
    configured_token = settings.whatsapp_verify_token.get_secret_value()

    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WhatsApp webhook verification is not configured",
        )

    token_is_valid = verify_token is not None and hmac.compare_digest(
        verify_token,
        configured_token,
    )

    if mode != "subscribe" or not token_is_valid or challenge is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook verification failed",
        )

    return PlainTextResponse(content=challenge, status_code=status.HTTP_200_OK)


@router.post("", response_model=WebhookAccepted)
async def receive_webhook(
    request: Request,
    settings: Annotated[Settings, Depends(get_request_settings)],
    status_store: Annotated[
        ProcessingStatusStore,
        Depends(get_processing_status_store),
    ],
    task_dispatcher: Annotated[TaskDispatcher, Depends(get_task_dispatcher)],
    signature: Annotated[str | None, Header(alias="X-Hub-Signature-256")] = None,
) -> WebhookAccepted:
    app_secret = settings.whatsapp_app_secret.get_secret_value()

    if not app_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WhatsApp webhook signature validation is not configured",
        )

    raw_body = await request.body()

    if not is_valid_meta_signature(raw_body, signature, app_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    payload = _decode_payload(raw_body)
    documents = extract_document_events(payload)

    queued = 0
    duplicates = 0
    for document in documents:
        if not status_store.register_received(document):
            duplicates += 1
            continue

        try:
            task_dispatcher.enqueue(document)
        except Exception as exc:
            status_store.release(document.message_id)
            logger.exception("Could not enqueue document %s", document.message_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Processing queue is unavailable",
            ) from exc
        queued += 1

    logger.info(
        "Accepted webhook: received=%d queued=%d duplicates=%d",
        len(documents),
        queued,
        duplicates,
    )

    return WebhookAccepted(
        documents_received=len(documents),
        documents_queued=queued,
        duplicates_ignored=duplicates,
    )


def _decode_payload(raw_body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload must be a JSON object",
        )

    return payload

from fastapi import Request

from src.application.task_dispatcher import TaskDispatcher
from src.config import Settings
from src.repositories.processing_status import ProcessingStatusStore


def get_request_settings(request: Request) -> Settings:
    """Return the settings attached to the current FastAPI application."""

    return request.app.state.settings


def get_processing_status_store(request: Request) -> ProcessingStatusStore:
    return request.app.state.processing_status_store


def get_task_dispatcher(request: Request) -> TaskDispatcher:
    return request.app.state.task_dispatcher

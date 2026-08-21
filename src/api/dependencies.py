from fastapi import Request

from src.config import Settings


def get_request_settings(request: Request) -> Settings:
    """Return the settings attached to the current FastAPI application."""

    return request.app.state.settings


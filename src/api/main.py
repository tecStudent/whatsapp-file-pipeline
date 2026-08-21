from fastapi import FastAPI

from src.api.routes.health import router as health_router
from src.api.routes.webhook import router as webhook_router
from src.application.task_dispatcher import CeleryTaskDispatcher, TaskDispatcher
from src.config import Settings, get_settings
from src.repositories.processing_status import (
    ProcessingStatusStore,
    create_processing_status_store,
)


def create_app(
    settings: Settings | None = None,
    processing_status_store: ProcessingStatusStore | None = None,
    task_dispatcher: TaskDispatcher | None = None,
) -> FastAPI:
    application_settings = settings or get_settings()
    application = FastAPI(
        title=application_settings.app_name,
        description="API for receiving and processing WhatsApp file events.",
        version="0.3.0",
    )

    application.state.settings = application_settings
    application.state.processing_status_store = (
        processing_status_store or create_processing_status_store(application_settings)
    )
    application.state.task_dispatcher = task_dispatcher or CeleryTaskDispatcher()
    application.include_router(health_router)
    application.include_router(webhook_router)

    return application


app = create_app()

from fastapi import FastAPI

from src.api.routes.health import router as health_router
from src.api.routes.webhook import router as webhook_router
from src.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    application_settings = settings or get_settings()
    application = FastAPI(
        title=application_settings.app_name,
        description="API for receiving and processing WhatsApp file events.",
        version="0.2.0",
    )

    application.state.settings = application_settings
    application.include_router(health_router)
    application.include_router(webhook_router)

    return application


app = create_app()

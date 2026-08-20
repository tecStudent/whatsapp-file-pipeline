from fastapi import FastAPI


def create_app() -> FastAPI:
    application = FastAPI(
        title="WhatsApp File Pipeline API",
        description="API for receiving and processing WhatsApp file events.",
        version="0.1.0",
    )

    @application.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"message": "WhatsApp File Pipeline API is running"}

    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    return application


app = create_app()


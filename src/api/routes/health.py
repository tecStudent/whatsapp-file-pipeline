from fastapi import APIRouter

router = APIRouter()


@router.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"message": "WhatsApp File Pipeline API is running"}


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


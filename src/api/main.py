from fastapi import FastAPI

app = FastAPI(
    title="WhatsApp File Pipeline API",
    description="API local para o projeto WhatsApp File Pipeline.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "WhatsApp File Pipeline API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
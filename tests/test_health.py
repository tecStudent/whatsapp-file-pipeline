from fastapi.testclient import TestClient

from src.api.main import create_app

client = TestClient(create_app())


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "WhatsApp File Pipeline API is running"}


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

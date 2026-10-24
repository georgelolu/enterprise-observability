import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app" / "product-service"),
)

from main import app  # noqa: E402

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "product-service",
    }


def test_readiness_endpoint():
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_existing_product_is_returned():
    response = client.get("/products/101")

    assert response.status_code == 200
    assert response.json() == {
        "id": "101",
        "name": "Laptop",
        "price": 1200,
    }


def test_unknown_product_returns_404():
    response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_metrics_endpoint_is_available():
    response = client.get("/metrics/")

    assert response.status_code == 200
    assert "# HELP product_service_http_requests_total" in response.text

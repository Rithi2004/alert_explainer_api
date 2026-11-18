from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import Base, get_db
from main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Iterator[Session]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_create_alert(client: TestClient) -> None:
    response = client.post(
        "/alerts/",
        json={
            "title": "High CPU usage",
            "severity": "critical",
            "source": "web-server",
            "metric_name": "cpu_usage",
            "metric_value": 95.0,
            "threshold": 80.0,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["title"] == "High CPU usage"
    assert data["severity"] == "critical"
    assert data["metric_name"] == "cpu_usage"


def test_list_alerts(client: TestClient) -> None:
    alert = {
        "title": "High memory usage",
        "severity": "warning",
        "source": "worker",
        "metric_name": "memory_usage",
        "metric_value": 82.0,
        "threshold": 75.0,
    }
    client.post("/alerts/", json=alert)

    response = client.get("/alerts/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == alert["title"]
    assert data[0]["metric_name"] == alert["metric_name"]


def test_get_alert_by_id(client: TestClient) -> None:
    create_response = client.post(
        "/alerts/",
        json={
            "title": "Low disk space",
            "severity": "warning",
            "source": "database",
            "metric_name": "disk_usage",
            "metric_value": 91.0,
            "threshold": 85.0,
        },
    )
    alert_id = create_response.json()["id"]

    response = client.get(f"/alerts/{alert_id}")

    assert response.status_code == 200
    assert response.json()["id"] == alert_id
    assert response.json()["title"] == "Low disk space"


def test_explain_alert(client: TestClient) -> None:
    create_response = client.post(
        "/alerts/",
        json={
            "title": "High CPU usage",
            "severity": "critical",
            "source": "web-server",
            "metric_name": "cpu_usage",
            "metric_value": 95.0,
            "threshold": 80.0,
        },
    )
    alert_id = create_response.json()["id"]

    response = client.post(f"/alerts/{alert_id}/explain")

    assert response.status_code == 200
    data = response.json()
    assert data["alert_id"] == alert_id
    assert "critical" in data["explanation"]
    assert "cpu_usage" in data["explanation"]
    generated_at = datetime.fromisoformat(data["generated_at"])
    assert generated_at.tzinfo is not None

# --- Edge cases added manually ---

def _create_alert(client: TestClient, **overrides: str | float) -> dict:
    """Create an alert through the API and return its JSON response."""
    payload: dict[str, str | float] = {
        "title": "Test alert",
        "severity": "warning",
        "source": "test-source",
        "metric_name": "test_metric",
        "metric_value": 50.0,
        "threshold": 40.0,
    }
    payload.update(overrides)
    response = client.post("/alerts", json=payload)
    assert response.status_code == 201
    return response.json()

def test_explain_alert_for_nonexistent_id_returns_404(
    client: TestClient,
) -> None:
    response = client.post("/alerts/999/explain")

    assert response.status_code == 404
    assert response.json()["detail"] == "Alert not found"

def test_explain_alert_when_metric_is_below_threshold(
    client: TestClient,
) -> None:
    alert = _create_alert(
        client,
        title="Connection pool below minimum",
        severity="warning",
        source="db-pool",
        metric_name="active_connections",
        metric_value=2,
        threshold=10,
    )

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert "fell below its threshold" in response.json()["explanation"]

def test_explain_alert_with_zero_threshold_does_not_crash(
    client: TestClient,
) -> None:
    alert = _create_alert(
        client,
        title="Unexpected traffic on idle endpoint",
        severity="info",
        source="edge-cache",
        metric_name="request_count",
        metric_value=5,
        threshold=0,
    )

    response = client.post(f"/alerts/{alert['id']}/explain")

    assert response.status_code == 200
    assert "threshold of 0.0" in response.json()["explanation"]


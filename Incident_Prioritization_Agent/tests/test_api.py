"""
API and Integration Tests for FastAPI Endpoints.
Verifies POST /prioritize, status codes, input validation, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from agent.api import app
from agent.config import PriorityLevel


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["auto_dispatch_authorized"] is False
    assert data["neighborhoods_loaded"] > 200


def test_prioritize_valid_critical_incident(client):
    payload = {
        "incident_id": "INC-TEST-001",
        "incident_type": "AGG ASSAULT",
        "immediate_danger": True,
        "serious_injury": True,
        "weapon_reported": True,
        "victim_count": 2,
        "neighborhood": "DOWNTOWN",
        "latitude": 33.7537,
        "longitude": -84.3863,
    }
    response = client.post("/prioritize", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Requirements 8 & 9: Return incident ID, priority score, priority level, recommended action
    assert data["incident_id"] == "INC-TEST-001"
    assert "priority_score" in data
    assert data["priority_level"] == PriorityLevel.CRITICAL.value
    assert "recommended_action" in data
    assert data["auto_dispatch_authorized"] is False

    # Requirements 12: Geofencing & Response Assignment integration readiness
    assert data["geofencing_integration"]["ready_for_geofencing"] is True
    assert data["geofencing_integration"]["perimeter_alert_recommended"] is True
    assert data["response_assignment_integration"]["ready_for_assignment"] is True
    assert data["response_assignment_integration"]["supervisor_review_required"] is True


def test_prioritize_with_missing_emergency_fields(client):
    """
    Requirement 4: Treat unknown emergency fields as missing, not false.
    """
    payload = {
        "incident_id": "INC-TEST-002",
        "incident_type": "BURGLARY-RESIDENCE",
        # immediate_danger, serious_injury, weapon_reported are omitted (None)
        "neighborhood": "MIDTOWN",
    }
    response = client.post("/prioritize", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["field_status"]["immediate_danger_status"] == "MISSING_UNKNOWN"
    assert data["field_status"]["missing_fields_count"] == 3
    assert data["auto_dispatch_authorized"] is False


def test_prioritize_input_validation_empty_id(client):
    """
    Requirement 10: Input validation and error handling.
    """
    payload = {
        "incident_id": "   ",  # Blank ID
        "incident_type": "AUTO THEFT",
    }
    response = client.post("/prioritize", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["auto_dispatch_authorized"] is False


def test_prioritize_input_validation_invalid_coordinates(client):
    """
    Requirement 10: Input validation on coordinate boundaries.
    """
    payload = {
        "incident_id": "INC-TEST-COORD",
        "incident_type": "AUTO THEFT",
        "latitude": 999.0,  # Invalid latitude
    }
    response = client.post("/prioritize", json=payload)
    assert response.status_code == 422


def test_prioritize_input_validation_negative_victims(client):
    """
    Requirement 10: Negative victim count rejected.
    """
    payload = {
        "incident_id": "INC-TEST-VICTIM",
        "incident_type": "AUTO THEFT",
        "victim_count": -5,
    }
    response = client.post("/prioritize", json=payload)
    assert response.status_code == 422


def test_prioritize_batch_endpoint(client):
    payload = {
        "incidents": [
            {
                "incident_id": "BATCH-1",
                "incident_type": "HOMICIDE",
                "immediate_danger": True,
            },
            {
                "incident_id": "BATCH-2",
                "incident_type": "LARCENY-NON VEHICLE",
                "immediate_danger": False,
                "serious_injury": False,
                "weapon_reported": False,
            },
        ]
    }
    response = client.post("/prioritize/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 2
    assert data["critical_count"] >= 1
    assert data["low_count"] >= 1


def test_neighborhoods_endpoints(client):
    response = client.get("/neighborhoods")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 200

    single_resp = client.get("/neighborhoods/DOWNTOWN")
    assert single_resp.status_code == 200
    assert single_resp.json()["neighborhood"] == "DOWNTOWN"


def test_evaluation_endpoint(client):
    """
    Requirement 5: Prototyping evaluation endpoint against historical proxy labels.
    """
    response = client.get("/evaluation?sample_size=100")
    assert response.status_code == 200
    data = response.json()
    assert "prototype_warning" in data
    assert "evaluated_sample_size" in data
    assert "per_class_metrics" in data
    assert "missing_emergency_fields_handled" in data

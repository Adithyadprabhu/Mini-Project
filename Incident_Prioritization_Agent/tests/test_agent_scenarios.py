"""
Automated tests for different incident scenarios (Requirement 11).
Tests scenarios across CRITICAL, HIGH, MEDIUM, LOW, missing fields,
and cross-agent integrations (Geofencing & Response Assignment).
"""

import pytest
from agent.config import PriorityLevel
from agent.schemas import IncidentInput
from agent.scoring_engine import PriorityScoringEngine


@pytest.fixture
def engine():
    return PriorityScoringEngine()


def test_scenario_critical_armed_violent_encounter(engine):
    """
    Scenario 1: CRITICAL
    Active armed robbery in progress with shots fired and serious injury in high-risk neighborhood.
    """
    incident = IncidentInput(
        incident_id="SCENARIO-CRITICAL-01",
        incident_type="ROBBERY-PEDESTRIAN",
        immediate_danger=True,
        serious_injury=True,
        weapon_reported=True,
        victim_count=1,
        neighborhood="DOWNTOWN",
        address="150 CARNEGIE WAY NW",
        latitude=33.7588,
        longitude=-84.3879,
    )
    result = engine.prioritize(incident)

    assert result.priority_level == PriorityLevel.CRITICAL
    assert result.priority_score >= 85.0
    assert "SUPERVISOR" in result.recommended_action
    assert result.auto_dispatch_authorized is False
    assert result.geofencing_integration.perimeter_alert_recommended is True
    assert "TACTICAL_SUPPORT" in result.response_assignment_integration.suggested_unit_types
    assert "EMS_ADVANCED_LIFE_SUPPORT" in result.response_assignment_integration.suggested_unit_types


def test_scenario_high_commercial_robbery_uninjured(engine):
    """
    Scenario 2: HIGH
    Commercial robbery where weapon is reported, but immediate bodily injury is verified false.
    """
    incident = IncidentInput(
        incident_id="SCENARIO-HIGH-01",
        incident_type="ROBBERY-COMMERCIAL",
        immediate_danger=True,
        serious_injury=False,
        weapon_reported=True,
        victim_count=1,
        neighborhood="BUCKHEAD",
        latitude=33.8400,
        longitude=-84.3800,
    )
    result = engine.prioritize(incident)

    assert result.priority_level in [PriorityLevel.HIGH, PriorityLevel.CRITICAL]
    assert result.priority_score >= 70.0
    assert result.auto_dispatch_authorized is False
    assert result.response_assignment_integration.supervisor_review_required is True


def test_scenario_medium_residential_burglary_cold(engine):
    """
    Scenario 3: MEDIUM
    Past residential burglary discovered upon return. Danger and injury ruled out.
    """
    incident = IncidentInput(
        incident_id="SCENARIO-MEDIUM-01",
        incident_type="BURGLARY-RESIDENCE",
        immediate_danger=False,
        serious_injury=False,
        weapon_reported=False,
        victim_count=1,
        neighborhood="OLD FOURTH WARD",
        latitude=33.7600,
        longitude=-84.3700,
    )
    result = engine.prioritize(incident)

    assert result.priority_level == PriorityLevel.MEDIUM
    assert 40.0 <= result.priority_score < 70.0
    assert "STANDARD_QUEUE" in result.recommended_action
    assert result.auto_dispatch_authorized is False


def test_scenario_low_larceny_from_vehicle(engine):
    """
    Scenario 4: LOW
    Theft from parked vehicle overnight. No weapon, no injury, no immediate danger.
    """
    incident = IncidentInput(
        incident_id="SCENARIO-LOW-01",
        incident_type="LARCENY-FROM VEHICLE",
        immediate_danger=False,
        serious_injury=False,
        weapon_reported=False,
        victim_count=1,
        neighborhood="MIDTOWN",
        latitude=33.7800,
        longitude=-84.3850,
    )
    result = engine.prioritize(incident)

    assert result.priority_level == PriorityLevel.LOW
    assert result.priority_score < 40.0
    assert "ROUTINE_ADMIN_REVIEW" in result.recommended_action
    assert result.auto_dispatch_authorized is False
    assert result.geofencing_integration.perimeter_alert_recommended is False


def test_scenario_missing_emergency_fields_cautionary_handling(engine):
    """
    Scenario 5: AMBIGUOUS INTAKE WITH MISSING EMERGENCY FIELDS
    Caller reports suspicious breaking glass and noises; call disconnects before
    immediate danger, injury, or weapon can be established.
    The agent must treat fields as MISSING (Requirement 4), apply uncertainty buffer,
    and flag for dispatcher callback rather than assuming danger is False.
    """
    incident = IncidentInput(
        incident_id="SCENARIO-MISSING-01",
        incident_type="BURGLARY",
        immediate_danger=None,
        serious_injury=None,
        weapon_reported=None,
        victim_count=1,
        neighborhood="INMAN PARK",
    )
    result = engine.prioritize(incident)

    assert result.field_status.data_completeness_level == "MINIMAL"
    assert result.field_status.missing_fields_count == 3
    assert result.scoring_breakdown.uncertainty_buffer > 0.0
    # Must NOT have treated them as verified False
    assert result.field_status.immediate_danger_status.value == "MISSING_UNKNOWN"
    assert result.field_status.serious_injury_status.value == "MISSING_UNKNOWN"
    assert result.field_status.weapon_reported_status.value == "MISSING_UNKNOWN"


def test_scenario_mass_casualty_incident(engine):
    """
    Scenario 6: MASS CASUALTY / MULTI-VICTIM INCIDENT
    Shots fired incident with 6 reported victims.
    """
    incident = IncidentInput(
        incident_id="SCENARIO-MASS-CASUALTY",
        incident_type="SHOTS FIRED",
        immediate_danger=True,
        serious_injury=True,
        weapon_reported=True,
        victim_count=6,
        neighborhood="DOWNTOWN",
        latitude=33.7550,
        longitude=-84.3900,
    )
    result = engine.prioritize(incident)

    assert result.priority_level == PriorityLevel.CRITICAL
    assert result.priority_score >= 95.0
    assert result.response_assignment_integration.minimum_personnel >= 2
    assert "EMS_ADVANCED_LIFE_SUPPORT" in result.response_assignment_integration.suggested_unit_types
    assert result.geofencing_integration.suggested_geofence_radius_meters == 1000


def test_scenario_geofencing_and_assignment_contract_compliance(engine):
    """
    Scenario 7: CONTRACT COMPLIANCE FOR GEOFENCING AND RESPONSE ASSIGNMENT AGENTS
    Requirement 12: Keep the API ready to integrate with Geofencing Agent and Response Assignment Agent.
    """
    incident = IncidentInput(
        incident_id="SCENARIO-CONTRACT-01",
        incident_type="AGG ASSAULT",
        immediate_danger=True,
        serious_injury=False,
        weapon_reported=True,
        victim_count=1,
        neighborhood="MIDTOWN",
        latitude=33.7834,
        longitude=-84.3831,
    )
    result = engine.prioritize(incident)

    # Validate Geofencing contract
    geo = result.geofencing_integration
    assert geo.ready_for_geofencing is True
    assert geo.latitude == 33.7834
    assert geo.longitude == -84.3831
    assert geo.neighborhood == "MIDTOWN"
    assert geo.location_context_band is not None
    assert isinstance(geo.geofence_priority_weight, float)
    assert geo.suggested_geofence_radius_meters > 0

    # Validate Response Assignment contract
    assignment = result.response_assignment_integration
    assert assignment.ready_for_assignment is True
    assert assignment.priority_tier in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]
    assert len(assignment.suggested_unit_types) > 0
    assert assignment.minimum_personnel >= 1
    assert len(assignment.staging_instructions) > 0
    assert assignment.supervisor_review_required is True
    assert assignment.auto_dispatch_authorized is False

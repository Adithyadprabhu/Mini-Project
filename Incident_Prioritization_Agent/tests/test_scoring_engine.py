"""
Tests for Priority Scoring Engine.
Verifies scoring logic, priority tiers (CRITICAL, HIGH, MEDIUM, LOW),
emergency modifiers, missing data handling, and auto-dispatch constraint.
"""

import pytest
from agent.config import (
    AUTO_DISPATCH_ENABLED,
    EmergencyFieldState,
    LocationContextBand,
    PriorityLevel,
)
from agent.schemas import IncidentInput
from agent.scoring_engine import PriorityScoringEngine


@pytest.fixture
def engine():
    return PriorityScoringEngine()


def test_missing_emergency_fields_treated_as_missing_not_false(engine):
    """
    Requirement 4: Treat unknown historical/intake emergency fields as missing, not false.
    Verify that when immediate_danger, serious_injury, and weapon_reported are None,
    they are identified as MISSING_UNKNOWN, not VERIFIED_FALSE.
    """
    incident = IncidentInput(
        incident_id="TEST-MISSING-01",
        incident_type="BURGLARY-RESIDENCE",
        immediate_danger=None,
        serious_injury=None,
        weapon_reported=None,
    )
    result = engine.prioritize(incident)

    status = result.field_status
    assert status.immediate_danger_status == EmergencyFieldState.MISSING_UNKNOWN
    assert status.serious_injury_status == EmergencyFieldState.MISSING_UNKNOWN
    assert status.weapon_reported_status == EmergencyFieldState.MISSING_UNKNOWN
    assert status.missing_fields_count == 3
    assert set(status.missing_fields) == {"immediate_danger", "serious_injury", "weapon_reported"}
    # Uncertainty buffer is added rather than penalizing/treating as false
    assert result.scoring_breakdown.uncertainty_buffer > 0


def test_verified_false_emergency_fields_differ_from_missing(engine):
    """
    Verify that explicit False behaves differently from None (missing).
    When verified False, uncertainty buffer is 0.
    """
    incident_false = IncidentInput(
        incident_id="TEST-FALSE-01",
        incident_type="BURGLARY-RESIDENCE",
        immediate_danger=False,
        serious_injury=False,
        weapon_reported=False,
    )
    result_false = engine.prioritize(incident_false)

    assert result_false.field_status.immediate_danger_status == EmergencyFieldState.VERIFIED_FALSE
    assert result_false.field_status.missing_fields_count == 0
    assert result_false.scoring_breakdown.uncertainty_buffer == 0.0

    # Incident with None (missing) should have uncertainty buffer
    incident_missing = IncidentInput(
        incident_id="TEST-MISSING-02",
        incident_type="BURGLARY-RESIDENCE",
        immediate_danger=None,
        serious_injury=None,
        weapon_reported=None,
    )
    result_missing = engine.prioritize(incident_missing)
    assert result_missing.priority_score > result_false.priority_score


def test_critical_override_active_danger_and_weapon(engine):
    """
    Safety override: Active danger + weapon must yield CRITICAL tier.
    """
    incident = IncidentInput(
        incident_id="TEST-CRIT-01",
        incident_type="LARCENY-FROM VEHICLE",  # Low base crime elevated by acute threat
        immediate_danger=True,
        weapon_reported=True,
        serious_injury=False,
    )
    result = engine.prioritize(incident)
    assert result.priority_level == PriorityLevel.CRITICAL
    assert result.priority_score >= 80.0
    assert result.scoring_breakdown.critical_override_triggered is True


def test_mass_casualty_victim_scaling(engine):
    """
    Mass casualty scaling: Multiple victims and serious injury elevate priority.
    """
    incident = IncidentInput(
        incident_id="TEST-MASS-01",
        incident_type="AGG ASSAULT",
        immediate_danger=True,
        serious_injury=True,
        victim_count=5,
    )
    result = engine.prioritize(incident)
    assert result.priority_level == PriorityLevel.CRITICAL
    assert result.priority_score >= 90.0
    assert result.scoring_breakdown.victim_count_modifier >= 15.0


def test_neighborhood_context_influences_score(engine):
    """
    Historical neighborhood context modulates score appropriately.
    """
    # High risk neighborhood (e.g. DOWNTOWN - Q4)
    inc_q4 = IncidentInput(
        incident_id="TEST-Q4",
        incident_type="AUTO THEFT",
        neighborhood="DOWNTOWN",
        immediate_danger=False,
        serious_injury=False,
        weapon_reported=False,
    )
    res_q4 = engine.prioritize(inc_q4)

    # Low risk neighborhood (e.g. Q1 neighborhood)
    inc_q1 = IncidentInput(
        incident_id="TEST-Q1",
        incident_type="AUTO THEFT",
        neighborhood="ARDEN/HABERSHAM",
        immediate_danger=False,
        serious_injury=False,
        weapon_reported=False,
    )
    res_q1 = engine.prioritize(inc_q1)

    assert res_q4.scoring_breakdown.neighborhood_modifier > res_q1.scoring_breakdown.neighborhood_modifier


def test_auto_dispatch_strictly_disabled(engine):
    """
    Requirement 13: Do not automatically dispatch emergency services.
    Every single prioritization output must explicitly enforce auto_dispatch_authorized = False.
    """
    incident = IncidentInput(
        incident_id="TEST-DISPATCH-CHECK",
        incident_type="HOMICIDE",
        immediate_danger=True,
        serious_injury=True,
        weapon_reported=True,
        victim_count=3,
    )
    result = engine.prioritize(incident)
    assert result.auto_dispatch_authorized is False
    assert result.response_assignment_integration.auto_dispatch_authorized is False
    assert result.response_assignment_integration.supervisor_review_required is True
    assert "human" in result.recommended_action.lower()

"""
Pydantic Schemas for Incident Prioritization Agent.
Provides input validation, output models, and integration ready interfaces.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from agent.config import (
    AUTO_DISPATCH_ENABLED,
    DISPATCH_DISCLAIMER,
    EmergencyFieldState,
    LocationContextBand,
    PriorityLevel,
)


class IncidentInput(BaseModel):
    """
    Input schema for an incident to be prioritized.
    Supports incident type, dynamic emergency factors, location and metadata.
    Treats unknown emergency fields as missing (None), NOT as False.
    """
    incident_id: str = Field(
        ...,
        description="Unique identifier for the incident",
        min_length=1,
        examples=["INC-2026-90412"]
    )
    incident_type: str = Field(
        ...,
        description="Type or classification of the incident (e.g., AGG ASSAULT, ROBBERY-PEDESTRIAN, AUTO THEFT)",
        min_length=1,
        examples=["AGG ASSAULT"]
    )
    immediate_danger: Optional[bool] = Field(
        default=None,
        description="Whether there is active immediate threat to life. None/null indicates unknown/missing (not false)."
    )
    serious_injury: Optional[bool] = Field(
        default=None,
        description="Whether serious or life-threatening bodily injury is reported. None/null indicates unknown/missing."
    )
    weapon_reported: Optional[bool] = Field(
        default=None,
        description="Whether a firearm, bladed weapon, or dangerous instrument is reported. None/null indicates unknown/missing."
    )
    victim_count: Optional[int] = Field(
        default=1,
        ge=0,
        le=500,
        description="Reported number of victims involved in the incident"
    )
    neighborhood: Optional[str] = Field(
        default=None,
        description="Atlanta neighborhood name (e.g., DOWNTOWN, MIDTOWN, OLD FOURTH WARD)",
        examples=["DOWNTOWN"]
    )
    address: Optional[str] = Field(
        default=None,
        description="Reported street address or intersection",
        examples=["100 PEACHTREE ST NW"]
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees",
        examples=[33.7537]
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees",
        examples=[-84.3863]
    )
    beat: Optional[str] = Field(
        default=None,
        description="Police beat number or code",
        examples=["501"]
    )
    incident_time: Optional[str] = Field(
        default=None,
        description="Reported timestamp or time string",
        examples=["14:30:00"]
    )
    cad_source_id: Optional[str] = Field(
        default=None,
        description="External CAD/911 system record ID"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Caller narrative or supplementary notes"
    )

    @field_validator("incident_id")
    @classmethod
    def validate_incident_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("incident_id cannot be empty or blank")
        return clean

    @field_validator("incident_type")
    @classmethod
    def validate_incident_type(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("incident_type cannot be empty or blank")
        return clean

    @field_validator("neighborhood")
    @classmethod
    def clean_neighborhood(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        clean = v.strip().upper()
        return clean if clean else None


class ScoringBreakdown(BaseModel):
    """Detailed score decomposition for transparent explainability."""
    base_offense_score: float
    matched_offense_type: str
    emergency_modifier: float
    victim_count_modifier: float
    neighborhood_modifier: float
    uncertainty_buffer: float
    raw_computed_score: float
    final_score: float
    critical_override_triggered: bool = False
    override_reason: Optional[str] = None


class FieldMissingStatus(BaseModel):
    """
    Explicit status of emergency fields to satisfy Requirement 4:
    Treat unknown historical/intake emergency fields as missing, not false.
    """
    immediate_danger_status: EmergencyFieldState
    serious_injury_status: EmergencyFieldState
    weapon_reported_status: EmergencyFieldState
    missing_fields: List[str]
    missing_fields_count: int
    data_completeness_level: str  # HIGH, MEDIUM, LOW
    confidence_assessment: str


class GeofencingIntegration(BaseModel):
    """
    Geofencing Agent integration contract.
    Ready for coordinate mapping, zone checks, and proximity geofence alerts.
    """
    ready_for_geofencing: bool
    latitude: Optional[float]
    longitude: Optional[float]
    neighborhood: Optional[str]
    location_context_band: LocationContextBand
    historical_count_percentile: Optional[float]
    perimeter_alert_recommended: bool
    suggested_geofence_radius_meters: int
    geofence_priority_weight: float


class ResponseAssignmentIntegration(BaseModel):
    """
    Response Assignment Agent integration contract.
    Provides unit capabilities, staging requirements, and supervisor protocols.
    Strictly forbids automatic dispatch.
    """
    ready_for_assignment: bool
    priority_tier: PriorityLevel
    dispatch_queue: str
    suggested_unit_types: List[str]
    minimum_responders: int = 1
    minimum_personnel: Optional[int] = None
    staging_instructions: str
    supervisor_review_required: bool = True
    auto_dispatch_authorized: bool = False

    def model_post_init(self, __context: Any) -> None:
        if self.minimum_personnel is None:
            self.minimum_personnel = self.minimum_responders


class PrioritizationResponse(BaseModel):
    """
    Primary API response for POST /prioritize.
    Satisfies Requirements 8, 9, 10, 12, 13.
    """
    incident_id: str
    priority_score: float = Field(
        ...,
        description="Overall priority score from 0.0 to 100.0",
        ge=0.0,
        le=100.0
    )
    priority_level: PriorityLevel = Field(
        ...,
        description="Triage level: CRITICAL, HIGH, MEDIUM, or LOW"
    )
    recommended_action: str = Field(
        ...,
        description="Actionable triage recommendation for 911 dispatch personnel"
    )
    auto_dispatch_authorized: bool = Field(
        default=AUTO_DISPATCH_ENABLED,
        description="Strictly False: Automated dispatch is disabled"
    )
    disclaimer: str = Field(
        default=DISPATCH_DISCLAIMER,
        description="Legal and operational disclaimer"
    )
    scoring_breakdown: ScoringBreakdown
    field_status: FieldMissingStatus
    geofencing_integration: GeofencingIntegration
    response_assignment_integration: ResponseAssignmentIntegration
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatchPrioritizationRequest(BaseModel):
    """Batch input schema."""
    incidents: List[IncidentInput] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="List of incidents to prioritize"
    )


class BatchPrioritizationResponse(BaseModel):
    """Batch output schema."""
    total_processed: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    results: List[PrioritizationResponse]


class NeighborhoodProfileResponse(BaseModel):
    """Neighborhood risk context response."""
    neighborhood: str
    historical_incident_count: int
    critical_offense_count: int
    high_offense_count: int
    medium_offense_count: int
    low_offense_count: int
    historical_count_percentile: float
    location_context_band: LocationContextBand
    interpretation_warning: str


class EvaluationSummaryResponse(BaseModel):
    """Evaluation summary against historical proxy labels."""
    prototype_warning: str
    evaluated_sample_size: int
    overall_proxy_concordance: float
    per_class_metrics: Dict[str, Any]
    missing_emergency_fields_handled: Dict[str, Any]

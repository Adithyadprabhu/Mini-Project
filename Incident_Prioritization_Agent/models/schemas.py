"""
Shared Pydantic Schemas for Multi-Agent Tourist Safety Alert System.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from models.enums import (
    AssignmentStatus,
    EmergencyFieldState,
    LocationContextBand,
    PriorityLevel,
    ResponseCategory,
    RiskLevel,
    WeatherCompatibility,
    ZoneType,
)

AUTO_DISPATCH_ENABLED = False
DISPATCH_DISCLAIMER = (
    "AUTOMATED DISPATCH DISABLED: Triage recommendation only. "
    "Dispatch authorization requires human 911 dispatcher or supervisor review and approval."
)


# ---------------- INCIDENT SCHEMAS ----------------

class IncidentInput(BaseModel):
    """
    Standardized Incident Input for Incident Prioritization Agent.
    Treats unknown emergency fields as missing (None), NOT as False.
    """
    incident_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the incident",
        examples=["INC-2026-90412"]
    )
    incident_type: str = Field(
        ...,
        min_length=1,
        description="Type or classification of the incident (e.g. AGG ASSAULT, ROBBERY, BURGLARY, AUTO THEFT)",
        examples=["AGG ASSAULT"]
    )
    immediate_danger: Optional[bool] = Field(
        default=None,
        description="Active immediate threat to life. None/null indicates unknown/missing (not false)."
    )
    serious_injury: Optional[bool] = Field(
        default=None,
        description="Serious or life-threatening bodily injury. None/null indicates unknown/missing."
    )
    weapon_reported: Optional[bool] = Field(
        default=None,
        description="Firearm, knife, or dangerous weapon reported. None/null indicates unknown/missing."
    )
    victim_count: Optional[int] = Field(
        default=1,
        ge=0,
        le=500,
        description="Reported number of victims"
    )
    neighborhood: Optional[str] = Field(
        default=None,
        description="Atlanta neighborhood name (e.g. DOWNTOWN, MIDTOWN, OLD FOURTH WARD)",
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
    beat: Optional[str] = Field(default=None, description="Police beat number or code")
    incident_time: Optional[str] = Field(default=None, description="Reported timestamp or time string")
    cad_source_id: Optional[str] = Field(default=None, description="External CAD/911 system record ID")
    notes: Optional[str] = Field(default=None, description="Caller narrative or supplementary notes")

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
    """Detailed score decomposition for explainable triage."""
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
    """Status of dynamic emergency fields (Requirement 4)."""
    immediate_danger_status: EmergencyFieldState
    serious_injury_status: EmergencyFieldState
    weapon_reported_status: EmergencyFieldState
    missing_fields: List[str]
    missing_fields_count: int
    data_completeness_level: str
    confidence_assessment: str


class WeatherContext(BaseModel):
    """Contextual weather details when incident timestamp is compatible."""
    weather_compatibility: WeatherCompatibility
    matched_datetime: Optional[str] = None
    temperature_f: Optional[float] = None
    precipitation_in: Optional[float] = None
    apparent_temp_f: Optional[float] = None
    weather_condition: Optional[str] = None
    is_daylight: Optional[bool] = None
    weather_note: str


class GeofencingIntegration(BaseModel):
    """Contract for Geofencing Agent."""
    ready_for_geofencing: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    neighborhood: Optional[str] = None
    location_context_band: LocationContextBand = LocationContextBand.UNKNOWN
    historical_count_percentile: Optional[float] = None
    perimeter_alert_recommended: bool = False
    suggested_geofence_radius_meters: int = 250
    geofence_priority_weight: float = 0.5


class ResponseAssignmentIntegration(BaseModel):
    """Contract for Response Assignment Agent."""
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
    """Full triage response for prioritized incidents."""
    incident_id: str
    priority_score: float = Field(..., ge=0.0, le=100.0)
    priority_level: PriorityLevel
    recommended_action: str
    auto_dispatch_authorized: bool = Field(default=AUTO_DISPATCH_ENABLED)
    disclaimer: str = Field(default=DISPATCH_DISCLAIMER)
    scoring_breakdown: ScoringBreakdown
    field_status: FieldMissingStatus
    weather_context: Optional[WeatherContext] = None
    geofencing_integration: GeofencingIntegration
    response_assignment_integration: ResponseAssignmentIntegration
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------- GEOFENCING SCHEMAS ----------------

class GeofenceZone(BaseModel):
    """Geofencing Zone definition with GeoJSON Polygon/MultiPolygon geometry."""
    id: str
    name: str
    risk_level: RiskLevel
    zone_type: ZoneType
    geometry: Dict[str, Any]
    description: Optional[str] = None


class TouristLocationCheck(BaseModel):
    """Tourist coordinate check."""
    tourist_id: Optional[str] = Field(default="TOURIST-001", description="Identifier for tourist or app user")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GeofenceAlertRequest(BaseModel):
    """
    Geofencing Alert ingestion request.
    Connects Geofencing Agent to Incident Prioritization Agent (Module 2).
    """
    alert_id: Optional[str] = None
    tourist_id: Optional[str] = "TOURIST-001"
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: Optional[str] = None
    alert_type: str = Field(default="ZONE_ENTRY_WARNING", description="ZONE_ENTRY_WARNING, RESTRICTED_AREA_BREACH, or TOURIST_SOS")
    zone_name: Optional[str] = None
    zone_type: Optional[ZoneType] = None
    risk_level: Optional[RiskLevel] = None
    caller_reported_emergency: bool = Field(
        default=False,
        description="Distinguishes standard zone entry warning from an actual reported crime or emergency"
    )
    immediate_danger: Optional[bool] = None
    serious_injury: Optional[bool] = None
    weapon_reported: Optional[bool] = None
    notes: Optional[str] = None


class GeofenceAlertResponse(BaseModel):
    """Response returned after processing a geofence alert."""
    alert_id: str
    tourist_id: Optional[str]
    is_duplicate: bool
    duplicate_message: Optional[str] = None
    inside_zone: bool
    zone_name: Optional[str]
    zone_type: Optional[ZoneType]
    risk_level: Optional[RiskLevel]
    is_actual_emergency: bool
    alert_message: str
    prioritization: Optional[PrioritizationResponse] = None
    timestamp: str


# ---------------- RESPONSE ASSIGNMENT SCHEMAS ----------------

class AuthorizedUnit(BaseModel):
    """Authorized unit definition from unit catalog."""
    unit_id: str
    unit_type: str
    category: ResponseCategory
    capabilities: List[str]
    base_station: str
    status: str = "AVAILABLE"


class ResponseAssignmentRequest(BaseModel):
    """Request to assign or recommend a response unit for an incident."""
    incident_id: str
    priority_level: PriorityLevel
    incident_type: str
    response_category: Optional[ResponseCategory] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    neighborhood: Optional[str] = None
    notes: Optional[str] = None


class ResponseAssignmentResponse(BaseModel):
    """Response Assignment Agent output (Module 3)."""
    assignment_id: str
    incident_id: str
    priority_tier: PriorityLevel
    response_category: ResponseCategory
    recommended_unit_types: List[str]
    assigned_unit_id: Optional[str] = None
    assigned_unit_name: Optional[str] = None
    minimum_personnel: int
    staging_instructions: str
    assignment_status: AssignmentStatus
    human_supervisor_approval_required: bool = True
    auto_dispatch_authorized: bool = False
    disclaimer: str = DISPATCH_DISCLAIMER
    timestamp: str


# ---------------- BATCH & AUXILIARY SCHEMAS ----------------

class BatchPrioritizationRequest(BaseModel):
    incidents: List[IncidentInput] = Field(..., min_length=1, max_length=500)


class BatchPrioritizationResponse(BaseModel):
    total_processed: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    results: List[PrioritizationResponse]


class NeighborhoodProfileResponse(BaseModel):
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
    prototype_warning: str
    evaluated_sample_size: int
    overall_proxy_concordance: float
    per_class_metrics: Dict[str, Any]
    confusion_matrix: Dict[str, Dict[str, int]]
    missing_emergency_fields_handled: Dict[str, Any]
    concordance_explanation: str

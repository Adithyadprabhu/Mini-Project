"""
FastAPI Application for Incident Prioritization Agent.

Endpoints:
- POST /prioritize: Prioritize single incident with validation and scoring
- POST /prioritize/batch: Prioritize batch of incidents
- GET /neighborhoods: List all 242 Atlanta neighborhood risk profiles
- GET /neighborhoods/{name}: Retrieve specific neighborhood risk context
- GET /evaluation: Baseline prototyping evaluation against historical proxy labels
- GET /health: Service health and dataset loading readiness
"""

from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Path, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.config import AUTO_DISPATCH_ENABLED, DISPATCH_DISCLAIMER
from agent.data_loader import DataLoader, get_data_loader
from agent.evaluator import PrototypeEvaluator
from agent.schemas import (
    BatchPrioritizationRequest,
    BatchPrioritizationResponse,
    EvaluationSummaryResponse,
    IncidentInput,
    NeighborhoodProfileResponse,
    PrioritizationResponse,
)
from agent.scoring_engine import PriorityScoringEngine


# Eagerly initialize core singletons for fast and reliable startup
_default_loader = get_data_loader()
_default_engine = PriorityScoringEngine(data_loader=_default_loader)
_default_evaluator = PrototypeEvaluator(engine=_default_engine, data_loader=_default_loader)

app = FastAPI(
    title="Atlanta Incident Prioritization Agent API",
    description=(
        "Public Safety Incident Prioritization Agent leveraging historical Atlanta crime "
        "and neighborhood risk profiles. Integrates with Geofencing and Response Assignment Agents. "
        f"\n\n**CRITICAL NOTICE:** {DISPATCH_DISCLAIMER}"
    ),
    version="1.0.0",
)

# Attach singletons to app state
app.state.data_loader = _default_loader
app.state.scoring_engine = _default_engine
app.state.evaluator = _default_evaluator

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_engine() -> PriorityScoringEngine:
    return getattr(app.state, "scoring_engine", _default_engine)


def get_loader() -> DataLoader:
    return getattr(app.state, "data_loader", _default_loader)


def get_evaluator() -> PrototypeEvaluator:
    return getattr(app.state, "evaluator", _default_evaluator)


# Custom Validation Error Handler (Requirement 10)
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append({
            "field": field_path,
            "message": err.get("msg", "Validation error"),
            "type": err.get("type", "value_error"),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Input Validation Error",
            "detail": errors,
            "auto_dispatch_authorized": False,
        },
    )


@app.get("/health", tags=["System"])
def health_check():
    """Returns service health, data loading status, and safety constraints."""
    loader = get_loader()
    return {
        "status": "healthy",
        "service": "Incident Prioritization Agent",
        "version": "1.0.0",
        "auto_dispatch_authorized": AUTO_DISPATCH_ENABLED,
        "neighborhoods_loaded": len(loader.list_neighborhoods()),
        "disclaimer": DISPATCH_DISCLAIMER,
    }


@app.post(
    "/prioritize",
    response_model=PrioritizationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Prioritization"],
    summary="Prioritize an incoming incident",
    description=(
        "Scores and classifies an incident into CRITICAL, HIGH, MEDIUM, or LOW priority. "
        "Considers incident type, dynamic emergency factors (immediate danger, serious injury, weapon), "
        "victim count, and neighborhood risk profile. Missing emergency fields are treated as unknown, not false. "
        "Generates Geofencing and Response Assignment integration payloads. Does NOT dispatch units."
    ),
)
def prioritize_incident(incident: IncidentInput) -> PrioritizationResponse:
    """
    Primary endpoint fulfilling Requirements 8, 9, 10, 12, 13.
    """
    try:
        engine = get_engine()
        result = engine.prioritize(incident)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prioritization scoring failed: {str(e)}",
        )


@app.post(
    "/prioritize/batch",
    response_model=BatchPrioritizationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Prioritization"],
    summary="Batch prioritize multiple incidents",
)
def prioritize_batch(batch: BatchPrioritizationRequest) -> BatchPrioritizationResponse:
    """Processes a batch of incidents and returns aggregate triage counts and results."""
    engine = get_engine()
    results = []
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for incident in batch.incidents:
        res = engine.prioritize(incident)
        counts[res.priority_level.value] += 1
        results.append(res)

    return BatchPrioritizationResponse(
        total_processed=len(results),
        critical_count=counts["CRITICAL"],
        high_count=counts["HIGH"],
        medium_count=counts["MEDIUM"],
        low_count=counts["LOW"],
        results=results,
    )


@app.get(
    "/neighborhoods",
    response_model=List[NeighborhoodProfileResponse],
    tags=["Context"],
    summary="List all historical neighborhood risk profiles",
)
def list_neighborhoods() -> List[NeighborhoodProfileResponse]:
    """Retrieves all 242 neighborhood risk profiles loaded from neighborhood_risk_profile.csv."""
    loader = get_loader()
    profiles = loader.list_neighborhoods()
    return [
        NeighborhoodProfileResponse(
            neighborhood=p["neighborhood"],
            historical_incident_count=p["historical_incident_count"],
            critical_offense_count=p["critical_offense_count"],
            high_offense_count=p["high_offense_count"],
            medium_offense_count=p["medium_offense_count"],
            low_offense_count=p["low_offense_count"],
            historical_count_percentile=p["historical_count_percentile"],
            location_context_band=p["location_context_band"],
            interpretation_warning=p["interpretation_warning"],
        )
        for p in profiles
    ]


@app.get(
    "/neighborhoods/{name}",
    response_model=NeighborhoodProfileResponse,
    tags=["Context"],
    summary="Get single neighborhood risk profile",
)
def get_neighborhood(name: str = Path(..., min_length=1)) -> NeighborhoodProfileResponse:
    """Fetches risk profile for a specific neighborhood, or neutral fallback if not found."""
    loader = get_loader()
    p = loader.get_neighborhood_profile(name)
    return NeighborhoodProfileResponse(
        neighborhood=p["neighborhood"],
        historical_incident_count=p["historical_incident_count"],
        critical_offense_count=p["critical_offense_count"],
        high_offense_count=p["high_offense_count"],
        medium_offense_count=p["medium_offense_count"],
        low_offense_count=p["low_offense_count"],
        historical_count_percentile=p["historical_count_percentile"],
        location_context_band=p["location_context_band"],
        interpretation_warning=p["interpretation_warning"],
    )


@app.get(
    "/evaluation",
    response_model=EvaluationSummaryResponse,
    tags=["Prototyping & Evaluation"],
    summary="Run rule-based prototyping evaluation against dataset proxy labels",
    description=(
        "Fulfills Requirement 5: Evaluates the rule-based engine against historical proxy labels. "
        "Highlights that proxy labels are non-verified proxies and emergency fields were missing in history."
    ),
)
def evaluate_prototype(sample_size: int = 1000) -> EvaluationSummaryResponse:
    """Runs prototyping evaluation on a sample of historical incidents."""
    evaluator = get_evaluator()
    safe_size = max(100, min(sample_size, 10000))
    return evaluator.evaluate_sample(sample_size=safe_size)

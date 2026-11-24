"""
Configuration settings for the Incident Prioritization Agent.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EmergencyFieldState(str, Enum):
    VERIFIED_TRUE = "VERIFIED_TRUE"
    VERIFIED_FALSE = "VERIFIED_FALSE"
    MISSING_UNKNOWN = "MISSING_UNKNOWN"


class LocationContextBand(str, Enum):
    Q4_HIGHEST = "Q4_HIGHEST"
    Q3 = "Q3"
    Q2 = "Q2"
    Q1_LOWEST = "Q1_LOWEST"
    UNKNOWN = "UNKNOWN"


# File paths resolution - supports both 'datasets' and 'dataset' directories
BASE_DIR = Path(__file__).resolve().parent.parent

def resolve_dataset_path(filename: str) -> Path:
    candidates = [
        BASE_DIR / "datasets" / filename,
        BASE_DIR / "dataset" / filename,
        Path("datasets") / filename,
        Path("dataset") / filename,
    ]
    for p in candidates:
        if p.is_file():
            return p
    # Default to first candidate
    return candidates[0]

INCIDENT_DATASET_PATH = resolve_dataset_path("incident_prioritization_dataset.csv")
NEIGHBORHOOD_RISK_PATH = resolve_dataset_path("neighborhood_risk_profile.csv")

# Critical constraint: Emergency services must NOT be automatically dispatched
AUTO_DISPATCH_ENABLED = False
DISPATCH_DISCLAIMER = (
    "AUTOMATED DISPATCH DISABLED: This agent performs triage recommendation only. "
    "Dispatch authorization requires review and confirmation by a human 911 dispatcher or supervisor."
)

# Priority score classification thresholds (0 - 100 scale)
SCORE_THRESHOLDS = {
    PriorityLevel.CRITICAL: 80.0,
    PriorityLevel.HIGH: 60.0,
    PriorityLevel.MEDIUM: 40.0,
    PriorityLevel.LOW: 0.0,
}

# Base offense proxy scores calibrated from Atlanta Historical Incident Dataset
BASE_OFFENSE_SCORES: Dict[str, float] = {
    # Critical Offenses
    "HOMICIDE": 95.0,
    "RAPE": 90.0,
    "AGG ASSAULT": 85.0,
    "AGGRAVATED ASSAULT": 85.0,
    "ACTIVE SHOOTER": 100.0,
    "SHOTS FIRED": 85.0,
    "KIDNAPPING": 90.0,
    
    # High Priority Offenses
    "ROBBERY-PEDESTRIAN": 70.0,
    "ROBBERY-COMMERCIAL": 70.0,
    "ROBBERY-RESIDENCE": 72.0,
    "ARMED ROBBERY": 78.0,
    "CARJACKING": 75.0,
    
    # Medium Priority Offenses
    "BURGLARY-RESIDENCE": 48.0,
    "BURGLARY-NONRES": 44.0,
    "BURGLARY": 46.0,
    "STOLEN VEHICLE": 34.0,
    "AUTO THEFT": 34.0,
    
    # Low Priority Offenses
    "LARCENY-FROM VEHICLE": 24.0,
    "LARCENY-NON VEHICLE": 20.0,
    "THEFT": 22.0,
    "VANDALISM": 18.0,
    "PROPERTY DAMAGE": 18.0,
    "SUSPICIOUS ACTIVITY": 28.0,
}

DEFAULT_OFFENSE_SCORE = 28.0

# Dynamic Emergency Weights (when present)
WEIGHTS = {
    # Emergency modifiers
    "immediate_danger_true": 25.0,
    "immediate_danger_missing_buffer": 5.0,  # Uncertainty buffer, not false
    "serious_injury_true": 25.0,
    "serious_injury_missing_buffer": 5.0,    # Uncertainty buffer, not false
    "weapon_reported_true": 20.0,
    "weapon_reported_missing_buffer": 3.0,   # Uncertainty buffer, not false
    
    # Victim count scaling
    "victim_single": 0.0,
    "victim_two": 6.0,
    "victim_three_to_four": 12.0,
    "victim_mass_casualty": 20.0,  # 5 or more victims
    
    # Neighborhood risk context
    "neighborhood_q4": 5.0,
    "neighborhood_q3": 3.5,
    "neighborhood_q2": 2.0,
    "neighborhood_q1": 0.0,
    "neighborhood_unknown": 2.0,
    "neighborhood_percentile_weight": 2.5,  # Max additional points based on percentile
}

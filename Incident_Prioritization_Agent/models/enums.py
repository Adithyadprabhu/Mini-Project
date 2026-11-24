"""
Shared Enums for Atlanta Tourist Safety Alert Multi-Agent System.
"""

from enum import Enum


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


class ZoneType(str, Enum):
    SAFE = "SAFE"
    HIGH_RISK = "HIGH_RISK"
    RESTRICTED = "RESTRICTED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ResponseCategory(str, Enum):
    POLICE = "POLICE"
    AMBULANCE = "AMBULANCE"
    FIRE = "FIRE"
    MULTI_AGENCY = "MULTI_AGENCY"


class AssignmentStatus(str, Enum):
    RECOMMENDED_PENDING_APPROVAL = "RECOMMENDED_PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    STAGED = "STAGED"


class WeatherCompatibility(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    MISSING_DATA = "MISSING_DATA"

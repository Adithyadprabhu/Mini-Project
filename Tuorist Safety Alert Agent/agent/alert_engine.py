"""
Module 4: Tourist Safety Alert Engine
Generates prioritized, contextual safety alerts based on assessed risk levels:
  - Low Risk: Safe status / No warning
  - Medium Risk: Caution notification
  - High Risk: Safety warning
  - Very High Risk: Urgent safety warning
  - Restricted Zone: Restricted-area notification

Includes tourist coordinates, zone name, risk level, formatted message,
timestamp, actionable safety guidance, and emergency response eligibility.
"""

import uuid
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, Tuple


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    RESTRICTED = "RESTRICTED"


class AlertType(str, Enum):
    NO_WARNING = "NO_WARNING"
    CAUTION = "CAUTION"
    SAFETY_WARNING = "SAFETY_WARNING"
    URGENT_SAFETY_WARNING = "URGENT_SAFETY_WARNING"
    RESTRICTED_ACCESS = "RESTRICTED_ACCESS"


class TouristAlert:
    """Represents a structured tourist safety alert."""

    def __init__(
        self,
        tourist_id: str,
        coordinates: Tuple[float, float],
        zone_name: Optional[str],
        risk_level: str,
        zone_type: str,
        alert_type: AlertType,
        message: str,
        recommended_action: str,
        event_type: str,
        emergency_dispatch_eligible: bool = False,
        timestamp: Optional[datetime] = None,
    ):
        self.alert_id = str(uuid.uuid4())
        self.tourist_id = tourist_id
        self.coordinates = coordinates
        self.zone_name = zone_name or "General Atlanta Perimeter"
        self.risk_level = risk_level.upper()
        self.zone_type = zone_type.upper()
        self.alert_type = alert_type
        self.message = message
        self.recommended_action = recommended_action
        self.event_type = event_type
        self.emergency_dispatch_eligible = emergency_dispatch_eligible
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "tourist_id": self.tourist_id,
            "tourist_coordinates": {
                "latitude": round(self.coordinates[0], 6),
                "longitude": round(self.coordinates[1], 6),
            },
            "zone_name": self.zone_name,
            "risk_level": self.risk_level,
            "zone_type": self.zone_type,
            "alert_type": self.alert_type.value,
            "message": self.message,
            "recommended_action": self.recommended_action,
            "event_type": self.event_type,
            "emergency_dispatch_eligible": self.emergency_dispatch_eligible,
            "timestamp": self.timestamp.isoformat(),
        }


class AlertEngine:
    """
    Evaluates tracking transitions and risk scores to synthesize tailored alerts.
    """

    def generate_alert(
        self,
        tourist_id: str,
        coordinates: Tuple[float, float],
        risk_level: str,
        zone_name: Optional[str] = None,
        zone_type: str = "SAFE",
        event_type: str = "ENTRY",
        custom_message: Optional[str] = None,
    ) -> TouristAlert:
        """
        Creates a structured TouristAlert corresponding to the input risk level and zone type.
        """
        norm_risk = str(risk_level).upper().replace(" ", "_")
        norm_zone_type = str(zone_type).upper().replace(" ", "_")

        # 1. RESTRICTED ZONE
        if norm_zone_type == "RESTRICTED" or norm_risk == "RESTRICTED":
            return TouristAlert(
                tourist_id=tourist_id,
                coordinates=coordinates,
                zone_name=zone_name or "Restricted Sector",
                risk_level="RESTRICTED",
                zone_type="RESTRICTED",
                alert_type=AlertType.RESTRICTED_ACCESS,
                message=custom_message or (
                    f"⛔ RESTRICTED AREA ALERT: You have approached or entered '{zone_name or 'a restricted facility'}'. "
                    "Public access is strictly forbidden by municipal and federal regulations."
                ),
                recommended_action=(
                    "Halt immediately and retrace your steps to public pedestrian roads. "
                    "Do not climb fences or cross railway/utility barriers."
                ),
                event_type=event_type,
                emergency_dispatch_eligible=True,
            )

        # 2. VERY HIGH RISK
        elif norm_risk in ["VERY_HIGH", "VERY_HIGH_RISK"]:
            return TouristAlert(
                tourist_id=tourist_id,
                coordinates=coordinates,
                zone_name=zone_name or "High Crime Hotspot",
                risk_level="VERY_HIGH",
                zone_type=norm_zone_type,
                alert_type=AlertType.URGENT_SAFETY_WARNING,
                message=custom_message or (
                    f"🚨 URGENT SAFETY WARNING: You entered a Very High Crime Risk area ('{zone_name or 'Critical Hotspot'}'). "
                    "Historical records show elevated violent and robbery incidents in this sector."
                ),
                recommended_action=(
                    "Leave this area promptly. Follow the recommended safe route toward Centennial Olympic Park or a lit safe corridor. "
                    "Keep valuables concealed, avoid solitary paths, and trigger the Emergency SOS if feeling threatened."
                ),
                event_type=event_type,
                emergency_dispatch_eligible=True,
            )

        # 3. HIGH RISK
        elif norm_risk in ["HIGH", "HIGH_RISK"]:
            return TouristAlert(
                tourist_id=tourist_id,
                coordinates=coordinates,
                zone_name=zone_name or "Elevated Risk Sector",
                risk_level="HIGH",
                zone_type=norm_zone_type,
                alert_type=AlertType.SAFETY_WARNING,
                message=custom_message or (
                    f"⚠️ SAFETY WARNING: You are entering '{zone_name or 'a monitored elevated-risk sector'}'. "
                    "The local crime frequency is above average (frequent vehicle larceny and thefts)."
                ),
                recommended_action=(
                    "Maintain continuous situational awareness. Stick to busy, well-lit main avenues (e.g. Peachtree St). "
                    "Do not leave bags unattended and avoid walking alone after dark."
                ),
                event_type=event_type,
                emergency_dispatch_eligible=False,
            )

        # 4. MEDIUM RISK
        elif norm_risk in ["MEDIUM", "MEDIUM_RISK"]:
            return TouristAlert(
                tourist_id=tourist_id,
                coordinates=coordinates,
                zone_name=zone_name or "Moderate Activity Zone",
                risk_level="MEDIUM",
                zone_type=norm_zone_type,
                alert_type=AlertType.CAUTION,
                message=custom_message or (
                    f"ℹ️ CAUTION NOTIFICATION: '{zone_name or 'This area'}' has moderate crime activity reported. "
                    "Standard urban precautions are advised."
                ),
                recommended_action=(
                    "Keep mobile phones and personal items secure. Enjoy your visit while remaining observant of your surroundings."
                ),
                event_type=event_type,
                emergency_dispatch_eligible=False,
            )

        # 5. LOW RISK / SAFE
        else:
            return TouristAlert(
                tourist_id=tourist_id,
                coordinates=coordinates,
                zone_name=zone_name or "Designated Safe Zone",
                risk_level="LOW",
                zone_type="SAFE",
                alert_type=AlertType.NO_WARNING,
                message=custom_message or (
                    f"✅ SAFE ZONE: You are in '{zone_name or 'a verified low-risk tourist sector'}'. "
                    "Monitored pedestrian corridors and active security patrols are present."
                ),
                recommended_action=(
                    "Safe to explore. Standard travel precautions apply."
                ),
                event_type=event_type,
                emergency_dispatch_eligible=False,
            )


if __name__ == "__main__":
    engine = AlertEngine()
    coords = (33.7530, -84.3880)

    # Test all severity levels
    for r in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH", "RESTRICTED"]:
        alert = engine.generate_alert("T-01", coords, risk_level=r, zone_name=f"Test {r} Zone")
        d = alert.to_dict()
        print(f"\n[{d['alert_type']}] Risk: {d['risk_level']}")
        print(f"Message: {d['message']}")
        print(f"Action: {d['recommended_action']}")

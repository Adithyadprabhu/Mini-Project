"""
Master Orchestrator Agent: TouristSafetyAgent
Coordinates crime data processing, machine learning risk inference, geofence monitoring,
alert generation, evasive safe route recommendation, and emergency response dispatch.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

try:
    from .crime_data_processor import CrimeDataProcessor
    from .crime_risk_predictor import CrimeRiskPredictor
    from .geofence_integration import GeofenceManager, TouristLocationTracker
    from .alert_engine import AlertEngine, TouristAlert, AlertSeverity
    from .safe_route import SafeRouteEngine
    from .emergency_integration import EmergencyResponseDispatcher
except ImportError:
    from crime_data_processor import CrimeDataProcessor
    from crime_risk_predictor import CrimeRiskPredictor
    from geofence_integration import GeofenceManager, TouristLocationTracker
    from alert_engine import AlertEngine, TouristAlert, AlertSeverity
    from safe_route import SafeRouteEngine
    from emergency_integration import EmergencyResponseDispatcher

logger = logging.getLogger(__name__)


class TouristSafetyAgent:
    """
    Unified AI Agent for Atlanta Tourist Safety.
    Integrates geofencing, ML risk prediction, contextual alerts,
    safe navigation, and emergency services dispatch.
    """

    def __init__(
        self,
        zones_file: Optional[str] = None,
        auto_load_model: bool = True,
    ):
        self.processor = CrimeDataProcessor()
        self.risk_predictor = CrimeRiskPredictor()
        
        if auto_load_model:
            loaded = self.risk_predictor.load_model()
            if not loaded:
                logger.info("Pre-trained model not found. Model can be trained using risk_predictor.train_and_evaluate().")

        self.geofence_manager = GeofenceManager(zones_file=zones_file)
        self.tracker = TouristLocationTracker(self.geofence_manager)
        self.alert_engine = AlertEngine()
        self.route_engine = SafeRouteEngine()
        self.emergency_dispatcher = EmergencyResponseDispatcher()

        self.alert_log: List[Dict[str, Any]] = []

    def monitor_tourist(
        self,
        tourist_id: str,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None,
        auto_dispatch_emergency: bool = False,
    ) -> Dict[str, Any]:
        """
        Primary continuous monitoring loop.
        Evaluates tourist GPS coordinates against geofenced polygons,
        predicts ML risk, detects state transitions (ENTRY/EXIT),
        suppresses repeated alerts, recommends safe routes if endangered,
        and optionally alerts emergency services.
        """
        now = timestamp or datetime.now()

        # 1. Geofence evaluation & state transition tracking
        transition = self.tracker.update_tourist_location(
            tourist_id=tourist_id,
            latitude=latitude,
            longitude=longitude,
            timestamp=now,
        )

        # 2. Machine learning spatio-temporal risk prediction
        try:
            ml_prediction = self.risk_predictor.predict_risk(
                latitude=latitude,
                longitude=longitude,
                timestamp=now,
            )
        except Exception as e:
            logger.warning(f"ML risk prediction fallback: {e}")
            ml_prediction = {
                "risk_level": "Low Risk",
                "risk_code": 0,
                "confidence": 0.5,
                "probabilities": {"Low Risk": 0.8, "Medium Risk": 0.2, "High Risk": 0.0, "Very High Risk": 0.0},
            }

        # 3. Determine effective risk level
        # If tourist is inside a geofenced area, geofence designation takes priority.
        # Otherwise, ambient ML prediction governs.
        if transition["inside"]:
            effective_risk = transition["risk_level"]
            effective_zone = transition["zone_name"]
            effective_zone_type = transition["zone_type"]
        else:
            effective_risk = ml_prediction["risk_level"].upper().replace(" ", "_")
            effective_zone = f"Atlanta Metro (Grid {ml_prediction.get('grid_id', '')})"
            effective_zone_type = "SAFE" if "LOW" in effective_risk else "HIGH_RISK"

        # 4. Generate alert if required by state transition
        alert_dict = None
        if transition["alert_required"]:
            alert = self.alert_engine.generate_alert(
                tourist_id=tourist_id,
                coordinates=(latitude, longitude),
                risk_level=effective_risk,
                zone_name=effective_zone,
                zone_type=effective_zone_type,
                event_type=transition["event_type"],
            )
            alert_dict = alert.to_dict()
            self.alert_log.append(alert_dict)

        # 5. Safe route recommendation if risk is elevated
        safe_route = None
        needs_safe_route = (
            effective_risk in ["HIGH", "VERY_HIGH", "RESTRICTED", "HIGH_RISK", "VERY_HIGH_RISK"]
            or effective_zone_type in ["HIGH_RISK", "RESTRICTED"]
        )

        if needs_safe_route:
            safe_route = self.route_engine.plan_safe_route(
                start_lat=latitude,
                start_lon=longitude,
                zones=self.geofence_manager.zones,
            )

        # 6. Emergency dispatch integration
        emergency_dispatch = None
        is_critical = (
            effective_risk in ["VERY_HIGH", "RESTRICTED", "VERY_HIGH_RISK"]
            or effective_zone_type == "RESTRICTED"
        )

        if is_critical and auto_dispatch_emergency:
            emergency_dispatch = self.emergency_dispatcher.dispatch_response(
                tourist_id=tourist_id,
                latitude=latitude,
                longitude=longitude,
                risk_level=effective_risk,
                zone_name=effective_zone,
                incident_type="CRITICAL_SAFETY_THREAT",
            )

        # 7. Query nearby emergency units for situational awareness
        nearby_emergency_units = self.emergency_dispatcher.get_nearby_emergency_units(
            latitude=latitude,
            longitude=longitude,
            max_distance_km=8.0,
        )

        return {
            "tourist_id": tourist_id,
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "timestamp": now.isoformat(),
            "geofence_status": transition,
            "ml_risk_prediction": ml_prediction,
            "effective_risk_level": effective_risk,
            "effective_zone_name": effective_zone,
            "effective_zone_type": effective_zone_type,
            "new_alert_generated": transition["alert_required"],
            "active_alert": alert_dict,
            "safe_route_recommendation": safe_route,
            "emergency_dispatch": emergency_dispatch,
            "nearby_emergency_units": nearby_emergency_units[:3],
        }

    def trigger_sos(self, tourist_id: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """Manual SOS trigger button from the tourist or admin dashboard."""
        logger.warning(f"MANUAL SOS TRIGGERED by Tourist {tourist_id} at ({latitude}, {longitude})!")
        
        # Immediate emergency dispatch
        dispatch = self.emergency_dispatcher.dispatch_response(
            tourist_id=tourist_id,
            latitude=latitude,
            longitude=longitude,
            risk_level="VERY_HIGH",
            zone_name="Tourist SOS Trigger Location",
            incident_type="PANIC_BUTTON_SOS",
        )

        # Immediate urgent alert
        alert = self.alert_engine.generate_alert(
            tourist_id=tourist_id,
            coordinates=(latitude, longitude),
            risk_level="VERY_HIGH",
            zone_name="SOS Incident Location",
            zone_type="HIGH_RISK",
            event_type="SOS_MANUAL_TRIGGER",
            custom_message="🚨 EMERGENCY SOS ACTIVATED: Public safety authorities notified. Nearest unit dispatched.",
        )
        self.alert_log.append(alert.to_dict())

        # Safe route to closest police station or safe haven
        route = self.route_engine.plan_safe_route(
            start_lat=latitude,
            start_lon=longitude,
            zones=self.geofence_manager.zones,
        )

        return {
            "status": "SOS_DISPATCHED",
            "dispatch": dispatch,
            "alert": alert.to_dict(),
            "evasive_route": route,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = TouristSafetyAgent()

    print("--- Simulating Tourist Journey in Atlanta ---")
    # Step 1: Tourist starts in safe area (Centennial Olympic Park: 33.7600, -84.3930)
    print("\n1. Tourist in Centennial Olympic Park:")
    s1 = agent.monitor_tourist("T-100", 33.7600, -84.3930)
    print(f"Risk: {s1['effective_risk_level']} | Zone: {s1['effective_zone_name']} | Alert: {s1['new_alert_generated']}")

    # Step 2: Tourist enters Downtown High Crime Zone (33.7530, -84.3880)
    print("\n2. Tourist enters Downtown High Risk Area:")
    s2 = agent.monitor_tourist("T-100", 33.7530, -84.3880)
    print(f"Risk: {s2['effective_risk_level']} | Zone: {s2['effective_zone_name']} | Alert: {s2['new_alert_generated']}")
    if s2["active_alert"]:
        print(f"Warning: {s2['active_alert']['message']}")
    if s2["safe_route_recommendation"]:
        print(f"Safe Route to: {s2['safe_route_recommendation']['destination']['name']}")

    # Step 3: Tourist enters Restricted Rail Yard (33.7980, -84.4350)
    print("\n3. Tourist approaches Restricted Inman Rail Yard:")
    s3 = agent.monitor_tourist("T-100", 33.7980, -84.4350, auto_dispatch_emergency=True)
    print(f"Risk: {s3['effective_risk_level']} | Alert: {s3['new_alert_generated']}")
    if s3["emergency_dispatch"]:
        print(f"Emergency Unit Dispatched: {s3['emergency_dispatch']['dispatched_unit']['unit_id']} (ETA: {s3['emergency_dispatch']['dispatched_unit']['eta_minutes']} min)")

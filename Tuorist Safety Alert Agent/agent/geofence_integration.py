"""
Module 3: Geofencing Integration
Integrates the existing Geofencing Agent from Geo-Fancing/geofence.py.
Manages safety and danger zones (polygons) across Atlanta.
Maintains stateful tracking per tourist to detect ENTRY, EXIT, and INSIDE events,
and eliminates redundant repetitive alerts while the tourist remains inside a zone.
"""

import sys
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from shapely.geometry import Point, shape

logger = logging.getLogger(__name__)

# Attempt to locate and import check_location from existing Geofencing Agent
BASE_DIR = Path(__file__).resolve().parent.parent
GEO_FANCING_DIR = BASE_DIR.parent / "Geo-Fancing"

if GEO_FANCING_DIR.exists():
    sys.path.insert(0, str(GEO_FANCING_DIR))
    try:
        from geofence import check_location as existing_check_location
        logger.info(f"Successfully imported existing check_location from {GEO_FANCING_DIR / 'geofence.py'}")
    except ImportError:
        existing_check_location = None
else:
    existing_check_location = None


def check_location(latitude: float, longitude: float, zones: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates whether (latitude, longitude) is inside any geofenced zone.
    Delegates to the existing Geofencing Agent function if available,
    while providing identical Shapely point-in-polygon resolution.
    """
    if existing_check_location is not None:
        return existing_check_location(latitude, longitude, zones)

    # Built-in reference implementation exactly matching the Geofencing Agent
    tourist_point = Point(longitude, latitude)

    for zone in zones:
        geometry = shape(zone["geometry"])
        if geometry.contains(tourist_point):
            return {
                "inside": True,
                "zone_name": zone["name"],
                "risk_level": zone.get("risk_level", "LOW"),
                "zone_type": zone.get("zone_type", "SAFE"),
                "message": f"You entered {zone['name']}",
            }

    return {
        "inside": False,
        "zone_name": None,
        "risk_level": "LOW",
        "zone_type": "SAFE",
        "message": "You are currently outside the monitored danger zones.",
    }


class GeofenceManager:
    """
    Manages loading, persistence, and querying of safety and danger zones.
    Standardized to GeoJSON Polygon geometry compatible with existing Geofencing Agent.
    """

    def __init__(self, zones_file: Optional[str] = None):
        if zones_file:
            self.zones_file = Path(zones_file)
        else:
            self.zones_file = BASE_DIR / "datasets" / "atlanta_safety_zones.json"
        
        self.zones: List[Dict[str, Any]] = []
        self.load_zones()

    def load_zones(self) -> List[Dict[str, Any]]:
        """Loads zones from JSON file or initializes default Atlanta safety zones."""
        if self.zones_file.exists():
            try:
                with open(self.zones_file, "r", encoding="utf-8") as f:
                    self.zones = json.load(f)
                logger.info(f"Loaded {len(self.zones)} safety zones from {self.zones_file}")
                return self.zones
            except Exception as e:
                logger.warning(f"Failed to read zones file {self.zones_file}: {e}")

        # Initialize canonical Atlanta safety, risk, and restricted zones
        self.zones = self._init_default_atlanta_zones()
        self.save_zones()
        return self.zones

    def save_zones(self) -> None:
        """Saves current zones to disk."""
        self.zones_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.zones_file, "w", encoding="utf-8") as f:
            json.dump(self.zones, f, indent=4)
        logger.info(f"Saved {len(self.zones)} safety zones to {self.zones_file}")

    def _init_default_atlanta_zones(self) -> List[Dict[str, Any]]:
        """
        Creates authentic Atlanta geofenced zones:
        - SAFE: Centennial Olympic Park, Piedmont Park, Midtown Arts
        - HIGH_RISK: Downtown Hotspot, Old Fourth Ward Corridor, West End
        - VERY_HIGH: Bankhead Sector
        - RESTRICTED: Inman Rail Yards, CSX Hulsey Yard, Chattahoochee Water Works
        """
        default_zones = [
            {
                "id": str(uuid.uuid4()),
                "name": "Centennial Olympic Park Safe Haven",
                "risk_level": "LOW",
                "zone_type": "SAFE",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.3965, 33.7585],
                        [-84.3910, 33.7585],
                        [-84.3910, 33.7635],
                        [-84.3965, 33.7635],
                        [-84.3965, 33.7585],
                    ]],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Piedmont Park Tourist Corridor",
                "risk_level": "LOW",
                "zone_type": "SAFE",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.3780, 33.7820],
                        [-84.3680, 33.7820],
                        [-84.3680, 33.7915],
                        [-84.3780, 33.7915],
                        [-84.3780, 33.7820],
                    ]],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Midtown Arts & Culture Safe Haven",
                "risk_level": "LOW",
                "zone_type": "SAFE",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.3890, 33.7860],
                        [-84.3810, 33.7860],
                        [-84.3810, 33.7940],
                        [-84.3890, 33.7940],
                        [-84.3890, 33.7860],
                    ]],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Downtown Central High-Theft Zone",
                "risk_level": "HIGH",
                "zone_type": "HIGH_RISK",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.3930, 33.7500],
                        [-84.3830, 33.7500],
                        [-84.3830, 33.7570],
                        [-84.3930, 33.7570],
                        [-84.3930, 33.7500],
                    ]],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Old Fourth Ward Elevated Incident Zone",
                "risk_level": "MEDIUM",
                "zone_type": "HIGH_RISK",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.3770, 33.7530],
                        [-84.3660, 33.7530],
                        [-84.3660, 33.7610],
                        [-84.3770, 33.7610],
                        [-84.3770, 33.7530],
                    ]],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "name": "West End High Crime Risk Zone",
                "risk_level": "HIGH",
                "zone_type": "HIGH_RISK",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.4300, 33.7320],
                        [-84.4150, 33.7320],
                        [-84.4150, 33.7420],
                        [-84.4300, 33.7420],
                        [-84.4300, 33.7320],
                    ]],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Bankhead Extreme Risk Area",
                "risk_level": "VERY_HIGH",
                "zone_type": "HIGH_RISK",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.4500, 33.7650],
                        [-84.4330, 33.7650],
                        [-84.4330, 33.7750],
                        [-84.4500, 33.7750],
                        [-84.4500, 33.7650],
                    ]],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Inman Industrial Rail Switching Yard",
                "risk_level": "HIGH",
                "zone_type": "RESTRICTED",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.4450, 33.7950],
                        [-84.4280, 33.7950],
                        [-84.4280, 33.8050],
                        [-84.4450, 33.8050],
                        [-84.4450, 33.7950],
                    ]],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "name": "CSX Hulsey Intermodal Security Zone",
                "risk_level": "HIGH",
                "zone_type": "RESTRICTED",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.3650, 33.7520],
                        [-84.3500, 33.7520],
                        [-84.3500, 33.7580],
                        [-84.3650, 33.7580],
                        [-84.3650, 33.7520],
                    ]],
                },
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Chattahoochee Municipal Water Works",
                "risk_level": "HIGH",
                "zone_type": "RESTRICTED",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.4480, 33.8200],
                        [-84.4320, 33.8200],
                        [-84.4320, 33.8320],
                        [-84.4480, 33.8320],
                        [-84.4480, 33.8200],
                    ]],
                },
            },
        ]
        return default_zones

    def add_zone(
        self,
        name: str,
        risk_level: str,
        zone_type: str,
        coordinates: List[List[float]],
    ) -> Dict[str, Any]:
        """Creates and persists a new zone polygon."""
        new_zone = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "risk_level": risk_level.upper(),
            "zone_type": zone_type.upper(),
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates],
            },
        }
        self.zones.append(new_zone)
        self.save_zones()
        return new_zone

    def remove_zone(self, zone_id: str) -> bool:
        """Deletes a zone by id."""
        initial = len(self.zones)
        self.zones = [z for z in self.zones if z["id"] != zone_id]
        if len(self.zones) < initial:
            self.save_zones()
            return True
        return False


class TouristLocationTracker:
    """
    Maintains continuous state for tourists.
    Detects ENTRY, EXIT, and INSIDE events.
    Applies suppression logic to avoid spamming repeated alerts while remaining in the same zone.
    """

    def __init__(self, geofence_manager: GeofenceManager):
        self.manager = geofence_manager
        # Mapping tourist_id -> state dict
        self.tourist_states: Dict[str, Dict[str, Any]] = {}

    def update_tourist_location(
        self,
        tourist_id: str,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Receives new GPS coordinate for tourist and computes zone status and state transition.
        Returns transition event details:
          - event_type: "ENTRY", "EXIT", "INSIDE_UNCHANGED", "RISK_ESCALATION", "OUTSIDE"
          - alert_required: bool (True only when new warning should be surfaced)
          - zone_name: str
          - risk_level: str
          - zone_type: str
        """
        now = timestamp or datetime.now()
        geofence_res = check_location(latitude, longitude, self.manager.zones)

        current_inside = geofence_res["inside"]
        current_zone_name = geofence_res["zone_name"]
        current_risk_level = geofence_res["risk_level"]
        current_zone_type = geofence_res["zone_type"]

        # Retrieve previous tourist state
        prev_state = self.tourist_states.get(tourist_id, {
            "inside": False,
            "zone_name": None,
            "risk_level": "LOW",
            "zone_type": "SAFE",
            "last_coordinates": None,
            "last_alert_time": None,
            "entry_time": None,
        })

        event_type = "OUTSIDE"
        alert_required = False
        message = ""

        # Case 1: Tourist entered a zone (was outside, or moved from one zone to another)
        if current_inside and (not prev_state["inside"] or prev_state["zone_name"] != current_zone_name):
            event_type = "ENTRY"
            alert_required = True
            message = f"Tourist entered geofenced area: '{current_zone_name}' ({current_zone_type})"
            entry_time = now

        # Case 2: Tourist remains inside the SAME zone
        elif current_inside and prev_state["inside"] and prev_state["zone_name"] == current_zone_name:
            # Check if risk escalated
            risk_severity = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "VERY_HIGH": 3}
            prev_sev = risk_severity.get(prev_state["risk_level"], 0)
            curr_sev = risk_severity.get(current_risk_level, 0)

            if curr_sev > prev_sev:
                event_type = "RISK_ESCALATION"
                alert_required = True
                message = f"Risk escalated in '{current_zone_name}' from {prev_state['risk_level']} to {current_risk_level}!"
            else:
                # Same zone, no risk escalation -> SUPPRESS REPEATED ALERT
                event_type = "INSIDE_UNCHANGED"
                alert_required = False
                message = f"Tourist remains inside '{current_zone_name}'. Repeated alert suppressed."
            
            entry_time = prev_state.get("entry_time", now)

        # Case 3: Tourist exited a zone into unmonitored / safe territory
        elif not current_inside and prev_state["inside"]:
            event_type = "EXIT"
            alert_required = True
            message = f"Tourist exited danger zone: '{prev_state['zone_name']}'. Now in safe perimeter."
            entry_time = None

        # Case 4: Tourist remains outside all geofenced zones
        else:
            event_type = "OUTSIDE"
            alert_required = False
            message = "Tourist is outside monitored geofences."
            entry_time = None

        # Update persisted state for this tourist
        self.tourist_states[tourist_id] = {
            "inside": current_inside,
            "zone_name": current_zone_name,
            "risk_level": current_risk_level,
            "zone_type": current_zone_type,
            "last_coordinates": (latitude, longitude),
            "last_alert_time": now if alert_required else prev_state.get("last_alert_time"),
            "entry_time": entry_time,
            "last_event_type": event_type,
        }

        return {
            "tourist_id": tourist_id,
            "coordinates": (latitude, longitude),
            "timestamp": now.isoformat(),
            "inside": current_inside,
            "zone_name": current_zone_name,
            "risk_level": current_risk_level,
            "zone_type": current_zone_type,
            "event_type": event_type,
            "alert_required": alert_required,
            "status_message": message,
            "entry_time": entry_time.isoformat() if entry_time else None,
        }

    def reset_tourist(self, tourist_id: str) -> None:
        """Clears state for a tourist session."""
        if tourist_id in self.tourist_states:
            del self.tourist_states[tourist_id]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mgr = GeofenceManager()
    tracker = TouristLocationTracker(mgr)

    print(f"Total Geofenced Zones: {len(mgr.zones)}")

    # Test coordinate 1: Downtown High Crime Zone (33.7530, -84.3880)
    print("\n--- Step 1: Tourist walks into Downtown High Risk Zone ---")
    ev1 = tracker.update_tourist_location("T-01", 33.7530, -84.3880)
    print(f"Event: {ev1['event_type']}, Alert Required: {ev1['alert_required']}, Zone: {ev1['zone_name']}")

    # Test coordinate 2: Tourist takes 2 steps inside the same zone (33.7535, -84.3882)
    print("\n--- Step 2: Tourist stays inside Downtown Zone (Suppression Test) ---")
    ev2 = tracker.update_tourist_location("T-01", 33.7535, -84.3882)
    print(f"Event: {ev2['event_type']}, Alert Required: {ev2['alert_required']}, Message: {ev2['status_message']}")

    # Test coordinate 3: Tourist exits zone to Safe Haven (Centennial Olympic Park: 33.7600, -84.3930)
    print("\n--- Step 3: Tourist moves to Centennial Olympic Park ---")
    ev3 = tracker.update_tourist_location("T-01", 33.7600, -84.3930)
    print(f"Event: {ev3['event_type']}, Alert Required: {ev3['alert_required']}, Zone: {ev3['zone_name']}")

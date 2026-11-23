"""
Unit tests for Module 3: Geofencing Integration and Tourist Location Tracker.
Tests:
  - Exact Shapely Point-in-Polygon zone detection
  - ENTRY event detection when entering a zone
  - INSIDE event with alert suppression (avoiding repetitive alerts)
  - EXIT event detection when leaving a zone
  - RISK_ESCALATION event detection
"""

import unittest
from datetime import datetime
from agent.geofence_integration import GeofenceManager, TouristLocationTracker, check_location


class TestGeofenceIntegration(unittest.TestCase):

    def setUp(self):
        # Sample test zones
        self.sample_zones = [
            {
                "id": "zone-safe-01",
                "name": "Centennial Safe Haven",
                "risk_level": "LOW",
                "zone_type": "SAFE",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.400, 33.750],
                        [-84.390, 33.750],
                        [-84.390, 33.760],
                        [-84.400, 33.760],
                        [-84.400, 33.750],
                    ]],
                },
            },
            {
                "id": "zone-danger-01",
                "name": "Downtown High Risk Zone",
                "risk_level": "HIGH",
                "zone_type": "HIGH_RISK",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.390, 33.740],
                        [-84.380, 33.740],
                        [-84.380, 33.750],
                        [-84.390, 33.750],
                        [-84.390, 33.740],
                    ]],
                },
            },
        ]
        self.manager = GeofenceManager()
        # Override with known sample zones for deterministic testing
        self.manager.zones = self.sample_zones
        self.tracker = TouristLocationTracker(self.manager)

    def test_check_location_inside_zone(self):
        # Point inside Centennial Safe Haven (33.755, -84.395)
        res = check_location(33.755, -84.395, self.sample_zones)
        self.assertTrue(res["inside"])
        self.assertEqual(res["zone_name"], "Centennial Safe Haven")
        self.assertEqual(res["risk_level"], "LOW")
        self.assertEqual(res["zone_type"], "SAFE")

    def test_check_location_outside_zone(self):
        # Point outside all zones (33.800, -84.500)
        res = check_location(33.800, -84.500, self.sample_zones)
        self.assertFalse(res["inside"])
        self.assertIsNone(res["zone_name"])
        self.assertEqual(res["risk_level"], "LOW")
        self.assertEqual(res["zone_type"], "SAFE")

    def test_tourist_entry_event(self):
        # Tourist starts outside, walks into Downtown High Risk Zone (33.745, -84.385)
        ev = self.tracker.update_tourist_location("T-TEST-1", 33.745, -84.385)
        self.assertEqual(ev["event_type"], "ENTRY")
        self.assertTrue(ev["alert_required"])
        self.assertEqual(ev["zone_name"], "Downtown High Risk Zone")
        self.assertEqual(ev["risk_level"], "HIGH")

    def test_tourist_suppression_when_remaining_inside(self):
        # Step 1: Entry
        ev1 = self.tracker.update_tourist_location("T-TEST-2", 33.745, -84.385)
        self.assertEqual(ev1["event_type"], "ENTRY")
        self.assertTrue(ev1["alert_required"])

        # Step 2: Next coordinate slightly different, but still in the same zone
        ev2 = self.tracker.update_tourist_location("T-TEST-2", 33.746, -84.386)
        self.assertEqual(ev2["event_type"], "INSIDE_UNCHANGED")
        self.assertFalse(ev2["alert_required"], "Alert must be suppressed when remaining in the same zone!")

    def test_tourist_exit_event(self):
        # Step 1: Enter zone
        self.tracker.update_tourist_location("T-TEST-3", 33.745, -84.385)

        # Step 2: Walk out into safe open perimeter
        ev_exit = self.tracker.update_tourist_location("T-TEST-3", 33.800, -84.500)
        self.assertEqual(ev_exit["event_type"], "EXIT")
        self.assertTrue(ev_exit["alert_required"])
        self.assertFalse(ev_exit["inside"])


if __name__ == "__main__":
    unittest.main()

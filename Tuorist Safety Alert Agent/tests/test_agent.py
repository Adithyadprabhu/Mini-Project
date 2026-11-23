"""
Integration tests for the complete TouristSafetyAgent pipeline.
Tests:
  - End-to-end tourist monitoring pipeline
  - Ambient ML risk prediction integration
  - Geofence trigger and alert generation
  - Safe route recommendation integration
  - Emergency SOS panic button trigger and dispatch
"""

import unittest
from agent.tourist_safety_agent import TouristSafetyAgent


class TestTouristSafetyAgent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate agent
        cls.agent = TouristSafetyAgent(auto_load_model=True)

    def test_monitor_tourist_safe_zone(self):
        # Tourist at Centennial Olympic Park (33.7600, -84.3930)
        res = self.agent.monitor_tourist(
            tourist_id="T-INT-01",
            latitude=33.7600,
            longitude=-84.3930,
        )
        self.assertEqual(res["tourist_id"], "T-INT-01")
        self.assertEqual(res["effective_risk_level"], "LOW")
        self.assertIn("Centennial", res["effective_zone_name"])
        self.assertTrue(res["geofence_status"]["inside"])

    def test_monitor_tourist_high_risk_zone(self):
        # Tourist enters Downtown Central High-Theft Zone (33.7530, -84.3880)
        res = self.agent.monitor_tourist(
            tourist_id="T-INT-02",
            latitude=33.7530,
            longitude=-84.3880,
        )
        self.assertEqual(res["effective_risk_level"], "HIGH")
        self.assertTrue(res["new_alert_generated"])
        self.assertIsNotNone(res["active_alert"])
        self.assertEqual(res["active_alert"]["risk_level"], "HIGH")
        self.assertIsNotNone(res["safe_route_recommendation"])

    def test_monitor_tourist_restricted_zone_emergency(self):
        # Tourist approaches Inman Rail Yard (33.8000, -84.4360)
        res = self.agent.monitor_tourist(
            tourist_id="T-INT-03",
            latitude=33.8000,
            longitude=-84.4360,
            auto_dispatch_emergency=True,
        )
        self.assertEqual(res["effective_zone_type"], "RESTRICTED")
        self.assertTrue(res["new_alert_generated"])
        self.assertIsNotNone(res["emergency_dispatch"])
        self.assertTrue(res["emergency_dispatch"]["dispatch_success"])

    def test_manual_sos_trigger(self):
        sos_res = self.agent.trigger_sos("T-INT-04", 33.7550, -84.3900)
        self.assertEqual(sos_res["status"], "SOS_DISPATCHED")
        self.assertTrue(sos_res["dispatch"]["dispatch_success"])
        self.assertIn("EMERGENCY SOS", sos_res["alert"]["message"])
        self.assertIsNotNone(sos_res["evasive_route"])


if __name__ == "__main__":
    unittest.main()

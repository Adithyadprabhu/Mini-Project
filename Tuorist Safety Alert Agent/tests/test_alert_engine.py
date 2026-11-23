"""
Unit tests for Module 4: Alert Engine.
Tests:
  - Generation of all required alert levels: LOW, MEDIUM, HIGH, VERY_HIGH, RESTRICTED
  - Verification that all required fields are present in the alert payload:
    coordinates, zone name, risk level, message, timestamp, recommended action.
  - Verification of emergency dispatch eligibility flag.
"""

import unittest
from agent.alert_engine import AlertEngine, AlertType


class TestAlertEngine(unittest.TestCase):

    def setUp(self):
        self.engine = AlertEngine()
        self.coords = (33.7530, -84.3880)

    def test_low_risk_alert(self):
        alert = self.engine.generate_alert(
            tourist_id="T-01",
            coordinates=self.coords,
            risk_level="LOW",
            zone_name="Centennial Olympic Park",
            zone_type="SAFE",
        )
        d = alert.to_dict()
        self.assertEqual(d["risk_level"], "LOW")
        self.assertEqual(d["alert_type"], AlertType.NO_WARNING.value)
        self.assertIn("SAFE ZONE", d["message"])
        self.assertFalse(d["emergency_dispatch_eligible"])
        self._verify_required_fields(d)

    def test_medium_risk_alert(self):
        alert = self.engine.generate_alert(
            tourist_id="T-01",
            coordinates=self.coords,
            risk_level="MEDIUM",
            zone_name="Old Fourth Ward",
            zone_type="HIGH_RISK",
        )
        d = alert.to_dict()
        self.assertEqual(d["risk_level"], "MEDIUM")
        self.assertEqual(d["alert_type"], AlertType.CAUTION.value)
        self.assertIn("CAUTION", d["message"])
        self._verify_required_fields(d)

    def test_high_risk_alert(self):
        alert = self.engine.generate_alert(
            tourist_id="T-01",
            coordinates=self.coords,
            risk_level="HIGH",
            zone_name="Downtown Core",
            zone_type="HIGH_RISK",
        )
        d = alert.to_dict()
        self.assertEqual(d["risk_level"], "HIGH")
        self.assertEqual(d["alert_type"], AlertType.SAFETY_WARNING.value)
        self.assertIn("SAFETY WARNING", d["message"])
        self._verify_required_fields(d)

    def test_very_high_risk_alert(self):
        alert = self.engine.generate_alert(
            tourist_id="T-01",
            coordinates=self.coords,
            risk_level="VERY_HIGH",
            zone_name="Bankhead Sector",
            zone_type="HIGH_RISK",
        )
        d = alert.to_dict()
        self.assertEqual(d["risk_level"], "VERY_HIGH")
        self.assertEqual(d["alert_type"], AlertType.URGENT_SAFETY_WARNING.value)
        self.assertTrue(d["emergency_dispatch_eligible"])
        self._verify_required_fields(d)

    def test_restricted_zone_alert(self):
        alert = self.engine.generate_alert(
            tourist_id="T-01",
            coordinates=self.coords,
            risk_level="HIGH",
            zone_name="Inman Rail Yards",
            zone_type="RESTRICTED",
        )
        d = alert.to_dict()
        self.assertEqual(d["risk_level"], "RESTRICTED")
        self.assertEqual(d["alert_type"], AlertType.RESTRICTED_ACCESS.value)
        self.assertIn("RESTRICTED AREA", d["message"])
        self.assertTrue(d["emergency_dispatch_eligible"])
        self._verify_required_fields(d)

    def _verify_required_fields(self, alert_dict):
        required = [
            "alert_id",
            "tourist_id",
            "tourist_coordinates",
            "zone_name",
            "risk_level",
            "alert_type",
            "message",
            "recommended_action",
            "timestamp",
        ]
        for field in required:
            self.assertIn(field, alert_dict, f"Missing required field '{field}' in alert payload")
        self.assertIn("latitude", alert_dict["tourist_coordinates"])
        self.assertIn("longitude", alert_dict["tourist_coordinates"])
        self.assertTrue(len(alert_dict["recommended_action"]) > 0)


if __name__ == "__main__":
    unittest.main()

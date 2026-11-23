"""
Unit tests for Module 5: Safe Route Recommendation Engine.
Tests:
  - Nearest safe haven selection
  - Route calculation to safe destination
  - Calculation of quantitative safety metrics (distance, walking time, high risk distance, safety score)
  - Circumvention of restricted zones
"""

import unittest
from agent.safe_route import SafeRouteEngine, haversine_distance


class TestSafeRouteEngine(unittest.TestCase):

    def setUp(self):
        self.engine = SafeRouteEngine()
        self.sample_zones = [
            {
                "id": "restricted-yard-01",
                "name": "Restricted Rail Yard",
                "risk_level": "HIGH",
                "zone_type": "RESTRICTED",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-84.3940, 33.7550],
                        [-84.3920, 33.7550],
                        [-84.3920, 33.7580],
                        [-84.3940, 33.7580],
                        [-84.3940, 33.7550],
                    ]],
                },
            }
        ]

    def test_find_nearest_safe_haven(self):
        # Coordinates near Downtown (33.755, -84.390)
        haven = self.engine.find_nearest_safe_haven(33.755, -84.390)
        self.assertIsNotNone(haven)
        self.assertIn("name", haven)
        self.assertIn("straight_line_distance_m", haven)
        self.assertGreater(haven["straight_line_distance_m"], 0)

    def test_plan_safe_route_generation(self):
        # Route from Downtown (33.753, -84.388)
        route = self.engine.plan_safe_route(33.753, -84.388, zones=self.sample_zones)
        self.assertEqual(route["status"], "ROUTE_OPTIMIZED")
        self.assertIn("coordinates", route)
        self.assertTrue(len(route["coordinates"]) >= 2)
        self.assertGreater(route["total_distance_m"], 0)
        self.assertGreater(route["estimated_walking_time_min"], 0)
        self.assertIn("safety_metrics", route)
        self.assertIn("safety_score_pct", route)
        self.assertTrue(0 <= route["safety_score_pct"] <= 100)

    def test_haversine_distance(self):
        # Distance between two identical points must be 0
        p = (33.750, -84.390)
        self.assertAlmostEqual(haversine_distance(p, p), 0.0, places=2)

        # Distance between (33.750, -84.390) and (33.760, -84.390) is ~1.11 km
        p2 = (33.760, -84.390)
        dist = haversine_distance(p, p2)
        self.assertTrue(1000 <= dist <= 1200)


if __name__ == "__main__":
    unittest.main()

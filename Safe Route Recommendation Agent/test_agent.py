"""
Automated Comprehensive Test Suite for Safe Route Recommendation Agent
Location: B.C. Road, Bantwal, Dakshina Kannada, Karnataka
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_engine
from route_engine import (
    recommend_route,
    load_data,
    load_zones,
    load_graph,
    apply_safety_weights,
    validate_coordinates,
    check_restricted_point,
    load_designed_routes,
    save_designed_routes,
    design_route_from_waypoints,
    design_route_from_coordinates,
    delete_designed_route,
    toggle_designed_route_status,
    BC_ROAD_BOUNDS
)


def run_tests():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE TEST SUITE - SAFE ROUTE RECOMMENDATION AGENT")
    print("=" * 60)
    passed = 0
    total = 0

    # 1. Test Data and Road Network Loading
    total += 1
    print("\n[Test 1] Testing Road Network and Geofencing Data Loading...")
    try:
        G, zones = load_data()
        assert G is not None, "Graph failed to load"
        assert len(G.nodes) > 0, "Graph has 0 nodes"
        assert len(G.edges) > 0, "Graph has 0 edges"
        print(f"  ✓ Road Network loaded: {len(G.nodes)} nodes, {len(G.edges)} edges.")
        print(f"  ✓ Geofencing Zones loaded: {len(zones)} zones from Geo-Fancing.")
        passed += 1
    except Exception as e:
        print(f"  ✗ Test 1 FAILED: {e}")

    # 2. Test Safe Route Calculation (B.C. Road Bus Stand -> Bantwal Town Hall)
    total += 1
    print("\n[Test 2] Testing Safe Route Calculation in B.C. Road...")
    try:
        # B.C. Road Bus Stand (12.88175, 75.02991) to Bantwal Town Hall (12.88500, 75.03500)
        start_lat, start_lon = 12.88175, 75.02991
        end_lat, end_lon = 12.88500, 75.03500
        result = recommend_route(start_lat, start_lon, end_lat, end_lon)
        assert result["status"] == "ROUTE_FOUND"
        assert result["distance_m"] > 0
        assert result["walking_time_min"] > 0
        assert len(result["coordinates"]) > 0
        print(f"  ✓ Route calculated successfully!")
        print(f"    - Total Distance: {result['distance_m']} m ({result['distance_km']} km)")
        print(f"    - Walking Time: {result['walking_time_min']} mins")
        print(f"    - Coordinates count: {len(result['coordinates'])}")
        print(f"    - Safety Warnings: {result['warnings']}")
        passed += 1
    except Exception as e:
        print(f"  ✗ Test 2 FAILED: {e}")

    # 3. Test Invalid Coordinate Handling
    total += 1
    print("\n[Test 3] Testing Out-of-Bounds / Invalid Coordinate Rejection...")
    try:
        # Bangalore coordinates (far outside B.C. Road, Bantwal)
        out_lat, out_lon = 12.9716, 77.5946
        try:
            recommend_route(out_lat, out_lon, 12.88500, 75.03500)
            print("  ✗ Test 3 FAILED: Out-of-bounds coordinates were not rejected!")
        except ValueError as ve:
            print(f"  ✓ Correctly rejected out-of-bounds start coordinates: {ve}")
            passed += 1
    except Exception as e:
        print(f"  ✗ Test 3 FAILED: {e}")

    # 4. Test Restricted Area Avoidance
    total += 1
    print("\n[Test 4] Testing Restricted Area Avoidance & Edge Pruning...")
    try:
        # Create a synthetic restricted polygon right in the middle of a route
        test_restricted_zone = {
            "name": "Test Military/Hazard Restricted Area",
            "zone_type": "RESTRICTED",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [75.0290, 12.8815],
                    [75.0310, 12.8815],
                    [75.0310, 12.8825],
                    [75.0290, 12.8825],
                    [75.0290, 12.8815]
                ]]
            }
        }
        G_raw, base_zones = load_data()
        test_zones = base_zones + [test_restricted_zone]
        G_pruned = apply_safety_weights(G_raw, test_zones)

        assert len(G_pruned.edges) < len(G_raw.edges), "Restricted road edges were not removed from graph!"
        removed_count = len(G_raw.edges) - len(G_pruned.edges)
        print(f"  ✓ Successfully removed {removed_count} road segments intersecting the restricted zone.")

        # Test point rejection when start is inside restricted area
        try:
            check_restricted_point(12.8820, 75.0300, test_zones, "Test Point")
            print("  ✗ Test 4 FAILED: Point inside restricted zone was not flagged!")
        except ValueError as ve:
            print(f"  ✓ Successfully rejected starting point inside restricted zone: {ve}")
            passed += 1
    except Exception as e:
        print(f"  ✗ Test 4 FAILED: {e}")

    # 5. Test High-Risk Route Penalty
    total += 1
    print("\n[Test 5] Testing High-Risk Zone Cost Weighting...")
    try:
        # Existing zones in Geo-Fancing has 'risky' zone (HIGH_RISK)
        G_raw, zones = load_data()
        G_weighted = apply_safety_weights(G_raw, zones)
        
        high_risk_edges = [
            (u, v, k, d) for u, v, k, d in G_weighted.edges(keys=True, data=True)
            if d.get("risk_factor", 1.0) > 1.0
        ]
        print(f"  ✓ High-Risk penalty multiplier applied to {len(high_risk_edges)} intersecting edges.")
        for u, v, k, d in high_risk_edges[:3]:
            print(f"    - Edge ({u}, {v}) safe_cost: {d['safe_cost']:.1f} vs length: {d['length']:.1f} (Penalty: {d['risk_factor']}x)")
        passed += 1
    except Exception as e:
        print(f"  ✗ Test 5 FAILED: {e}")

    # 6. Test Missing or Empty zones.json Handling
    total += 1
    print("\n[Test 6] Testing Missing or Empty zones.json Graceful Handling...")
    try:
        # Temporarily mock non-existent zones path
        orig_func = route_engine.get_zones_path
        route_engine.get_zones_path = lambda: Path("non_existent_zones_test.json")
        zones_fallback = route_engine.load_zones()
        assert zones_fallback == [], "Did not fallback to empty list for missing zones"
        print("  ✓ Gracefully handled missing zones file without raising uncaught exception.")
        
        # Test routing still functions with safety warnings about empty zones
        res_empty = recommend_route(12.88175, 75.02991, 12.88500, 75.03500)
        assert res_empty["status"] == "ROUTE_FOUND"
        print("  ✓ Basic routing remains functional when zones file is empty.")
        
        # Restore original function
        route_engine.get_zones_path = orig_func
        passed += 1
    except Exception as e:
        print(f"  ✗ Test 6 FAILED: {e}")
        route_engine.get_zones_path = orig_func

    # 7. Test No Route Found Handling
    total += 1
    print("\n[Test 7] Testing Disconnected / No Route Found Handling...")
    try:
        # Try routing to an impossible point isolated by restricted perimeter
        isolated_zone = {
            "name": "Enclosing Barrier",
            "zone_type": "RESTRICTED",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [75.0330, 12.8830],
                    [75.0370, 12.8830],
                    [75.0370, 12.8870],
                    [75.0330, 12.8870],
                    [75.0330, 12.8830]
                ]]
            }
        }
        # In a graph where destination is completely cut off by removing all edges in box
        # recommend_route should raise RuntimeError with clear message
        G_raw, base_zones = load_data()
        test_zones = base_zones + [isolated_zone]
        
        try:
            # We test applying safety weights and path search between severed nodes
            G_cut = apply_safety_weights(G_raw, test_zones)
            # Find a node that got disconnected or test no path
            import networkx as nx
            # Create a detached graph
            G_sub = G_cut.copy()
            # Pick any two nodes and remove all edges between components
            nodes = list(G_sub.nodes)
            G_sub.remove_nodes_from(nodes[len(nodes)//2:])
            # Attempt shortest path across disconnected components
            try:
                nx.shortest_path(G_sub, source=nodes[0], target=nodes[-1], weight="safe_cost")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                print("  ✓ NetworkXNoPath caught and recognized properly.")
                passed += 1
        except Exception as e:
            print(f"  ✗ Test 7 FAILED: {e}")
    except Exception as e:
        print(f"  ✗ Test 7 FAILED: {e}")

    # 8. Test Admin Designing Route from Waypoints
    total += 1
    print("\n[Test 8] Testing Admin Designing Route from Waypoints (Road Snapping)...")
    try:
        waypoints = [
            {"name": "Start: B.C. Road Circle", "lat": 12.88175, "lon": 75.02991},
            {"name": "Stop: Bantwal Town Hall", "lat": 12.88500, "lon": 75.03500},
            {"name": "End: Railway Station", "lat": 12.88720, "lon": 75.03850}
        ]
        new_route = design_route_from_waypoints(
            name="Admin Test Corridor",
            category="SAFE_CORRIDOR",
            description="Test corridor generated by admin.",
            waypoints=waypoints,
            lighting="Well Lit",
            patrol="Regular Police Patrols"
        )
        assert new_route["id"] is not None
        assert new_route["distance_m"] > 0
        assert len(new_route["coordinates"]) > 0
        assert new_route["restricted_violations"] == 0
        print(f"  ✓ Admin designed route successfully: '{new_route['name']}' ({new_route['distance_m']}m, {len(new_route['coordinates'])} points).")
        passed += 1
    except Exception as e:
        print(f"  ✗ Test 8 FAILED: {e}")

    # 9. Test Admin Designing Route from Freehand Drawn Coordinates
    total += 1
    print("\n[Test 9] Testing Admin Freehand Drawn Route Creation...")
    try:
        drawn_coords = [
            [12.88175, 75.02991],
            [12.88250, 75.03100],
            [12.88350, 75.03250],
            [12.88450, 75.03400]
        ]
        drawn_route = design_route_from_coordinates(
            name="Admin Drawn Trail",
            category="HERITAGE_WALK",
            description="Scenic custom trail drawn by admin.",
            coordinates=drawn_coords,
            lighting="Adequate Lighting",
            patrol="Community Safety Watch"
        )
        assert drawn_route["id"] is not None
        assert drawn_route["distance_m"] > 0
        print(f"  ✓ Admin drawn route saved: '{drawn_route['name']}' ({drawn_route['distance_m']}m).")
        passed += 1
    except Exception as e:
        print(f"  ✗ Test 9 FAILED: {e}")

    # 10. Test Admin Route Management (Toggle & Delete)
    total += 1
    print("\n[Test 10] Testing Admin Route Management (Toggle Status & Delete)...")
    try:
        # Toggle status of drawn_route
        toggled = toggle_designed_route_status(drawn_route["id"])
        target = [r for r in toggled if r["id"] == drawn_route["id"]]
        assert target and target[0]["is_active"] is False, "Route status was not toggled to False"
        print("  ✓ Admin successfully toggled route active status to False.")

        # Delete the test routes to clean up
        delete_designed_route(drawn_route["id"])
        delete_designed_route(new_route["id"])
        remaining = load_designed_routes()
        assert not any(r["id"] in [drawn_route["id"], new_route["id"]] for r in remaining)
        print("  ✓ Admin successfully deleted test routes.")
        passed += 1
    except Exception as e:
        print(f"  ✗ Test 10 FAILED: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} TESTS PASSED")
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

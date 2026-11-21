import json
import logging
import math
import uuid
from datetime import datetime
from pathlib import Path
import numpy as np
import networkx as nx
import osmnx as ox
from shapely.geometry import shape, Point, LineString

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
GRAPH_FILE = BASE_DIR / "bc_road_walk.graphml"
DESIGNED_ROUTES_FILE = BASE_DIR / "designed_routes.json"

# Geographic boundary for B.C. Road, Bantwal monitoring area
BC_ROAD_BOUNDS = {
    "min_lat": 12.8500,
    "max_lat": 12.9150,
    "min_lon": 75.0000,
    "max_lon": 75.0600
}

# Average walking speed: ~1.33 m/s (~4.8 km/h)
AVERAGE_WALKING_SPEED_MPS = 1.33

# Safety zone multipliers
WEIGHT_SAFE = 0.8        # Prefer safe roads
WEIGHT_HIGH_RISK = 7.5   # Heavy penalty on high-risk roads
WEIGHT_NORMAL = 1.0


def get_zones_path() -> Path:
    """Find the path to zones.json from the Geofencing Agent or local workspace."""
    candidate_paths = [
        BASE_DIR.parent / "Geo-Fancing" / "zones.json",
        BASE_DIR.parent / "Geofencing_Agent" / "zones.json",
        BASE_DIR / "zones.json"
    ]
    for path in candidate_paths:
        if path.exists():
            return path
    return candidate_paths[0]


def load_zones():
    """Load safety zones from zones.json."""
    zones_file = get_zones_path()
    if not zones_file.exists():
        logger.warning(f"Zones file not found at: {zones_file}")
        return []
    
    try:
        with open(zones_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"Zones file is empty: {zones_file}")
                return []
            zones = json.loads(content)
            if not isinstance(zones, list):
                logger.warning(f"Zones data is not a list in: {zones_file}")
                return []
            return zones
    except Exception as e:
        logger.error(f"Error loading zones from {zones_file}: {e}")
        return []


def load_graph():
    """Load the B.C. Road road network graph."""
    if not GRAPH_FILE.exists():
        logger.info(f"Graph file {GRAPH_FILE} not found. Attempting to download...")
        center = (12.88175, 75.02991)
        ox.settings.use_cache = True
        G = ox.graph_from_point(center, dist=3000, network_type="walk", simplify=True)
        ox.save_graphml(G, filepath=GRAPH_FILE)
        return G
    return ox.load_graphml(GRAPH_FILE)


def load_data():
    """Load graph and geofencing zones."""
    G = load_graph()
    zones = load_zones()
    return G, zones


def validate_coordinates(lat: float, lon: float, label: str = "Location"):
    """Validate if coordinates are within the B.C. Road operational boundary."""
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        raise ValueError(f"{label} has invalid numeric coordinates: ({lat}, {lon})")

    if not (BC_ROAD_BOUNDS["min_lat"] <= lat <= BC_ROAD_BOUNDS["max_lat"] and
            BC_ROAD_BOUNDS["min_lon"] <= lon <= BC_ROAD_BOUNDS["max_lon"]):
        raise ValueError(
            f"{label} ({lat:.5f}, {lon:.5f}) is outside the operational area of B.C. Road, Bantwal. "
            f"Allowed range: Lat [{BC_ROAD_BOUNDS['min_lat']}, {BC_ROAD_BOUNDS['max_lat']}], "
            f"Lon [{BC_ROAD_BOUNDS['min_lon']}, {BC_ROAD_BOUNDS['max_lon']}]."
        )


def check_restricted_point(lat: float, lon: float, zones: list, label: str = "Location"):
    """Check if a coordinate lies inside a restricted zone."""
    point = Point(lon, lat)
    for zone in zones:
        if zone.get("zone_type") == "RESTRICTED":
            try:
                poly = shape(zone["geometry"])
                if poly.contains(point) or poly.touches(point):
                    raise ValueError(
                        f"{label} is inside RESTRICTED zone '{zone.get('name', 'Restricted Area')}'. "
                        "Access to restricted zones is strictly prohibited."
                    )
            except Exception as e:
                if "RESTRICTED zone" in str(e):
                    raise
                logger.error(f"Error checking point in zone {zone}: {e}")


def apply_safety_weights(G, zones):
    """
    Apply risk-weighted costs to graph edges and exclude restricted segments.
    - RESTRICTED zones: Roads removed entirely.
    - HIGH_RISK zones: Higher cost penalty (WEIGHT_HIGH_RISK).
    - SAFE zones: Lower cost preference (WEIGHT_SAFE).
    - Other roads: Standard length cost (WEIGHT_NORMAL).
    """
    G = G.copy()

    zone_shapes = []
    for zone in zones:
        try:
            poly = shape(zone["geometry"])
            if poly.is_valid:
                zone_shapes.append({
                    "name": zone.get("name", "Zone"),
                    "geometry": poly,
                    "type": zone.get("zone_type", "SAFE")
                })
        except Exception as e:
            logger.warning(f"Skipping invalid zone geometry: {e}")

    restricted_edges = []

    for u, v, k, data in G.edges(keys=True, data=True):
        geometry = data.get("geometry")
        if geometry is None:
            geometry = LineString([
                (G.nodes[u]["x"], G.nodes[u]["y"]),
                (G.nodes[v]["x"], G.nodes[v]["y"])
            ])

        risk_penalty = WEIGHT_NORMAL
        is_restricted = False
        zone_name = None

        for z in zone_shapes:
            if geometry.intersects(z["geometry"]):
                if z["type"] == "RESTRICTED":
                    is_restricted = True
                    break
                elif z["type"] == "HIGH_RISK":
                    risk_penalty = max(risk_penalty, WEIGHT_HIGH_RISK)
                    zone_name = z["name"]
                elif z["type"] == "SAFE":
                    risk_penalty = min(risk_penalty, WEIGHT_SAFE)

        if is_restricted:
            restricted_edges.append((u, v, k))
        else:
            length = float(data.get("length", 1.0))
            G[u][v][k]["safe_cost"] = length * risk_penalty
            G[u][v][k]["risk_factor"] = risk_penalty
            G[u][v][k]["zone_intersected"] = zone_name

    # Remove restricted road segments completely
    G.remove_edges_from(restricted_edges)
    return G


def extract_route_details(G, node_list, zones):
    """Extract coordinates, distance, travel time, and safety summary for a node path."""
    route_edges = ox.routing.route_to_gdf(G, node_list, weight="safe_cost")
    
    coordinates = []
    for geometry in route_edges.geometry:
        if geometry is not None:
            for lon, lat in geometry.coords:
                pt = [lat, lon]
                if not coordinates or coordinates[-1] != pt:
                    coordinates.append(pt)

    total_distance = float(route_edges["length"].sum())
    walking_time_min = round(total_distance / (AVERAGE_WALKING_SPEED_MPS * 60), 1)

    # Analyze safety along the route
    high_risk_distance = 0.0
    safe_distance = 0.0
    restricted_violations = 0

    zone_polygons = []
    for z in zones:
        try:
            zone_polygons.append({
                "type": z.get("zone_type"),
                "name": z.get("name"),
                "shape": shape(z["geometry"])
            })
        except Exception:
            pass

    for _, row in route_edges.iterrows():
        edge_geom = row.geometry
        edge_len = float(row.get("length", 0.0))
        if edge_geom is not None:
            for zp in zone_polygons:
                if edge_geom.intersects(zp["shape"]):
                    if zp["type"] == "HIGH_RISK":
                        high_risk_distance += edge_len
                    elif zp["type"] == "SAFE":
                        safe_distance += edge_len
                    elif zp["type"] == "RESTRICTED":
                        restricted_violations += 1

    return {
        "coordinates": coordinates,
        "distance_m": round(total_distance, 1),
        "distance_km": round(total_distance / 1000.0, 2),
        "walking_time_min": walking_time_min,
        "high_risk_distance_m": round(high_risk_distance, 1),
        "safe_distance_m": round(safe_distance, 1),
        "restricted_violations": restricted_violations
    }


def find_nearest_node(G, lat: float, lon: float):
    """
    Find the closest graph node to (lat, lon).
    Uses a vectorized numpy distance calculation, guaranteeing fast execution
    without requiring optional external dependencies like scikit-learn.
    """
    nodes = list(G.nodes)
    if not nodes:
        raise ValueError("Graph has no road nodes available.")
    
    # Extract coordinates array of all nodes in G: shape (N, 2) [lat, lon]
    node_coords = np.array([(G.nodes[n]["y"], G.nodes[n]["x"]) for n in nodes])
    
    # Calculate squared Euclidean distance in degree space (scaled by latitude cos for accuracy)
    lat_scale = np.cos(np.radians(lat))
    d_lat = node_coords[:, 0] - lat
    d_lon = (node_coords[:, 1] - lon) * lat_scale
    sq_distances = d_lat ** 2 + d_lon ** 2
    
    nearest_idx = int(np.argmin(sq_distances))
    return nodes[nearest_idx]


def recommend_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    """
    Calculate the recommended safest route between start and end coordinates.
    Returns route data or raises an explanatory exception.
    """
    # 1. Validate coordinates within B.C. Road operational boundary
    validate_coordinates(start_lat, start_lon, label="Start Location")
    validate_coordinates(end_lat, end_lon, label="Destination")

    # 2. Load road graph and geofencing zones
    G, zones = load_data()

    # 3. Verify start and end are not in restricted zones
    check_restricted_point(start_lat, start_lon, zones, label="Start Location")
    check_restricted_point(end_lat, end_lon, zones, label="Destination")

    # 4. Apply safety weights and eliminate restricted edges
    G_safe = apply_safety_weights(G, zones)

    # 5. Snap to nearest available road nodes
    try:
        origin = find_nearest_node(G_safe, start_lat, start_lon)
        destination = find_nearest_node(G_safe, end_lat, end_lon)
    except Exception as e:
        raise RuntimeError(f"Unable to locate nearest road network nodes: {e}")

    if origin == destination:
        raise ValueError("Start location and Destination resolve to the same road point. Please choose distinct locations.")

    # 6. Calculate safest route avoiding restricted roads and penalizing high-risk areas
    try:
        safe_path = nx.shortest_path(G_safe, source=origin, target=destination, weight="safe_cost")
    except nx.NetworkXNoPath:
        raise RuntimeError(
            "No valid safe route found between these locations. "
            "All possible paths may be blocked by restricted zones or severed road segments."
        )
    except nx.NodeNotFound as e:
        raise RuntimeError(f"Road network node not found: {e}")

    primary_route = extract_route_details(G_safe, safe_path, zones)

    # 7. Calculate alternative route (e.g. shortest by pure length on non-restricted roads)
    alternative_route = None
    try:
        shortest_path = nx.shortest_path(G_safe, source=origin, target=destination, weight="length")
        if shortest_path != safe_path:
            alt_details = extract_route_details(G_safe, shortest_path, zones)
            # Only present if substantially distinct
            if abs(alt_details["distance_m"] - primary_route["distance_m"]) > 5 or alt_details["high_risk_distance_m"] > 0:
                alternative_route = alt_details
    except Exception:
        alternative_route = None

    # Safety advisory evaluation
    warnings = []
    if primary_route["high_risk_distance_m"] > 0:
        warnings.append(
            f"Caution: Approximately {primary_route['high_risk_distance_m']}m of this route passes near or through a High-Risk area because no viable alternate street exists."
        )
    else:
        warnings.append("Great: This recommended route completely avoids all identified High-Risk areas.")

    warnings.append(
        "Safety Notice: While this route avoids restricted zones and prioritizes safe areas based on current geofencing data, "
        "no route is guaranteed to be completely safe under all real-world conditions. Always maintain situational awareness."
    )

    return {
        "status": "ROUTE_FOUND",
        "coordinates": primary_route["coordinates"],
        "distance_m": primary_route["distance_m"],
        "distance_km": primary_route["distance_km"],
        "walking_time_min": primary_route["walking_time_min"],
        "safe_distance_m": primary_route["safe_distance_m"],
        "high_risk_distance_m": primary_route["high_risk_distance_m"],
        "warnings": warnings,
        "alternative_route": alternative_route,
        "origin_node": origin,
        "destination_node": destination
    }


# =====================================================================
# ADMIN ROUTE DESIGNER & MANAGEMENT
# =====================================================================

def haversine_distance(coord1, coord2):
    """Calculate distance in meters between two (lat, lon) coordinates."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def calculate_polyline_distance(coordinates):
    """Calculate total distance in meters along a list of [lat, lon] coordinates."""
    if not coordinates or len(coordinates) < 2:
        return 0.0
    total = 0.0
    for i in range(len(coordinates) - 1):
        total += haversine_distance(coordinates[i], coordinates[i + 1])
    return total


def validate_route_safety(coordinates, zones):
    """
    Validate an arbitrary coordinate path against geofenced zones.
    Returns safety analytics: restricted violations, high-risk exposure, and warnings.
    """
    if not coordinates or len(coordinates) < 2:
        return {
            "is_safe": True,
            "restricted_violations": 0,
            "high_risk_distance_m": 0.0,
            "safe_distance_m": 0.0,
            "warnings": []
        }

    line = LineString([(pt[1], pt[0]) for pt in coordinates])  # LineString takes (lon, lat)
    restricted_violations = 0
    high_risk_distance = 0.0
    safe_distance = 0.0
    warnings = []

    for z in zones:
        try:
            poly = shape(z["geometry"])
            if poly.is_valid and line.intersects(poly):
                z_type = z.get("zone_type", "SAFE")
                z_name = z.get("name", "Zone")
                
                # Approximate distance inside this zone
                intersection = line.intersection(poly)
                # Compute length of intersection
                inter_len = 0.0
                if hasattr(intersection, "geoms"):
                    for g in intersection.geoms:
                        if hasattr(g, "coords"):
                            coords_list = list(g.coords)
                            for i in range(len(coords_list) - 1):
                                inter_len += haversine_distance((coords_list[i][1], coords_list[i][0]), (coords_list[i+1][1], coords_list[i+1][0]))
                elif hasattr(intersection, "coords"):
                    coords_list = list(intersection.coords)
                    for i in range(len(coords_list) - 1):
                        inter_len += haversine_distance((coords_list[i][1], coords_list[i][0]), (coords_list[i+1][1], coords_list[i+1][0]))

                if z_type == "RESTRICTED":
                    restricted_violations += 1
                    warnings.append(f"CRITICAL: Route passes through RESTRICTED zone '{z_name}'. Access is forbidden!")
                elif z_type == "HIGH_RISK":
                    high_risk_distance += inter_len
                    warnings.append(f"Warning: Route traverses ~{round(inter_len, 1)}m of High-Risk Area '{z_name}'.")
                elif z_type == "SAFE":
                    safe_distance += inter_len
        except Exception as e:
            logger.warning(f"Error checking zone intersection: {e}")

    return {
        "is_safe": restricted_violations == 0,
        "restricted_violations": restricted_violations,
        "high_risk_distance_m": round(high_risk_distance, 1),
        "safe_distance_m": round(safe_distance, 1),
        "warnings": warnings
    }


def init_default_designed_routes():
    """Generate default curated routes for B.C. Road if designed_routes.json does not exist."""
    default_routes = []
    try:
        G, zones = load_data()
        G_safe = apply_safety_weights(G, zones)

        # Route 1: B.C. Road Heritage & Town Hall Safe Corridor
        origin = find_nearest_node(G_safe, 12.88175, 75.02991)
        dest1 = find_nearest_node(G_safe, 12.88500, 75.03500)
        path1 = nx.shortest_path(G_safe, origin, dest1, weight="safe_cost")
        details1 = extract_route_details(G_safe, path1, zones)

        default_routes.append({
            "id": "route-corridor-01",
            "name": "B.C. Road Main Town Hall Safe Corridor",
            "category": "SAFE_CORRIDOR",
            "category_label": "Designated Safe Corridor",
            "description": "Primary monitored walking corridor connecting B.C. Road Circle to Bantwal Town Hall along main lit streets.",
            "lighting": "Well Lit (Streetlights Active)",
            "police_patrol": "Regularly Monitored by Bantwal Police",
            "coordinates": details1["coordinates"],
            "waypoints": [
                {"name": "Start: B.C. Road Bus Stand & Circle", "lat": 12.88175, "lon": 75.02991},
                {"name": "End: Bantwal Town Hall", "lat": 12.88500, "lon": 75.03500}
            ],
            "distance_m": details1["distance_m"],
            "distance_km": details1["distance_km"],
            "walking_time_min": details1["walking_time_min"],
            "high_risk_distance_m": details1["high_risk_distance_m"],
            "safe_distance_m": details1["safe_distance_m"],
            "is_active": True,
            "created_at": datetime.now().isoformat()
        })

        # Route 2: Sri Venkataramana Temple Heritage Walk
        dest2 = find_nearest_node(G_safe, 12.89410, 75.03450)
        path2_part1 = nx.shortest_path(G_safe, origin, dest1, weight="safe_cost")
        path2_part2 = nx.shortest_path(G_safe, dest1, dest2, weight="safe_cost")
        combined_nodes = path2_part1 + path2_part2[1:]
        details2 = extract_route_details(G_safe, combined_nodes, zones)

        default_routes.append({
            "id": "route-heritage-02",
            "name": "Sri Venkataramana Temple Heritage Pilgrimage Walk",
            "category": "HERITAGE_WALK",
            "category_label": "Official Tourist Heritage Walk",
            "description": "Curated cultural walking trail from B.C. Road Junction via Town Hall to the historic Sri Venkataramana Temple.",
            "lighting": "Adequate Lighting",
            "police_patrol": "Festival & Daily Patrols",
            "coordinates": details2["coordinates"],
            "waypoints": [
                {"name": "Start: B.C. Road Circle", "lat": 12.88175, "lon": 75.02991},
                {"name": "Checkpoint: Town Hall", "lat": 12.88500, "lon": 75.03500},
                {"name": "End: Sri Venkataramana Temple", "lat": 12.89410, "lon": 75.03450}
            ],
            "distance_m": details2["distance_m"],
            "distance_km": details2["distance_km"],
            "walking_time_min": details2["walking_time_min"],
            "high_risk_distance_m": details2["high_risk_distance_m"],
            "safe_distance_m": details2["safe_distance_m"],
            "is_active": True,
            "created_at": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to generate default designed routes: {e}")

    save_designed_routes(default_routes)
    return default_routes


def load_designed_routes():
    """Load all admin-designed routes from disk."""
    if not DESIGNED_ROUTES_FILE.exists():
        return init_default_designed_routes()

    try:
        with open(DESIGNED_ROUTES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return init_default_designed_routes()
            routes = json.loads(content)
            if not isinstance(routes, list):
                return []
            return routes
    except Exception as e:
        logger.error(f"Error loading designed routes from {DESIGNED_ROUTES_FILE}: {e}")
        return []


def save_designed_routes(routes: list):
    """Save designed routes to designed_routes.json."""
    try:
        with open(DESIGNED_ROUTES_FILE, "w", encoding="utf-8") as f:
            json.dump(routes, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving designed routes to {DESIGNED_ROUTES_FILE}: {e}")
        return False


def design_route_from_waypoints(name: str, category: str, description: str, waypoints: list, lighting: str = "Well Lit", patrol: str = "Regularly Monitored"):
    """
    Design an official route snapped to the road network through a series of waypoints.
    Each waypoint is a dict: {"name": str, "lat": float, "lon": float}.
    """
    if len(waypoints) < 2:
        raise ValueError("At least 2 waypoints (Start and Destination) are required to design a route.")

    # Validate all waypoints within B.C. Road boundary
    for wp in waypoints:
        validate_coordinates(wp["lat"], wp["lon"], label=wp.get("name", "Waypoint"))

    G, zones = load_data()

    # Check waypoints for restricted areas
    for wp in waypoints:
        check_restricted_point(wp["lat"], wp["lon"], zones, label=wp.get("name", "Waypoint"))

    G_safe = apply_safety_weights(G, zones)

    combined_nodes = []
    for i in range(len(waypoints) - 1):
        wp_start = waypoints[i]
        wp_end = waypoints[i + 1]

        u_node = find_nearest_node(G_safe, wp_start["lat"], wp_start["lon"])
        v_node = find_nearest_node(G_safe, wp_end["lat"], wp_end["lon"])

        try:
            sub_path = nx.shortest_path(G_safe, source=u_node, target=v_node, weight="safe_cost")
            if not combined_nodes:
                combined_nodes.extend(sub_path)
            else:
                combined_nodes.extend(sub_path[1:])
        except nx.NetworkXNoPath:
            raise RuntimeError(f"No safe road path connects waypoint '{wp_start.get('name')}' to '{wp_end.get('name')}'.")

    details = extract_route_details(G_safe, combined_nodes, zones)

    category_labels = {
        "SAFE_CORRIDOR": "Designated Safe Corridor",
        "HERITAGE_WALK": "Official Tourist Heritage Walk",
        "PATROL_ROUTE": "Police Monitored Patrol Route",
        "EVACUATION_ROUTE": "Emergency Evacuation Route"
    }

    new_route = {
        "id": str(uuid.uuid4()),
        "name": name.strip(),
        "category": category,
        "category_label": category_labels.get(category, category),
        "description": description.strip(),
        "lighting": lighting,
        "police_patrol": patrol,
        "coordinates": details["coordinates"],
        "waypoints": waypoints,
        "distance_m": details["distance_m"],
        "distance_km": details["distance_km"],
        "walking_time_min": details["walking_time_min"],
        "high_risk_distance_m": details["high_risk_distance_m"],
        "safe_distance_m": details["safe_distance_m"],
        "restricted_violations": details["restricted_violations"],
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }

    routes = load_designed_routes()
    routes.append(new_route)
    save_designed_routes(routes)
    return new_route


def design_route_from_coordinates(name: str, category: str, description: str, coordinates: list, lighting: str = "Well Lit", patrol: str = "Regularly Monitored"):
    """
    Design an official route from freeform drawn coordinates (e.g. from folium polyline draw).
    coordinates: list of [lat, lon].
    """
    if len(coordinates) < 2:
        raise ValueError("A drawn route must have at least 2 coordinate points.")

    for pt in coordinates:
        validate_coordinates(pt[0], pt[1], label="Drawn Route Point")

    _, zones = load_data()
    safety = validate_route_safety(coordinates, zones)
    if safety["restricted_violations"] > 0:
        raise ValueError("Drawn route passes through a RESTRICTED zone! Admin routes must not violate restricted zones.")

    total_dist = round(calculate_polyline_distance(coordinates), 1)
    walking_time = round(total_dist / (AVERAGE_WALKING_SPEED_MPS * 60), 1)

    category_labels = {
        "SAFE_CORRIDOR": "Designated Safe Corridor",
        "HERITAGE_WALK": "Official Tourist Heritage Walk",
        "PATROL_ROUTE": "Police Monitored Patrol Route",
        "EVACUATION_ROUTE": "Emergency Evacuation Route"
    }

    new_route = {
        "id": str(uuid.uuid4()),
        "name": name.strip(),
        "category": category,
        "category_label": category_labels.get(category, category),
        "description": description.strip(),
        "lighting": lighting,
        "police_patrol": patrol,
        "coordinates": coordinates,
        "waypoints": [
            {"name": "Start", "lat": coordinates[0][0], "lon": coordinates[0][1]},
            {"name": "End", "lat": coordinates[-1][0], "lon": coordinates[-1][1]}
        ],
        "distance_m": total_dist,
        "distance_km": round(total_dist / 1000.0, 2),
        "walking_time_min": walking_time,
        "high_risk_distance_m": safety["high_risk_distance_m"],
        "safe_distance_m": safety["safe_distance_m"],
        "restricted_violations": 0,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }

    routes = load_designed_routes()
    routes.append(new_route)
    save_designed_routes(routes)
    return new_route


def delete_designed_route(route_id: str):
    """Delete a designed route by its id."""
    routes = load_designed_routes()
    routes = [r for r in routes if r["id"] != route_id]
    save_designed_routes(routes)
    return routes


def toggle_designed_route_status(route_id: str):
    """Toggle the active status of a designed route."""
    routes = load_designed_routes()
    for r in routes:
        if r["id"] == route_id:
            r["is_active"] = not r.get("is_active", True)
            break
    save_designed_routes(routes)
    return routes


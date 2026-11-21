import json
import importlib
from datetime import datetime
import streamlit as st
import folium
from streamlit_folium import st_folium
from branca.element import Element
from folium.plugins import Draw

import route_engine
# Ensure hot-reloads in Streamlit pick up changes in route_engine without stale cache
importlib.reload(route_engine)

from route_engine import (
    recommend_route,
    load_data,
    load_zones,
    get_zones_path,
    load_designed_routes,
    save_designed_routes,
    design_route_from_waypoints,
    design_route_from_coordinates,
    delete_designed_route,
    toggle_designed_route_status,
    validate_route_safety,
    BC_ROAD_BOUNDS,
    AVERAGE_WALKING_SPEED_MPS
)

# Page configuration
st.set_page_config(
    page_title="Safe Route Recommendation Agent - B.C. Road",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Exact safety zone color specification
ZONE_COLORS = {
    "SAFE": "#2563EB",        # BLUE
    "HIGH_RISK": "#EAB308",   # YELLOW
    "RESTRICTED": "#DC2626"   # RED
}

# Known landmarks / presets strictly within B.C. Road, Bantwal
PRESET_LOCATIONS = {
    "B.C. Road Bus Stand & Circle": (12.88175, 75.02991),
    "Bantwal Railway Station": (12.88720, 75.03850),
    "Sri Venkataramana Temple, Bantwal": (12.89410, 75.03450),
    "Kaikamba Junction, B.C. Road": (12.87650, 75.02520),
    "Bantwal Town Hall / Taluk Office": (12.88500, 75.03500),
    "Custom Coordinates": None
}

ROUTE_CATEGORY_META = {
    "SAFE_CORRIDOR": {"label": "Designated Safe Corridor", "color": "#10B981", "icon": "🔵"},
    "HERITAGE_WALK": {"label": "Official Tourist Heritage Walk", "color": "#059669", "icon": "🟢"},
    "PATROL_ROUTE": {"label": "Police Monitored Patrol Route", "color": "#3B82F6", "icon": "👮"},
    "EVACUATION_ROUTE": {"label": "Emergency Evacuation Route", "color": "#F97316", "icon": "⚠️"}
}


def build_satellite_map(center_lat=12.88175, center_lon=75.02991, zoom=15):
    """Create a Folium map using Esri World Imagery (Satellite) with road/place labels overlay."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles=None,
        control_scale=True
    )

    # 1. High-resolution Satellite Imagery (Default Base Map)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics",
        name="Satellite Imagery",
        overlay=False,
        control=True
    ).add_to(m)

    # 2. Roads, Street Names & Boundaries Overlay on top of Satellite
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Roads & Places Overlay",
        overlay=True,
        control=True
    ).add_to(m)

    # 3. Standard OpenStreetMap layer as alternative
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="OpenStreetMap contributors",
        name="OpenStreetMap View",
        overlay=False,
        control=True
    ).add_to(m)

    return m


def add_zones_to_map(m, zones):
    """Display safety zones on top of the satellite map with exact required colors."""
    zone_group = folium.FeatureGroup(name="Geofenced Safety Zones", show=True)

    for zone in zones:
        zone_type = zone.get("zone_type", "SAFE")
        zone_name = zone.get("name", "Unnamed Zone")
        color = ZONE_COLORS.get(zone_type, "#808080")
        risk_label = {
            "SAFE": "Safe Area (Low Risk)",
            "HIGH_RISK": "High-Risk Area (Avoid/Exercise Caution)",
            "RESTRICTED": "Restricted Area (Strictly Forbidden)"
        }.get(zone_type, zone_type)

        tooltip_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; line-height: 1.4;">
            <strong style="color: {color};">● {zone_name}</strong><br/>
            <span>Type: <b>{zone_type}</b></span><br/>
            <span>Classification: {risk_label}</span>
        </div>
        """

        try:
            folium.GeoJson(
                zone["geometry"],
                style_function=lambda feature, c=color: {
                    "fillColor": c,
                    "color": c,
                    "weight": 2.5,
                    "fillOpacity": 0.38,
                    "dashArray": "4, 4" if c == "#DC2626" else None
                },
                tooltip=folium.Tooltip(tooltip_html, sticky=True)
            ).add_to(zone_group)
        except Exception:
            pass

    zone_group.add_to(m)


def add_floating_legend(m, mode="tourist"):
    """Add a responsive floating visual legend directly onto the Leaflet map."""
    extra_items = ""
    if mode == "admin":
        extra_items = """
        <div style="margin: 3px 0; display: flex; align-items: center;">
            <span style="display:inline-block; width:14px; height:14px; background:#059669; margin-right:8px; border-radius:2px;"></span>
            <span>Admin Designed Route</span>
        </div>
        """

    legend_html = f"""
    <div style="
        position: fixed; 
        bottom: 25px; 
        right: 25px; 
        width: 235px; 
        background: rgba(17, 24, 39, 0.90);
        color: #f9fafb;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 10px 14px;
        font-family: sans-serif;
        font-size: 12px;
        z-index: 9999;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    ">
        <div style="font-weight: bold; margin-bottom: 6px; border-bottom: 1px solid #4b5563; padding-bottom: 4px;">
            🗺️ Map Legend
        </div>
        <div style="margin: 3px 0; display: flex; align-items: center;">
            <span style="display:inline-block; width:14px; height:14px; background:#10B981; margin-right:8px; border-radius:2px;"></span>
            <span>Recommended Safe Route</span>
        </div>
        {extra_items}
        <div style="margin: 3px 0; display: flex; align-items: center;">
            <span style="display:inline-block; width:14px; height:14px; background:#2563EB; margin-right:8px; border-radius:2px;"></span>
            <span>Safe Area</span>
        </div>
        <div style="margin: 3px 0; display: flex; align-items: center;">
            <span style="display:inline-block; width:14px; height:14px; background:#EAB308; margin-right:8px; border-radius:2px;"></span>
            <span>High-Risk Area</span>
        </div>
        <div style="margin: 3px 0; display: flex; align-items: center;">
            <span style="display:inline-block; width:14px; height:14px; background:#DC2626; margin-right:8px; border-radius:2px;"></span>
            <span>Restricted Area</span>
        </div>
        <div style="margin: 3px 0; display: flex; align-items: center;">
            <span style="color: #10B981; font-size: 15px; margin-right: 6px;">📍</span>
            <span>Start / Waypoint</span>
        </div>
        <div style="margin: 3px 0; display: flex; align-items: center;">
            <span style="color: #DC2626; font-size: 15px; margin-right: 6px;">📍</span>
            <span>Destination</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(Element(legend_html))


# ---------------- SIDEBAR NAVIGATION MODE ----------------

st.sidebar.title("🛡️ Safe Route Agent")
app_mode = st.sidebar.radio(
    "Select Operating Mode:",
    ["🚶 Tourist Navigation", "🛠️ Admin Route Designer"],
    index=0
)

# Load safety zones from Geofencing Agent
zones = load_zones()
designed_routes = load_designed_routes()

with st.sidebar.expander("🔗 Geofencing Integration Status", expanded=False):
    zones_path = get_zones_path()
    st.write(f"**Source:** `{zones_path}`")
    if zones_path.exists():
        st.success(f"Connected ({len(zones)} active zones).")
    else:
        st.warning("zones.json not found in companion folder.")
    if st.button("🔄 Refresh Safety Zones"):
        st.rerun()

st.sidebar.markdown(
    f"Active Zones: **{len(zones)}** "
    f"(🔵 {sum(1 for z in zones if z.get('zone_type') == 'SAFE')} Safe | "
    f"🟡 {sum(1 for z in zones if z.get('zone_type') == 'HIGH_RISK')} High-Risk | "
    f"🔴 {sum(1 for z in zones if z.get('zone_type') == 'RESTRICTED')} Restricted)"
)
st.sidebar.markdown(f"Official Designed Routes: **{len(designed_routes)}**")
st.sidebar.markdown("---")


# =====================================================================
# MODE 1: TOURIST NAVIGATION
# =====================================================================

if app_mode == "🚶 Tourist Navigation":

    st.title("🚶 Tourist Safe Route Recommendation")
    st.caption("Territory: **B.C. Road, Bantwal, Dakshina Kannada, Karnataka** | Safety-First Satellite Navigation")

    # Tourist choice: Official Designed Route OR Custom Dynamic Route
    tourist_route_type = st.sidebar.radio(
        "Choose Route Type:",
        ["🌟 Official Admin-Designed Safe Routes", "🔍 Custom Dynamic Route Finder"],
        index=0
    )

    selected_designed_route = None

    if tourist_route_type == "🌟 Official Admin-Designed Safe Routes":
        active_designed = [r for r in designed_routes if r.get("is_active", True)]
        if not active_designed:
            st.sidebar.warning("No active official routes available. Switching to Custom Route Finder.")
            tourist_route_type = "🔍 Custom Dynamic Route Finder"
        else:
            route_options = {r["name"]: r for r in active_designed}
            chosen_name = st.sidebar.selectbox("Select Curated Route:", list(route_options.keys()))
            selected_designed_route = route_options[chosen_name]

            st.sidebar.markdown(f"**Category:** {selected_designed_route.get('category_label', 'Safe Corridor')}")
            st.sidebar.markdown(f"**Lighting:** `{selected_designed_route.get('lighting', 'Well Lit')}`")
            st.sidebar.markdown(f"**Patrol:** `{selected_designed_route.get('police_patrol', 'Monitored')}`")
            st.sidebar.info(selected_designed_route.get("description", ""))

    # If Custom Dynamic Route Finder selected
    start_lat, start_lon = 12.88175, 75.02991
    end_lat, end_lon = 12.88500, 75.03500
    calc_clicked = False

    if tourist_route_type == "🔍 Custom Dynamic Route Finder":
        st.sidebar.subheader("1. Starting Location")
        start_preset = st.sidebar.selectbox(
            "Choose Starting Location:",
            list(PRESET_LOCATIONS.keys()),
            index=0,
            key="tourist_start"
        )
        if start_preset == "Custom Coordinates":
            start_lat = st.sidebar.number_input("Start Latitude", value=12.88175, format="%.6f", key="t_slat")
            start_lon = st.sidebar.number_input("Start Longitude", value=75.02991, format="%.6f", key="t_slon")
        else:
            start_lat, start_lon = PRESET_LOCATIONS[start_preset]
            st.sidebar.info(f"📍 {start_lat:.5f}, {start_lon:.5f}")

        st.sidebar.subheader("2. Destination")
        dest_preset = st.sidebar.selectbox(
            "Choose Destination:",
            list(PRESET_LOCATIONS.keys()),
            index=4,
            key="tourist_dest"
        )
        if dest_preset == "Custom Coordinates":
            end_lat = st.sidebar.number_input("Destination Latitude", value=12.88500, format="%.6f", key="t_elat")
            end_lon = st.sidebar.number_input("Destination Longitude", value=75.03500, format="%.6f", key="t_elon")
        else:
            end_lat, end_lon = PRESET_LOCATIONS[dest_preset]
            st.sidebar.info(f"🎯 {end_lat:.5f}, {end_lon:.5f}")

        calc_clicked = st.sidebar.button("🚀 Find Safest Route", type="primary", use_container_width=True)

    # Route display handling
    route_result = None
    calculation_error = None

    if selected_designed_route:
        route_result = {
            "status": "OFFICIAL_ROUTE",
            "name": selected_designed_route["name"],
            "coordinates": selected_designed_route["coordinates"],
            "distance_m": selected_designed_route["distance_m"],
            "distance_km": selected_designed_route["distance_km"],
            "walking_time_min": selected_designed_route["walking_time_min"],
            "safe_distance_m": selected_designed_route.get("safe_distance_m", 0),
            "high_risk_distance_m": selected_designed_route.get("high_risk_distance_m", 0),
            "waypoints": selected_designed_route.get("waypoints", []),
            "description": selected_designed_route.get("description", ""),
            "lighting": selected_designed_route.get("lighting", ""),
            "police_patrol": selected_designed_route.get("police_patrol", ""),
            "category_label": selected_designed_route.get("category_label", "Safe Route"),
            "warnings": [
                f"Official Route: Certified by B.C. Road safety authorities as '{selected_designed_route.get('category_label')}'.",
                "Safety Notice: While this route avoids restricted zones and prioritizes safe areas, always maintain personal situational awareness."
            ]
        }
    elif calc_clicked or "last_route" in st.session_state:
        if calc_clicked:
            try:
                with st.spinner("Calculating safest road path avoiding restricted zones..."):
                    route_result = recommend_route(start_lat, start_lon, end_lat, end_lon)
                    st.session_state["last_route"] = route_result
            except Exception as e:
                calculation_error = str(e)
                st.session_state.pop("last_route", None)
        else:
            route_result = st.session_state.get("last_route")

    if calculation_error:
        st.error(f"⚠️ **Routing Notice:** {calculation_error}")
        st.info("💡 Ensure coordinates are inside B.C. Road and neither point falls within a red restricted perimeter.")

    # Top metrics when route is ready
    if route_result:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Total Walking Distance", f"{route_result['distance_m']} m", f"{route_result['distance_km']} km")
        with col_m2:
            st.metric("Estimated Walk Time", f"{route_result['walking_time_min']} mins", f"~{AVERAGE_WALKING_SPEED_MPS*3.6:.1f} km/h")
        with col_m3:
            st.metric("Safe Zone Traversal", f"{route_result.get('safe_distance_m', 0)} m", "🔵 Preferred Path")
        with col_m4:
            risk_m = route_result.get("high_risk_distance_m", 0)
            st.metric("High-Risk Exposure", f"{risk_m} m", "Avoided" if risk_m == 0 else "⚠️ Caution", delta_color="inverse")

        # Warnings / Advisory
        for w in route_result.get("warnings", []):
            if "Caution:" in w or "Warning:" in w:
                st.warning(w)
            elif "Great:" in w or "Official Route:" in w:
                st.success(w)
            else:
                st.info(w)

    # Build Map
    if selected_designed_route and selected_designed_route.get("coordinates"):
        c_lat = selected_designed_route["coordinates"][0][0]
        c_lon = selected_designed_route["coordinates"][0][1]
    else:
        c_lat = (start_lat + end_lat) / 2.0
        c_lon = (start_lon + end_lon) / 2.0

    m = build_satellite_map(center_lat=c_lat, center_lon=c_lon, zoom=15)
    add_zones_to_map(m, zones)

    # Draw markers & route
    if route_result and route_result.get("coordinates"):
        # Waypoint / Start / Dest markers
        wps = route_result.get("waypoints")
        if wps:
            for i, wp in enumerate(wps):
                is_first = (i == 0)
                is_last = (i == len(wps) - 1)
                color = "green" if is_first else ("red" if is_last else "blue")
                icon_name = "play" if is_first else ("flag" if is_last else "info-sign")
                folium.Marker(
                    [wp["lat"], wp["lon"]],
                    tooltip=f"<b>{wp.get('name', 'Waypoint')}</b> ({wp['lat']:.5f}, {wp['lon']:.5f})",
                    popup=wp.get("name", "Waypoint"),
                    icon=folium.Icon(color=color, icon=icon_name)
                ).add_to(m)
        else:
            folium.Marker(
                [start_lat, start_lon],
                tooltip=f"<b>Start:</b> ({start_lat:.5f}, {start_lon:.5f})",
                popup="Start Location",
                icon=folium.Icon(color="green", icon="play", prefix="fa")
            ).add_to(m)
            folium.Marker(
                [end_lat, end_lon],
                tooltip=f"<b>Destination:</b> ({end_lat:.5f}, {end_lon:.5f})",
                popup="Destination",
                icon=folium.Icon(color="red", icon="flag", prefix="fa")
            ).add_to(m)

        # Recommended Route in bright green
        folium.PolyLine(
            route_result["coordinates"],
            color="#10B981",
            weight=6,
            opacity=0.9,
            tooltip="Recommended Safest Route"
        ).add_to(m)

        # Alternative route if present
        alt = route_result.get("alternative_route")
        if alt and alt.get("coordinates"):
            folium.PolyLine(
                alt["coordinates"],
                color="#6366F1",
                weight=4,
                opacity=0.7,
                dash_array="6, 8",
                tooltip=f"Alternative Direct Path ({alt['distance_m']}m)"
            ).add_to(m)

    add_floating_legend(m, mode="tourist")
    folium.LayerControl(position="topright").add_to(m)

    st_folium(m, width=None, height=600, use_container_width=True)


# =====================================================================
# MODE 2: ADMIN ROUTE DESIGNER
# =====================================================================

else:
    st.title("🛠️ Admin Route Designer Studio")
    st.caption("Design, calibrate, and publish official tourist routes, safe corridors, and emergency trails for B.C. Road.")

    tab_network, tab_freehand, tab_manage = st.tabs([
        "📍 Method 1: Waypoint Road-Network Designer",
        "✏️ Method 2: Freehand Map Drawing Tool",
        "📋 Route Management & Status"
    ])

    # ---------------- TAB 1: WAYPOINT ROAD NETWORK DESIGNER ----------------
    with tab_network:
        st.subheader("Design Road-Snapped Official Route")
        st.markdown(
            "Specify waypoints along B.C. Road. The engine calculates an optimal road-network path, "
            "verifies that no restricted zones are breached, and evaluates safety attributes."
        )

        col_n1, col_n2 = st.columns(2)
        with col_n1:
            route_name = st.text_input("Route Name", value="B.C. Road Police Safe Passage Corridor", key="adm_name")
            category = st.selectbox(
                "Route Category",
                ["SAFE_CORRIDOR", "HERITAGE_WALK", "PATROL_ROUTE", "EVACUATION_ROUTE"],
                format_func=lambda x: ROUTE_CATEGORY_META[x]["label"]
            )
            route_desc = st.text_area(
                "Route Description & Tourist Advice",
                value="Designated secure walking corridor monitored by police with active streetlights.",
                key="adm_desc"
            )

        with col_n2:
            lighting = st.selectbox(
                "Lighting Status",
                ["Well Lit (Active Streetlights)", "Adequate Lighting", "Daylight Recommended Only"],
                index=0
            )
            patrol = st.selectbox(
                "Police & Security Surveillance",
                ["Regular Police Patrols", "CCTV Monitored Corridor", "Community Safety Watch", "Occasional Patrol"],
                index=0
            )

        st.markdown("#### Waypoint Configuration (Minimum 2)")
        num_waypoints = st.slider("Number of Waypoints / Checkpoints", min_value=2, max_value=5, value=2)

        waypoints_input = []
        for i in range(num_waypoints):
            col_w1, col_w2, col_w3 = st.columns([2, 1, 1])
            with col_w1:
                default_name = "Start: B.C. Road Circle" if i == 0 else ("Destination: Town Hall" if i == num_waypoints - 1 else f"Checkpoint {i}")
                w_name = st.text_input(f"Waypoint {i+1} Name", value=default_name, key=f"wp_name_{i}")
            with col_w2:
                default_lat = 12.88175 if i == 0 else (12.88500 if i == num_waypoints - 1 else 12.88300)
                w_lat = st.number_input(f"Lat {i+1}", value=default_lat, format="%.6f", key=f"wp_lat_{i}")
            with col_w3:
                default_lon = 75.02991 if i == 0 else (75.03500 if i == num_waypoints - 1 else 75.03200)
                w_lon = st.number_input(f"Lon {i+1}", value=default_lon, format="%.6f", key=f"wp_lon_{i}")
            waypoints_input.append({"name": w_name, "lat": w_lat, "lon": w_lon})

        if st.button("🚀 Preview & Validate Designed Route", type="primary"):
            try:
                with st.spinner("Generating road network path and checking geofence zones..."):
                    new_r = design_route_from_waypoints(
                        name=route_name,
                        category=category,
                        description=route_desc,
                        waypoints=waypoints_input,
                        lighting=lighting,
                        patrol=patrol
                    )
                    st.success(f"Route '{new_r['name']}' designed and published successfully! Total Distance: {new_r['distance_m']}m ({new_r['walking_time_min']} mins).")
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to design route: {e}")

    # ---------------- TAB 2: FREEHAND MAP DRAWING TOOL ----------------
    with tab_freehand:
        st.subheader("Freehand Custom Route Drawing")
        st.markdown(
            "Use the **Polyline tool** on the top-left map toolbar to draw a customized route line over the satellite imagery. "
            "Then fill in the details below and click **Save Drawn Route**."
        )

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            draw_route_name = st.text_input("Drawn Route Name", value="B.C. Road Scenic River Path", key="draw_rname")
            draw_category = st.selectbox(
                "Category",
                ["SAFE_CORRIDOR", "HERITAGE_WALK", "PATROL_ROUTE", "EVACUATION_ROUTE"],
                format_func=lambda x: ROUTE_CATEGORY_META[x]["label"],
                key="draw_cat"
            )
        with col_f2:
            draw_lighting = st.selectbox("Lighting Condition", ["Well Lit", "Adequate Lighting", "Daylight Only"], key="draw_light")
            draw_patrol = st.selectbox("Security Status", ["Regular Patrols", "Monitored Area", "Self-Guided"], key="draw_patrol")

        draw_desc = st.text_area("Route Notes", value="Custom curated pathway designed directly on satellite map.", key="draw_desc")

        # Map with Folium Draw Polyline plugin
        m_draw = build_satellite_map(center_lat=12.88175, center_lon=75.02991, zoom=16)
        add_zones_to_map(m_draw, zones)

        draw_plugin = Draw(
            export=False,
            position="topleft",
            draw_options={
                "polyline": {
                    "shapeOptions": {
                        "color": "#10B981",
                        "weight": 5,
                        "opacity": 0.9
                    }
                },
                "polygon": False,
                "circle": False,
                "rectangle": False,
                "marker": True,
                "circlemarker": False
            },
            edit_options={"edit": True, "remove": True}
        )
        draw_plugin.add_to(m_draw)
        add_floating_legend(m_draw, mode="admin")

        draw_map_data = st_folium(
            m_draw,
            width=None,
            height=500,
            use_container_width=True,
            key="admin_draw_map"
        )

        if st.button("💾 Save Drawn Route", type="primary"):
            drawings = draw_map_data.get("all_drawings") if draw_map_data else None
            if not drawings:
                st.error("Please draw a route on the map using the Polyline tool first!")
            else:
                # Find polyline feature
                line_features = [f for f in drawings if f.get("geometry", {}).get("type") == "LineString"]
                if not line_features:
                    st.error("No polyline line drawing found. Please draw a line using the Polyline tool.")
                else:
                    feature = line_features[-1]
                    coords_lon_lat = feature["geometry"]["coordinates"]
                    coords_lat_lon = [[pt[1], pt[0]] for pt in coords_lon_lat]

                    try:
                        saved_r = design_route_from_coordinates(
                            name=draw_route_name,
                            category=draw_category,
                            description=draw_desc,
                            coordinates=coords_lat_lon,
                            lighting=draw_lighting,
                            patrol=draw_patrol
                        )
                        st.success(f"Route '{saved_r['name']}' saved successfully! ({saved_r['distance_m']}m, {saved_r['walking_time_min']} mins).")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Cannot save route: {e}")

    # ---------------- TAB 3: ROUTE MANAGEMENT ----------------
    with tab_manage:
        st.subheader("Manage Published Official Routes")

        if not designed_routes:
            st.info("No designed routes exist yet. Use Tab 1 or Tab 2 to create routes.")
        else:
            for idx, r in enumerate(designed_routes):
                with st.expander(f"{'🟢' if r.get('is_active', True) else '⚪'} {r['name']} ({r.get('distance_m')} m, ~{r.get('walking_time_min')} mins)", expanded=(idx == 0)):
                    col_det1, col_det2 = st.columns([3, 1])
                    with col_det1:
                        st.markdown(f"**Category:** `{r.get('category_label', r.get('category'))}`")
                        st.markdown(f"**Lighting:** `{r.get('lighting')}` | **Patrol:** `{r.get('police_patrol')}`")
                        st.markdown(f"**Description:** {r.get('description')}")
                        st.markdown(f"**Safety Breakdown:** Safe Zone: `{r.get('safe_distance_m', 0)}m` | High-Risk: `{r.get('high_risk_distance_m', 0)}m` | Restricted Violations: `{r.get('restricted_violations', 0)}`")
                        st.caption(f"ID: `{r['id']}` | Created: {r.get('created_at', 'N/A')}")
                    with col_det2:
                        current_status = r.get("is_active", True)
                        status_label = "Deactivate" if current_status else "Activate"
                        if st.button(f"🔄 {status_label}", key=f"tgl_{r['id']}"):
                            toggle_designed_route_status(r["id"])
                            st.rerun()

                        if st.button("🗑️ Delete Route", key=f"del_{r['id']}", type="secondary"):
                            delete_designed_route(r["id"])
                            st.success(f"Deleted route '{r['name']}'.")
                            st.rerun()

# Global Footer
st.markdown("---")
st.caption(
    "Tourist Safety Management System — Safe Route Recommendation Agent | "
    "Calibrated for B.C. Road, Bantwal, Karnataka"
)

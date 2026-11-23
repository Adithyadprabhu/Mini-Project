"""
Module 6: Streamlit Interactive Dashboard
AI-Based Tourist Safety Alert Agent for Atlanta

Displays:
  - Tourist's current location with real-time tracking
  - Historical crime hotspot heatmap (Folium HeatMap)
  - Color-coded safety zones (Safe, High Risk, Very High Risk, Restricted)
  - Active alert notifications with recommended safety actions
  - Machine learning risk prediction confidence & class probabilities
  - Dynamic safe route recommendations with quantitative safety evidence
  - Emergency unit dispatch interface with live ETAs
  - Interactive simulation walkthrough for academic demonstrations
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Add root directory to path to enable agent imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agent.tourist_safety_agent import TouristSafetyAgent
from agent.geofence_integration import GeofenceManager
from agent.safe_route import ATLANTA_SAFE_HAVENS

st.set_page_config(
    page_title="Atlanta Tourist Safety Alert Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- SESSION STATE & INITIALIZATION -----------------

@st.cache_resource
def get_agent():
    """Initializes and caches the master Tourist Safety Agent."""
    return TouristSafetyAgent()

@st.cache_data
def get_historical_hotspots(sample_size=3000):
    """Loads a representative sample of historical crime coordinates for the heatmap."""
    clean_csv = ROOT_DIR / "datasets" / "crime_incidents_clean.csv"
    if clean_csv.exists():
        df = pd.read_csv(
            clean_csv,
            usecols=["latitude", "longitude", "crime_type", "neighborhood"],
            nrows=50000,
        )
        df.dropna(subset=["latitude", "longitude"], inplace=True)
        # Sample for smooth browser rendering
        if len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
        return df[["latitude", "longitude"]].values.tolist()
    return []

agent = get_agent()
hotspot_coords = get_historical_hotspots()

# Preset tourist coordinates for quick demonstration
PRESET_LOCATIONS = {
    "Centennial Olympic Park (Safe Haven)": (33.7603, -84.3931),
    "Georgia Aquarium Plaza (Safe Corridor)": (33.7634, -84.3951),
    "Downtown Commercial Core (High Risk Zone)": (33.7530, -84.3880),
    "Old Fourth Ward (Medium Risk Zone)": (33.7560, -84.3720),
    "Bankhead / Center Hill (Very High Risk Area)": (33.7700, -84.4420),
    "Inman Rail Yard (Restricted Facility)": (33.8000, -84.4360),
    "Midtown Arts District (Safe Corridor)": (33.7895, -84.3850),
}

# Guided walking simulation coordinates
SIMULATION_SCENARIOS = {
    "Downtown Walk -> High Risk -> Safe Reroute": [
        {"name": "Centennial Park Start", "lat": 33.7610, "lon": -84.3920},
        {"name": "Crossing into Marietta St", "lat": 33.7570, "lon": -84.3905},
        {"name": "Entering Downtown High-Theft Zone", "lat": 33.7535, "lon": -84.3885},
        {"name": "Inside High Risk Zone (Suppression Test)", "lat": 33.7525, "lon": -84.3880},
        {"name": "Exiting to Safe Police Haven", "lat": 33.7580, "lon": -84.3910},
    ],
    "Industrial Perimeter -> Restricted Rail Yard Entry": [
        {"name": "Westside Public Road", "lat": 33.7900, "lon": -84.4250},
        {"name": "Approaching Industrial Spur", "lat": 33.7940, "lon": -84.4300},
        {"name": "Crossing Inman Rail Yard Fence (Restricted)", "lat": 33.8000, "lon": -84.4360},
        {"name": "Evacuation to Main Safe Avenue", "lat": 33.7850, "lon": -84.4100},
    ],
}

if "tourist_id" not in st.session_state:
    st.session_state["tourist_id"] = "Tourist-Alpha"

if "sim_scenario" not in st.session_state:
    st.session_state["sim_scenario"] = list(SIMULATION_SCENARIOS.keys())[0]

if "sim_step_idx" not in st.session_state:
    st.session_state["sim_step_idx"] = 0

if "current_lat" not in st.session_state:
    st.session_state["current_lat"] = 33.7603

if "current_lon" not in st.session_state:
    st.session_state["current_lon"] = -84.3931

if "auto_dispatch" not in st.session_state:
    st.session_state["auto_dispatch"] = True

# ----------------- SIDEBAR CONTROLS -----------------

with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield.png", width=64)
    st.title("Tourist Safety Agent")
    st.caption("AI-Powered Real-Time Spatio-Temporal Safety Engine")
    st.markdown("---")

    mode = st.radio("GPS Location Mode", ["Simulated Scenarios", "Preset Landmarks", "Manual GPS Coordinates"])

    if mode == "Simulated Scenarios":
        st.subheader("Interactive Walk Simulation")
        selected_scenario = st.selectbox("Select Scenario", list(SIMULATION_SCENARIOS.keys()))
        scenario_points = SIMULATION_SCENARIOS[selected_scenario]

        step_col1, step_col2, step_col3 = st.columns([1, 1, 1])
        with step_col1:
            if st.button("⏮ Reset"):
                st.session_state["sim_step_idx"] = 0
                st.rerun()
        with step_col2:
            if st.button("▶ Next Step"):
                st.session_state["sim_step_idx"] = (st.session_state["sim_step_idx"] + 1) % len(scenario_points)
                st.rerun()
        with step_col3:
            st.write(f"Step {st.session_state['sim_step_idx'] + 1}/{len(scenario_points)}")

        current_pt = scenario_points[st.session_state["sim_step_idx"]]
        st.session_state["current_lat"] = current_pt["lat"]
        st.session_state["current_lon"] = current_pt["lon"]
        st.info(f"**Waypoint:** {current_pt['name']}\n\n`({current_pt['lat']:.4f}, {current_pt['lon']:.4f})`")

    elif mode == "Preset Landmarks":
        st.subheader("Select Atlanta Landmark")
        chosen_preset = st.selectbox("Landmark", list(PRESET_LOCATIONS.keys()))
        lat, lon = PRESET_LOCATIONS[chosen_preset]
        st.session_state["current_lat"] = lat
        st.session_state["current_lon"] = lon

    else:
        st.subheader("Manual GPS Input")
        st.session_state["current_lat"] = st.number_input(
            "Latitude", value=st.session_state["current_lat"], format="%.6f", min_value=33.60, max_value=33.90
        )
        st.session_state["current_lon"] = st.number_input(
            "Longitude", value=st.session_state["current_lon"], format="%.6f", min_value=-84.58, max_value=-84.26
        )

    st.markdown("---")
    st.subheader("Map Visual Layers")
    show_heatmap = st.checkbox("Show Historical Crime HeatMap", value=True)
    show_zones = st.checkbox("Show Geofenced Zones", value=True)
    show_safe_havens = st.checkbox("Show Verified Safe Havens", value=True)
    show_emergency_units = st.checkbox("Show Emergency Response Stations", value=True)
    show_safe_route = st.checkbox("Show Recommended Evasive Route", value=True)

    st.markdown("---")
    st.subheader("Emergency Control")
    st.session_state["auto_dispatch"] = st.checkbox(
        "Auto-Dispatch on Very High / Restricted", value=st.session_state["auto_dispatch"]
    )
    if st.button("🚨 TRIGGER EMERGENCY SOS", type="primary", use_container_width=True):
        sos_res = agent.trigger_sos(
            st.session_state["tourist_id"],
            st.session_state["current_lat"],
            st.session_state["current_lon"],
        )
        st.success("🚨 Emergency SOS Transmitted to Regional Dispatch!")
        st.rerun()

# ----------------- AGENT PROCESSING -----------------

tracking_result = agent.monitor_tourist(
    tourist_id=st.session_state["tourist_id"],
    latitude=st.session_state["current_lat"],
    longitude=st.session_state["current_lon"],
    auto_dispatch_emergency=st.session_state["auto_dispatch"],
)

current_risk = tracking_result["effective_risk_level"]
zone_name = tracking_result["effective_zone_name"]
zone_type = tracking_result["effective_zone_type"]
transition_event = tracking_result["geofence_status"]["event_type"]
active_alert = tracking_result["active_alert"]
safe_route = tracking_result["safe_route_recommendation"]
emergency_dispatch = tracking_result["emergency_dispatch"]
ml_pred = tracking_result["ml_risk_prediction"]

# ----------------- HEADER & STATUS BAR -----------------

st.title("🛡️ AI Tourist Safety Alert Agent — Atlanta Metro")
st.caption(
    "Integrated Multi-Agent Tourist Protection System | Geofencing • Crime Risk ML • "
    "Alert Engine • Safe Route Recommendation • Emergency Services Dispatch"
)

# Color badge mapping
BADGE_COLORS = {
    "LOW": ("#10B981", "✅ LOW RISK — SAFE AREA"),
    "MEDIUM": ("#F59E0B", "⚠️ MEDIUM RISK — CAUTION"),
    "HIGH": ("#EF4444", "🚨 HIGH RISK — SAFETY WARNING"),
    "VERY_HIGH": ("#B91C1C", "⚡ VERY HIGH RISK — URGENT WARNING"),
    "RESTRICTED": ("#7F1D1D", "⛔ RESTRICTED AREA — ACCESS FORBIDDEN"),
}

badge_color, badge_text = BADGE_COLORS.get(current_risk, ("#6B7280", current_risk))

stat_col1, stat_col2, stat_col3, stat_col4 = st.columns([2.5, 2.5, 2, 2])
with stat_col1:
    st.markdown(
        f"<div style='background-color:{badge_color}; color:white; padding:10px 14px; border-radius:8px; font-weight:bold;'>"
        f"{badge_text}</div>",
        unsafe_allow_html=True,
    )
with stat_col2:
    st.metric("Current Location Zone", zone_name)
with stat_col3:
    st.metric("Geofence Event", transition_event)
with stat_col4:
    st.metric("ML Model Confidence", f"{ml_pred.get('confidence', 0.0) * 100:.1f}%")

# Active Alert Notification Banner
if active_alert:
    alert_box_color = badge_color
    st.markdown(
        f"""
        <div style="background-color: rgba(255, 255, 255, 0.05); border-left: 6px solid {alert_box_color}; padding: 14px 18px; margin: 12px 0; border-radius: 6px;">
            <h4 style="margin: 0; color: {alert_box_color};">{active_alert['alert_type'].replace('_', ' ')}</h4>
            <p style="margin: 6px 0; font-size: 15px;"><b>Message:</b> {active_alert['message']}</p>
            <p style="margin: 4px 0; font-size: 14px; color: #9CA3AF;"><b>Recommended Action:</b> {active_alert['recommended_action']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif transition_event == "INSIDE_UNCHANGED":
    st.info(f"ℹ️ Tourist remains inside '{zone_name}'. Repeated alert notification suppressed to prevent spam.")

# ----------------- MAP & VISUALIZATION -----------------

main_col, side_col = st.columns([3, 2])

with main_col:
    st.subheader("🗺️ Live Geofencing & Safety Map")

    # Initialize Folium Map
    m = folium.Map(
        location=[st.session_state["current_lat"], st.session_state["current_lon"]],
        zoom_start=14,
        tiles="CartoDB positron",
    )

    # 1. Historical Crime Heatmap Layer
    if show_heatmap and hotspot_coords:
        HeatMap(
            hotspot_coords,
            radius=12,
            blur=15,
            max_zoom=16,
            name="Crime Density HeatMap",
        ).add_to(m)

    # 2. Geofenced Safety Zones
    if show_zones:
        ZONE_STYLE_COLORS = {
            "SAFE": "#2563EB",         # Blue
            "HIGH_RISK": "#EAB308",    # Yellow/Orange
            "VERY_HIGH": "#DC2626",    # Red
            "RESTRICTED": "#450A0A",   # Dark Maroon
        }

        for z in agent.geofence_manager.zones:
            z_type = z.get("zone_type", "SAFE")
            z_risk = z.get("risk_level", "LOW")
            name = z.get("name", "Zone")
            color = ZONE_STYLE_COLORS.get(z_type, "#2563EB")
            if z_risk == "VERY_HIGH":
                color = "#DC2626"

            coords = z.get("geometry", {}).get("coordinates", [])
            if coords and len(coords[0]) > 2:
                # GeoJSON coordinates are [lon, lat], folium expects [lat, lon]
                poly_pts = [[pt[1], pt[0]] for pt in coords[0]]
                folium.Polygon(
                    locations=poly_pts,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.32,
                    weight=2.5,
                    popup=folium.Popup(f"<b>{name}</b><br>Type: {z_type}<br>Risk: {z_risk}", max_width=250),
                    tooltip=f"{name} ({z_type} - {z_risk})",
                ).add_to(m)

    # 3. Verified Safe Havens Markers
    if show_safe_havens:
        for haven in ATLANTA_SAFE_HAVENS:
            folium.Marker(
                location=[haven["latitude"], haven["longitude"]],
                icon=folium.Icon(color="green", icon="shield", prefix="fa"),
                tooltip=f"Verified Safe Haven: {haven['name']}",
                popup=folium.Popup(
                    f"<b>{haven['name']}</b><br>{haven['description']}<br><i>Security: {haven['security']}</i>",
                    max_width=280,
                ),
            ).add_to(m)

    # 4. Emergency Response Units
    if show_emergency_units:
        for unit in agent.emergency_dispatcher.units:
            status = unit.get("status", "AVAILABLE")
            u_color = "blue" if status == "AVAILABLE" else ("orange" if status == "ON_PATROL" else "red")
            folium.Marker(
                location=[unit["latitude"], unit["longitude"]],
                icon=folium.Icon(color=u_color, icon="ambulance" if unit["unit_type"] == "MEDICAL" else "bullhorn", prefix="fa"),
                tooltip=f"Emergency Unit: {unit['unit_id']} ({status})",
                popup=folium.Popup(
                    f"<b>{unit['unit_id']}</b><br>{unit['station_name']}<br>Status: <b>{status}</b><br>Radio: {unit['contact_radio']}",
                    max_width=260,
                ),
            ).add_to(m)

    # 5. Recommended Safe Route Polyline
    if show_safe_route and safe_route:
        route_coords = safe_route.get("coordinates", [])
        if route_coords:
            folium.PolyLine(
                locations=route_coords,
                color="#059669",
                weight=5,
                opacity=0.9,
                dash_array="8, 6",
                tooltip=f"Recommended Safe Route to {safe_route['destination']['name']}",
            ).add_to(m)

            # Destination Marker
            dest = safe_route["destination"]
            folium.Marker(
                location=[dest["latitude"], dest["longitude"]],
                icon=folium.Icon(color="darkgreen", icon="flag-checkered", prefix="fa"),
                tooltip=f"Safe Destination: {dest['name']}",
            ).add_to(m)

    # 6. Tourist Current Location Marker (Pulsing Red/Green Marker)
    folium.Marker(
        location=[st.session_state["current_lat"], st.session_state["current_lon"]],
        icon=folium.Icon(color="red" if current_risk in ["HIGH", "VERY_HIGH", "RESTRICTED"] else "blue", icon="user", prefix="fa"),
        tooltip=f"Tourist Location ({st.session_state['current_lat']:.4f}, {st.session_state['current_lon']:.4f})",
        popup=folium.Popup(f"<b>Current Tourist Position</b><br>Zone: {zone_name}<br>Assessed Risk: {current_risk}", max_width=250),
    ).add_to(m)

    st_folium(m, width="100%", height=560, key=f"map_{st.session_state['current_lat']}_{st.session_state['current_lon']}")

with side_col:
    # ----------------- ML RISK PREDICTION BREAKDOWN -----------------
    st.subheader("📊 Spatio-Temporal ML Risk Engine")
    
    st.write(f"**Target Prediction:** `{ml_pred['risk_level']}`")
    st.write(f"**Confidence:** `{ml_pred['confidence'] * 100:.1f}%`")

    # Bar chart of class probabilities
    probs = ml_pred.get("probabilities", {})
    if probs:
        prob_df = pd.DataFrame(list(probs.items()), columns=["Risk Level", "Probability"])
        st.bar_chart(prob_df.set_index("Risk Level"), height=180)

    # ----------------- SAFE ROUTE RECOMMENDATION -----------------
    st.markdown("---")
    st.subheader("🚶 Safe Route & Evasive Guidance")
    
    if safe_route:
        dest = safe_route["destination"]
        st.success(f"📍 **Recommended Haven:** {dest['name']}")
        st.write(f"ℹ️ {dest.get('description', '')}")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Distance", f"{safe_route['total_distance_m']} m")
        with c2:
            st.metric("Walking Time", f"{safe_route['estimated_walking_time_min']} min")
        with c3:
            st.metric("Safety Score", f"{safe_route['safety_score_pct']}%")

        st.caption("🛡️ **Safety Verification & Evidence:**")
        for ev in safe_route.get("warnings_and_evidence", []):
            st.markdown(f"- {ev}")
    else:
        st.info("Tourist is in a low-risk zone. No evasive reroute required.")

    # ----------------- EMERGENCY SERVICES STATUS -----------------
    st.markdown("---")
    st.subheader("🚑 Emergency Response Interface")
    
    if emergency_dispatch and emergency_dispatch.get("dispatch_success"):
        st.error(f"🚨 **ACTIVE EMERGENCY DISPATCH:** Unit `{emergency_dispatch['dispatched_unit']['unit_id']}`")
        u = emergency_dispatch["dispatched_unit"]
        st.write(f"**Station:** {u['station_name']}")
        st.write(f"**ETA:** `{u['eta_minutes']} mins` | **Distance:** `{u['distance_km']} km`")
        st.write(f"**Radio Channel:** `{u['contact_radio']}`")
        st.caption(f"Incident ID: `{emergency_dispatch['incident_id']}` | Assigned to Response Agent")
    else:
        st.write("Regional public safety units on standby:")
        nearby = tracking_result.get("nearby_emergency_units", [])
        for u in nearby[:2]:
            st.markdown(
                f"- **{u['unit_id']}** ({u['station_name']}): `{u['distance_km']} km`, ETA ~`{u['eta_minutes']} min` [`{u['status']}`]"
            )

# ----------------- FOOTER / DEMONSTRATION LOG -----------------
st.markdown("---")
with st.expander("📝 View Real-Time Alert Event Log & Telemetry", expanded=False):
    if agent.alert_log:
        st.dataframe(pd.DataFrame(agent.alert_log).tail(10), use_container_width=True)
    else:
        st.write("No alerts recorded in this session.")

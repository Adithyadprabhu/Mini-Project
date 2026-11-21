import json
import uuid
import streamlit as st
import folium
from shapely.geometry import shape

from streamlit_folium import st_folium
from folium.plugins import Draw

from geofence import check_location

st.set_page_config(
    page_title="Tourist Geofencing Agent",
    layout="wide"
)

ZONES_FILE = "zones.json"


def load_zones():
    try:
        with open(ZONES_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_zones(zones):
    with open(ZONES_FILE, "w") as f:
        json.dump(zones, f, indent=4)


zones = load_zones()

st.title("Tourist Safety - Geofencing Agent")
st.write("Admin panel for managing safety zones.")

# ---------------- ADMIN SIDEBAR ----------------

st.sidebar.header("Admin Area Management")

zone_name = st.sidebar.text_input("Area Name", key=f"zone_name_{len(zones)}")

zone_type = st.sidebar.selectbox(
    "Area Type",
    ["SAFE", "HIGH_RISK", "RESTRICTED"],
    format_func=lambda x: {
        "SAFE": "🔵 SAFE (Low Risk)",
        "HIGH_RISK": "🟡 HIGH_RISK (Medium Risk)",
        "RESTRICTED": "🔴 RESTRICTED (High Risk)"
    }.get(x, x)
)

# Suggest corresponding default risk level based on area type
default_risk_index = {"SAFE": 0, "HIGH_RISK": 1, "RESTRICTED": 2}.get(zone_type, 0)

risk_level = st.sidebar.selectbox(
    "Risk Level",
    ["LOW", "MEDIUM", "HIGH"],
    index=default_risk_index
)

# Colors for zones
ZONE_COLORS = {
    "SAFE": "#2563EB",        # BLUE
    "HIGH_RISK": "#EAB308",   # YELLOW
    "RESTRICTED": "#DC2626"   # RED
}

active_draw_color = ZONE_COLORS.get(zone_type, "#2563EB")

show_saved_zones = st.sidebar.checkbox("Show Saved Zones on Map", value=True)

st.sidebar.info(
    f"Active drawing color: **{zone_type}** ({active_draw_color})\n\n"
    "Draw a polygon on the map, then click **Save Drawn Area**."
)

# ---------------- MAP ----------------

m = folium.Map(
    location=[12.88175, 75.02991],
    zoom_start=17,
    tiles=None
)

# Satellite imagery
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri, Maxar, Earthstar Geographics",
    name="Satellite View",
    overlay=False,
    control=True
).add_to(m)

# Road labels over satellite imagery
folium.TileLayer(
    tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
    name="Roads and Place Labels",
    overlay=True,
    control=True
).add_to(m)

folium.LayerControl().add_to(m)

legend_html = """
<div style="
position: fixed;
bottom: 25px;
left: 25px;
width: 200px;
background: rgba(255, 255, 255, 0.95);
padding: 12px 14px;
border: 2px solid #6b7280;
border-radius: 8px;
z-index: 9999;
color: #111827;
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
font-size: 13px;
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
">
<b style="font-size: 14px; color: #111827;">Safety Zones Legend</b><br><br>
<span style="color:#2563EB; font-size: 16px;">●</span> <b>Safe Area</b> (Blue)<br>
<span style="color:#EAB308; font-size: 16px;">●</span> <b>High-Risk Area</b> (Yellow)<br>
<span style="color:#DC2626; font-size: 16px;">●</span> <b>Restricted Area</b> (Red)
</div>
"""

m.get_root().html.add_child(
    folium.Element(legend_html)
)

def get_zone_color(z):
    z_type = str(z.get("zone_type", "")).strip().upper().replace(" ", "_")
    r_level = str(z.get("risk_level", "")).strip().upper()

    if z_type == "RESTRICTED":
        return "#DC2626"  # Red
    elif z_type == "HIGH_RISK":
        return "#EAB308"  # Yellow
    elif z_type == "SAFE":
        return "#2563EB"  # Blue
    
    # Fallback based on risk level if zone_type is not recognized
    if r_level == "HIGH":
        return "#DC2626"
    elif r_level == "MEDIUM":
        return "#EAB308"
    return "#2563EB"

# Display saved zones cleanly as folium.Polygon
# Using folium.Polygon completely avoids streamlit-folium's GeoJson naming bugs
# and interactive=False ensures mouse clicks pass straight through to Draw
if show_saved_zones:
    for zone in zones:
        color = get_zone_color(zone)
        geom = zone.get("geometry", {})
        coords = geom.get("coordinates", [])

        if geom.get("type") == "Polygon" and coords:
            # GeoJSON coordinates are [lon, lat], folium.Polygon expects [lat, lon]
            locations = [[pt[1], pt[0]] for pt in coords[0]]
            folium.Polygon(
                locations=locations,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.35,
                weight=3,
                interactive=False
            ).add_to(m)
        elif geom.get("type") == "MultiPolygon" and coords:
            for poly in coords:
                locations = [[pt[1], pt[0]] for pt in poly[0]]
                folium.Polygon(
                    locations=locations,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.35,
                    weight=3,
                    interactive=False
                ).add_to(m)

# Drawing tool for admin with active color matching the selected Area Type
draw = Draw(
    export=False,
    draw_options={
        "polyline": False,
        "polygon": {
            "shapeOptions": {
                "color": active_draw_color,
                "fillColor": active_draw_color,
                "fillOpacity": 0.40,
                "weight": 3
            }
        },
        "rectangle": {
            "shapeOptions": {
                "color": active_draw_color,
                "fillColor": active_draw_color,
                "fillOpacity": 0.40,
                "weight": 3
            }
        },
        "circle": False,
        "marker": False,
        "circlemarker": False
    },
    edit_options={
        "edit": True,
        "remove": True
    }
)

draw.add_to(m)

map_data = st_folium(
    m,
    width=1100,
    height=600,
    key=f"admin_map_{len(zones)}"
)

# ---------------- SAVE NEW AREA ----------------

st.subheader("Create New Safety Zone")

if st.button("Save Drawn Area"):

    drawings = map_data.get("all_drawings") if map_data else None

    if not zone_name.strip():
        st.error("Please enter an Area Name in the sidebar first.")

    elif not drawings:
        st.error("Please draw an area on the map first using the polygon or rectangle tool.")

    else:
        feature = drawings[-1]

        new_zone = {
            "id": str(uuid.uuid4()),
            "name": zone_name.strip(),
            "risk_level": risk_level,
            "zone_type": zone_type,
            "geometry": feature["geometry"]
        }

        zones.append(new_zone)
        save_zones(zones)

        st.success(f"Area '{new_zone['name']}' saved successfully! You can now draw your next area.")
        st.rerun()

# ---------------- EDIT AREA DETAILS ----------------

st.subheader("Manage Existing Areas")

if "editing_zone_id" not in st.session_state:
    st.session_state["editing_zone_id"] = None

if zones:
    st.caption("All created places are listed below. Click **Edit** on any location to modify or delete it.")

    # Table header
    h_col1, h_col2, h_col3, h_col4 = st.columns([3, 2.5, 2, 1.5])
    with h_col1:
        st.markdown("**Location Name**")
    with h_col2:
        st.markdown("**Area Type**")
    with h_col3:
        st.markdown("**Risk Level**")
    with h_col4:
        st.markdown("**Action**")

    st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)

    # List all places
    for z in zones:
        # Ensure zone has an id
        if "id" not in z or not z["id"]:
            z["id"] = str(uuid.uuid4())

        col1, col2, col3, col4 = st.columns([3, 2.5, 2, 1.5])

        with col1:
            st.write(f"📍 **{z['name']}**")

        with col2:
            type_label = {
                "SAFE": "🔵 Safe Area",
                "HIGH_RISK": "🟡 High-Risk",
                "RESTRICTED": "🔴 Restricted"
            }.get(z.get("zone_type", ""), z.get("zone_type", ""))
            st.write(type_label)

        with col3:
            st.write(f"`{z.get('risk_level', 'LOW')}`")

        with col4:
            is_currently_editing = (st.session_state["editing_zone_id"] == z["id"])
            btn_label = "Editing..." if is_currently_editing else "✏️ Edit"
            if st.button(btn_label, key=f"btn_edit_{z['id']}"):
                st.session_state["editing_zone_id"] = z["id"]
                st.rerun()

    # Edit section appears ONLY after clicking a specific location
    if st.session_state["editing_zone_id"]:
        selected_zone = next((z for z in zones if z["id"] == st.session_state["editing_zone_id"]), None)

        if selected_zone:
            st.markdown("---")
            st.markdown(f"#### ✏️ Edit Location: `{selected_zone['name']}`")

            with st.container():
                edit_name = st.text_input(
                    "Update Location Name",
                    value=selected_zone["name"],
                    key=f"edit_name_{selected_zone['id']}"
                )

                edit_type = st.selectbox(
                    "Update Area Type",
                    ["SAFE", "HIGH_RISK", "RESTRICTED"],
                    index=["SAFE", "HIGH_RISK", "RESTRICTED"].index(selected_zone.get("zone_type", "SAFE")),
                    format_func=lambda x: {
                        "SAFE": "🔵 SAFE (Low Risk)",
                        "HIGH_RISK": "🟡 HIGH_RISK (Medium Risk)",
                        "RESTRICTED": "🔴 RESTRICTED (High Risk)"
                    }.get(x, x),
                    key=f"edit_type_{selected_zone['id']}"
                )

                edit_risk = st.selectbox(
                    "Update Risk Level",
                    ["LOW", "MEDIUM", "HIGH"],
                    index=["LOW", "MEDIUM", "HIGH"].index(selected_zone.get("risk_level", "LOW")),
                    key=f"edit_risk_{selected_zone['id']}"
                )

                btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 2])

                with btn_col1:
                    if st.button("💾 Save Changes", key=f"save_btn_{selected_zone['id']}"):
                        if edit_name.strip():
                            selected_zone["name"] = edit_name.strip()
                        selected_zone["zone_type"] = edit_type
                        selected_zone["risk_level"] = edit_risk
                        save_zones(zones)
                        st.session_state["editing_zone_id"] = None
                        st.success("Area updated successfully!")
                        st.rerun()

                with btn_col2:
                    if st.button("🗑️ Delete Location", key=f"delete_btn_{selected_zone['id']}"):
                        zones.remove(selected_zone)
                        save_zones(zones)
                        st.session_state["editing_zone_id"] = None
                        st.success("Area deleted!")
                        st.rerun()

                with btn_col3:
                    if st.button("✖ Cancel", key=f"cancel_btn_{selected_zone['id']}"):
                        st.session_state["editing_zone_id"] = None
                        st.rerun()
        else:
            st.session_state["editing_zone_id"] = None

else:
    st.info("No areas created yet. Use the drawing tool above to add your first area.")

# ---------------- TEST TOURIST LOCATION ----------------

st.subheader("Test Tourist GPS Location")

latitude = st.number_input(
    "Tourist Latitude",
    value=12.881750,
    format="%.6f"
)

longitude = st.number_input(
    "Tourist Longitude",
    value=75.029910,
    format="%.6f"
)

if st.button("Check Tourist Location"):

    result = check_location(
        latitude,
        longitude,
        zones
    )

    if result["inside"]:
        st.warning(
            f"⚠️ {result['message']} | "
            f"Risk: {result['risk_level']} | "
            f"Type: {result['zone_type']}"
        )
    else:
        st.success(result["message"])
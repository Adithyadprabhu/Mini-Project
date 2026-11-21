# 🛡️ Safe Route Recommendation Agent

**Tourist Safety Management System (Mini-Project)**  
**Target Territory:** B.C. Road, Bantwal, Dakshina Kannada, Karnataka, India

---

## 📌 Project Overview
The **Safe Route Recommendation Agent** is an intelligent pedestrian navigation system engineered specifically for tourists visiting B.C. Road, Bantwal. Integrating seamlessly with the **Geofencing Agent**, this agent dynamically assesses road network safety, completely excises restricted zones, penalizes high-risk paths, and directs tourists along safe and monitored corridors over high-resolution satellite imagery.

---

## 🎯 Key Capabilities
1. **B.C. Road Bounded Navigation:**
   - Calibrated exclusively for B.C. Road, Bantwal (`Lat: 12.8500 – 12.9150`, `Lon: 75.0000 – 75.0600`).
   - Coordinate validation and bounding box enforcement prevent erroneous or unrelated queries.

2. **Satellite-First GIS Mapping:**
   - High-resolution Esri World Imagery as the default base layer.
   - Roads, buildings, and place label overlays for clear landmark recognition.
   - Smooth panning, zooming, and layer control toggling.

3. **Geofencing Integration:**
   - Automatically detects and reads `zones.json` from the companion `Geo-Fancing` / `Geofencing_Agent` directory.
   - Dynamic real-time reload without restart using the in-app refresh control.
   - Zero duplication or alteration of existing Geofencing data.

4. **Exact Standardized Safety Color Schema:**
   - 🔵 **Safe Area:** `#2563EB` (Blue) — Promoted path segments with safety weight bonuses.
   - 🟡 **High-Risk Area:** `#EAB308` (Yellow) — Penalized segments avoided unless no alternate road exists.
   - 🔴 **Restricted Area:** `#DC2626` (Red) — Severed from the routing graph. Access is strictly forbidden.
   - 🟢 **Recommended Route:** `#10B981` (Green) — Displayed prominently with green start marker and red destination marker.

5. **Safety-Weighted Routing Engine:**
   - OpenStreetMap walking road network extracted via **OSMnx** (`bc_road_walk.graphml`).
   - Shortest path calculations performed using **NetworkX** with weighted cost functions (`safe_cost`).
   - Vectorized node proximity mapping (pure NumPy fallback ensures zero dependency breaks).
   - Walking distance (meters/km) and estimated travel time (~4.8 km/h pedestrian model).
   - Transparent safety warnings and disclaimer (no route is ever claimed to be 100% safe).

6. **Admin Route Designer Studio:**
   - **Method 1 (Waypoint-Guided Snapping):** Define checkpoints/waypoints across B.C. Road; engine snaps paths strictly to safe road segments, verifies 0 restricted area violations, and evaluates lighting & police surveillance.
   - **Method 2 (Interactive Freehand Polyline Drawing):** Draw custom paths directly over high-res satellite imagery using Folium Draw; system checks intersections with active geofenced safety zones and calculates geodesic distance.
   - **Route Lifecycle Management:** Activate, de-activate, or delete published official routes, making them instantly accessible to tourists.

---

## 📂 Project Structure
```text
Safe Route Recommendation Agent/
│── app.py                 # Streamlit web application (Tourist Navigation + Admin Route Designer)
│── route_engine.py        # Safety-weighted routing engine, geofencing & route designer
│── download_roads.py      # Script to download OSM walking network for B.C. Road
│── requirements.txt       # Project Python dependencies
│── README.md              # Project documentation and user guide
│── bc_road_walk.graphml   # Pre-downloaded road graph for B.C. Road, Bantwal
│── designed_routes.json   # Persistent store for admin-designed official routes
│── test_agent.py          # 10-point comprehensive automated test suite
└── cache/                 # Cache folder for OSMnx data
```

---

## 🚀 Installation & Running

### 1. Activate Virtual Environment
```powershell
# In Windows PowerShell:
.\venv\Scripts\Activate.ps1
```

### 2. Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start the Application
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Testing Checklist & Verification
- **Syntax & Indentation:** Validated and compiled error-free (`py_compile`).
- **Satellite Map Rendering:** Esri World Imagery with boundary overlays loads at B.C. Road center `(12.88175, 75.02991)`.
- **Geofence Zone Loading:** Active safety zones read directly from `Geo-Fancing/zones.json`.
- **Restricted Zone Avoidance:** Tested with coordinates inside or intersecting restricted perimeters.
- **High-Risk Zone Avoidance:** Confirmed routing algorithm diverts around yellow zones.
- **Boundary Validation:** Tested with out-of-bounds coordinates (graceful validation message).
- **Travel Time & Distance:** Accurately calculated and presented on interface metric cards.

# AI-Based Tourist Safety Alert Agent for Atlanta

An intelligent, multi-agent tourist safety system for Atlanta, Georgia. The agent continuously monitors tourist GPS locations, evaluates spatial danger zones and ambient crime risk using machine learning, detects entry/exit transitions, suppresses repetitive alerts, recommends safe evasive routes, and dispatches emergency response units.

---

## 1. Architecture Overview

```
                                      +------------------------------------+
                                      |   Tourist GPS Stream / Simulator   |
                                      +-----------------+------------------+
                                                        |
                                                        v
                                      +------------------------------------+
                                      |      Tourist Safety Agent          |
                                      +--------+-------------------+-------+
                                               |                   |
                     +-------------------------+                   +-------------------------+
                     v                                                                       v
     +-------------------------------+                                       +-------------------------------+
     |  Module 3: Geofencing Engine  |                                       | Module 2: Spatio-Temporal ML  |
     |  (Integrates Existing Agent)  |                                       | (Random Forest Classifier)    |
     +---------------+---------------+                                       +---------------+---------------+
                     |                                                                       |
                     +-------------------------+                   +-------------------------+
                                               v                   v
                                      +------------------------------------+
                                      |   Stateful Location Tracker        |
                                      |   (ENTRY / EXIT / SUPPRESSION)     |
                                      +-----------------+------------------+
                                                        |
                                                        v
                                      +------------------------------------+
                                      | Module 4: Alert Generation Engine  |
                                      | (Low, Medium, High, V.High, Restr) |
                                      +--------+-------------------+-------+
                                               |                   |
                     +-------------------------+                   +-------------------------+
                     v                                                                       v
     +-------------------------------+                                       +-------------------------------+
     | Module 5: Safe Route Engine   |                                       | Module 7: Emergency Dispatch  |
     | (Avoids Hazards / Safe Havens)|                                       | (Interface for Response Agent)|
     +-------------------------------+                                       +-------------------------------+
                                               |                   |
                                               v                   v
                                      +------------------------------------+
                                      | Module 6: Streamlit Folium UI Map  |
                                      +------------------------------------+
```

---

## 2. Directory Structure

```
Tuorist Safety Alert Agent/
├── datasets/
│   ├── atlcrime.csv                            # Historical Atlanta crime records (2009-2017)
│   ├── crime reports.csv                       # Detailed crime incident reports
│   ├── crime_incidents_clean.csv               # 290k canonical deduplicated incidents with coordinates
│   ├── crime_daily_counts.csv                  # Aggregated daily crime totals
│   ├── weather_daily_clean.csv                 # Daily weather data (2021-current)
│   ├── weather_hourly_clean.csv                # Hourly weather data (2021-current)
│   ├── daily_combined_timeline.csv             # Combined coverage panel
│   ├── atl_neighborhoods.* (shp, dbf, prj...) # Official Atlanta neighborhood boundary shapefiles
│   └── atlanta_safety_zones.json               # Geofenced Safe, High-Risk, and Restricted zones
├── models/
│   ├── crime_risk_model.joblib                 # Trained Random Forest Classifier
│   └── model_metrics.json                      # Accuracy, F1, precision, confusion matrix
├── agent/
│   ├── __init__.py                             # Agent package exports
│   ├── crime_data_processor.py                 # Module 1: Cleans, deduplicates, spatial-temporal features
│   ├── crime_risk_predictor.py                 # Module 2: Supervised ML risk classifier (4 levels)
│   ├── geofence_integration.py                 # Module 3: Existing Geofencing Agent integration & state tracker
│   ├── alert_engine.py                         # Module 4: Contextual safety alert engine
│   ├── safe_route.py                           # Module 5: Evasive route planner & safe havens catalog
│   ├── emergency_integration.py                # Module 7: Real Atlanta emergency units registry & dispatch
│   └── tourist_safety_agent.py                 # Master orchestrator agent
├── dashboard/
│   └── app.py                                  # Module 6: Streamlit + Folium interactive dashboard
├── tests/
│   ├── __init__.py
│   ├── test_geofence.py                        # Tests point-in-polygon, entry, exit, alert suppression
│   ├── test_alert_engine.py                    # Tests all 5 alert levels & schema compliance
│   ├── test_safe_route.py                      # Tests route metrics and obstacle avoidance
│   └── test_agent.py                           # Tests end-to-end multi-agent orchestration
├── requirements.txt                            # Python dependencies
└── README.md                                   # Comprehensive documentation
```

---

## 3. Module Details & Integration

### Module 1: Crime Data Processing (`agent/crime_data_processor.py`)
- Loads and cleans raw `atlcrime.csv`, `crime reports.csv`, or canonical `crime_incidents_clean.csv`.
- Filters out non-Atlanta or corrupted GPS coordinates outside $[33.60^\circ, 33.90^\circ]$ lat and $[-84.58^\circ, -84.26^\circ]$ lon.
- Deduplicates identical incident reports (matching date, time, crime type, location, and beat).
- Separates violent crimes (`HOMICIDE`, `AGG ASSAULT`, `RAPE`, `ROBBERY`) from property crimes.
- **Weather-Crime Decoupling**: Explicitly notes that crime data spans 2009–2017 while collected weather data spans 2021–current. Avoids synthetic joins that create spurious causal artifacts.

### Module 2: Crime Risk Prediction (`agent/crime_risk_predictor.py`)
- Supervised `RandomForestClassifier` predicting 4 risk classes:
  1. **Low Risk**
  2. **Medium Risk**
  3. **High Risk**
  4. **Very High Risk**
- **Risk Label Formulation**: Based on spatial-temporal crime severity scores:
  $$\text{Severity} = (\text{Violent Crimes} \times 3.0) + (\text{Property Crimes} \times 1.0)$$
- **Zero Data Leakage**: Enforces strict chronological train/test splitting (Train on 2009–2015, Test on 2016–2017). Spatial density features are strictly fitted on the training split only.
- Model artifacts are serialized with `joblib` into `models/crime_risk_model.joblib`.

### Module 3: Geofencing Integration (`agent/geofence_integration.py`)
- Directly integrates with the existing Geofencing Agent from `Geo-Fancing/geofence.py` via `check_location(latitude, longitude, zones)`.
- **Stateful Transition Tracking** (`TouristLocationTracker`):
  - Detects **`ENTRY`**: When tourist moves from outside into a monitored zone, or between zones.
  - Detects **`INSIDE_UNCHANGED`**: When tourist remains inside the same zone. **Suppresses repeat alerts to prevent notification fatigue.**
  - Detects **`EXIT`**: When tourist leaves a danger zone.
  - Detects **`RISK_ESCALATION`**: When ambient risk escalates inside the zone.
- Standardized to GeoJSON Polygon format in `datasets/atlanta_safety_zones.json`.

### Module 4: Tourist Safety Alert Engine (`agent/alert_engine.py`)
- Synthesizes formatted alerts with:
  * `tourist_coordinates`: `[lat, lon]`
  * `zone_name`: name of the geofenced area or neighborhood
  * `risk_level`: `LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH`, `RESTRICTED`
  * `alert_type`: `NO_WARNING`, `CAUTION`, `SAFETY_WARNING`, `URGENT_SAFETY_WARNING`, `RESTRICTED_ACCESS`
  * `message`: Contextual warning message
  * `recommended_action`: Actionable advice for tourists
  * `emergency_dispatch_eligible`: Boolean flag

### Module 5: Safe Route Recommendation (`agent/safe_route.py`)
- Catalog of verified Atlanta safe tourist havens (e.g., Centennial Olympic Park, Georgia Aquarium Plaza, Midtown Arts Safe Corridor, APD Zone 5 Precinct).
- Computes evasive routes that steer around high-risk zones and strictly forbid restricted areas.
- **Empirical Safety Audit**: Computes supporting quantitative data before claiming a route is safe:
  * High-risk traversal distance (meters)
  * Safe corridor traversal distance (meters)
  * Restricted violations count (must be 0)
  * Safety score percentage (0–100%)

### Module 7: Emergency Response Integration (`agent/emergency_integration.py`)
- Ready interface to connect an external Emergency Response Assignment Agent.
- Grounded registry of real Atlanta emergency facilities (APD Zone 5, Grady Memorial Trauma Center, AFRD Station 1, APD Zone 2).
- Tracks deterministic unit availability (`AVAILABLE`, `ON_PATROL`, `DISPATCHED`).
- Calculates realistic road transit ETAs and produces standardized incident dispatch payloads.

---

## 4. Installation & Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Windows, macOS, or Linux

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 5. Running the Application

### Launch the Streamlit Dashboard (Interactive Demo)
```bash
streamlit run dashboard/app.py
```
Open your browser to `http://localhost:8501`.

#### Features in the Dashboard:
1. **Interactive Walk Simulation**: Walk step-by-step through guided scenarios (e.g. Centennial Park $\to$ Downtown High Risk $\to$ Safe Police Reroute) to demonstrate entry detection, alert suppression, and evasive route planning.
2. **Preset Landmarks**: Instantly snap the tourist to major Atlanta locations (Buckhead, Downtown, Old Fourth Ward, Inman Rail Yard).
3. **Live Geofencing Map**: Folium map displaying crime heatmaps, colored geofence polygons, safe havens, emergency units, and active evasive routes.
4. **Emergency SOS Button**: One-click manual panic button that dispatches the closest emergency unit and plots an immediate escape path.

---

## 6. Running Unit Tests

Run the complete automated test suite (17 tests covering all modules):
```bash
python -m unittest discover tests/ -v
```

All tests pass out-of-the-box:
- Geofencing Point-in-Polygon & entry/exit detection
- Repeated alert suppression verification
- Alert payload validation & recommended actions
- Safe haven discovery and route validation
- End-to-end tourist monitoring & emergency SOS trigger

---

## 7. Programmatic Python API

You can import and run the agent in your own scripts:

```python
from agent.tourist_safety_agent import TouristSafetyAgent

# Initialize agent
agent = TouristSafetyAgent()

# Continuous monitoring call with GPS coordinates
result = agent.monitor_tourist(
    tourist_id="Tourist-101",
    latitude=33.7530,
    longitude=-84.3880,
    auto_dispatch_emergency=True
)

print("Risk Level:", result["effective_risk_level"])
print("Zone:", result["effective_zone_name"])
if result["active_alert"]:
    print("Alert:", result["active_alert"]["message"])
if result["safe_route_recommendation"]:
    print("Recommended Safe Haven:", result["safe_route_recommendation"]["destination"]["name"])
```

---

## 8. Live GPS Integration & Privacy Roadmap

To connect live GPS streams from a tourist mobile app:
1. **REST / WebSocket Ingestion**: Add a lightweight FastAPI endpoint that accepts `POST /api/v1/tourist/location` payloads containing `{tourist_id, lat, lon, timestamp}`.
2. **Privacy by Design**:
   - Store transient coordinates in memory only during active navigation.
   - Anonymize tourist identifiers with cryptographically salted hashes.
   - Flush location history upon session conclusion.

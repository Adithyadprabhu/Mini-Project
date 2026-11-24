# Atlanta Incident Prioritization Agent

A modular, production-ready Public Safety Incident Prioritization Agent built in Python with **FastAPI**, **Pandas**, and **Pydantic**. The agent scores and classifies incoming 911/CAD incidents into **CRITICAL**, **HIGH**, **MEDIUM**, and **LOW** priority tiers by fusing base offense hierarchies, dynamic emergency indicators, victim impact, and historical neighborhood risk context from Atlanta Police Department datasets.

---

## Key Architectural Principles & Requirements Compliance

1. **Pandas Dataset Ingestion**: Loads and indexes `incident_prioritization_dataset.csv` (290k+ unified incidents) and `neighborhood_risk_profile.csv` (242 historical neighborhood profiles).
2. **Incident Feature Fusion**: Combines:
   - Incident type base severity
   - Immediate danger
   - Serious injury
   - Weapon reported
   - Victim count & mass casualty scaling
   - Historical neighborhood risk context (`location_context_band` Q1 to Q4, historical incident percentile)
3. **Missing Data Handling (Requirement 4)**: Treats unknown historical and incoming emergency fields as **`MISSING_UNKNOWN` (None)**, strictly **never coerced to `False`**. Applies an uncertainty safety buffer and data completeness assessment.
4. **Proxy Label Separation (Requirement 5)**: Uses dataset proxy labels (`priority_level_proxy` and `offense_severity_proxy_score`) **only for initial rule-based prototyping and baseline calibration**, with clear disclaimers that historical proxies are not verified ground truth.
5. **Deterministic Priority Scoring Engine**: Computes explainable scores (0.0 to 100.0) with granular component breakdowns and life-safety overrides.
6. **FastAPI Endpoints**: Full REST API providing `POST /prioritize`, `POST /prioritize/batch`, `GET /health`, `GET /neighborhoods`, and `GET /evaluation`.
7. **Strict Non-Automatic Dispatch (Requirement 13)**: The agent **never automatically dispatches emergency services**. All recommendations enforce `auto_dispatch_authorized = False` and require human dispatcher/supervisor triage.
8. **Multi-Agent Integration Ready (Requirement 12)**: Native payload contracts ready for integration with:
   - **Geofencing Agent**: Lat/long spatial verification, containment alert recommendations, and dynamic perimeter radii.
   - **Response Assignment Agent**: Priority queue routing, suggested specialized unit types (e.g. Tactical, ALS EMS, Patrol Supervisor), and staging protocols.

---

## Project Structure

```text
Incident_Prioritization_Agent/
├── agent/
│   ├── __init__.py           # Package exports and interfaces
│   ├── config.py             # Score weights, thresholds, enums, dataset paths
│   ├── data_loader.py        # Pandas loader and O(1) neighborhood profile cache
│   ├── schemas.py            # Pydantic v2 schemas for inputs, outputs, integrations
│   ├── scoring_engine.py     # Deterministic Priority Scoring Engine & override rules
│   ├── evaluator.py          # Prototyping evaluator against historical proxy labels
│   └── api.py                # FastAPI app with POST /prioritize and health endpoints
├── datasets/                 # Atlanta Incident Prioritization Datasets
│   ├── incident_prioritization_dataset.csv
│   ├── neighborhood_risk_profile.csv
│   ├── daily_weather_context.csv
│   └── hourly_weather_context.csv
├── tests/
│   ├── test_data_loader.py       # Dataset loading and missing field checks
│   ├── test_scoring_engine.py    # Scoring engine formulas, overrides, thresholds
│   ├── test_api.py               # FastAPI testclient, validation & error handling
│   └── test_agent_scenarios.py   # Comprehensive multi-scenario public safety tests
├── run.py                    # Server runner and CLI evaluation tool
├── requirements.txt          # Python dependencies
└── README.md                 # Complete documentation
```

---

## Dataset Schema Inspection

### 1. `incident_prioritization_dataset.csv`
Contains 290,370 records spanning Atlanta historical incidents:
- `incident_type`: Offense classification (e.g., `AGG ASSAULT`, `ROBBERY-PEDESTRIAN`, `BURGLARY-RESIDENCE`, `AUTO THEFT`, `LARCENY-FROM VEHICLE`)
- `offense_severity_proxy_score`: Prototyping score proxy (20 to 100)
- `priority_level_proxy`: Prototype proxy level (`CRITICAL_PROXY`, `HIGH_PROXY`, `MEDIUM_PROXY`, `LOW_PROXY`)
- `immediate_danger`: Blank / unrecorded in historical source (`NaN`)
- `serious_injury`: Blank / unrecorded in historical source (`NaN`)
- `weapon_reported`: Blank / unrecorded in historical source (`NaN`)
- `victim_count`: Number of victims
- `neighborhood`, `beat`, `npu`, `address`, `latitude`, `longitude`

### 2. `neighborhood_risk_profile.csv`
Contains 242 neighborhood risk profiles:
- `neighborhood`: Cleaned uppercase neighborhood identifier
- `historical_incident_count`: Historical incident volume
- `location_context_band`: Risk quartile (`Q4_HIGHEST`, `Q3`, `Q2`, `Q1_LOWEST`)
- `historical_count_percentile`: Percentile rank across Atlanta neighborhoods (0.0041 to 1.0)
- `interpretation_warning`: Dataset coverage disclaimer

---

## Priority Scoring Formulation

$$\text{Final Score} = \min(100.0, \, \text{Base} + \Delta_{\text{emergency}} + \Delta_{\text{victims}} + \Delta_{\text{neighborhood}} + \Delta_{\text{uncertainty}})$$

### 1. Base Offense Severity
- **HOMICIDE / ACTIVE SHOOTER**: 95.0 – 100.0
- **RAPE / KIDNAPPING**: 90.0 – 94.0
- **AGGRAVATED ASSAULT / SHOTS FIRED**: 85.0
- **ARMED ROBBERY / ROBBERY**: 70.0 – 78.0
- **BURGLARY (Residence / Non-res)**: 44.0 – 48.0
- **AUTO THEFT**: 34.0
- **LARCENY / THEFT / VANDALISM**: 18.0 – 24.0

### 2. Emergency Factor Modifiers (Requirement 4)
| Field | `True` (Verified) | `False` (Ruled Out) | `None` (Unknown / Missing) |
| :--- | :---: | :---: | :---: |
| **`immediate_danger`** | +25.0 | +0.0 | **+5.0 (Uncertainty Buffer)** |
| **`serious_injury`** | +25.0 | +0.0 | **+5.0 (Uncertainty Buffer)** |
| **`weapon_reported`** | +20.0 | +0.0 | **+3.0 (Uncertainty Buffer)** |

*When emergency fields are omitted or unknown, the engine treats them as `MISSING_UNKNOWN`. Rather than falsely assuming no hazard exists, a precautionary uncertainty buffer is added and flagged for dispatcher verification.*

### 3. Victim Count Scaling
- 1 victim: +0.0
- 2 victims: +6.0
- 3 to 4 victims: +12.0
- 5+ victims (Mass Casualty Alert): +20.0

### 4. Historical Neighborhood Risk Context
- `Q4_HIGHEST` band: +5.0 + (Percentile × 2.5)
- `Q3` band: +3.5 + (Percentile × 2.5)
- `Q2` band: +2.0 + (Percentile × 2.5)
- `Q1_LOWEST` band: +0.0 + (Percentile × 2.5)
- `UNKNOWN` neighborhood: +2.0 neutral buffer

### 5. Life-Safety Critical Overrides
- **Active Danger + Confirmed Weapon**: Minimum floor score of **90.0** (`CRITICAL`).
- **Serious Injury + Multiple Victims**: Minimum floor score of **88.0** (`CRITICAL`).
- **Homicide / Rape / Active Shooter (Active)**: Minimum floor score of **92.0** (`CRITICAL`).
- **Armed Property/Encounter Crime**: Minimum floor score of **75.0** (`HIGH`).

### 6. Classification Tiers
- **CRITICAL**: Final Score $\ge 80.0$
- **HIGH**: $60.0 \le \text{Final Score} < 80.0$
- **MEDIUM**: $40.0 \le \text{Final Score} < 60.0$
- **LOW**: $\text{Final Score} < 40.0$

---

## Installation & Setup

### 1. Requirements
Ensure Python 3.10+ is installed. Install dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Running the API Server
Start the FastAPI server on port 8000:
```powershell
python run.py --host 127.0.0.1 --port 8000
```
Interactive Swagger documentation is available at: **http://127.0.0.1:8000/docs**

### 3. Running Prototype Evaluation CLI
To evaluate the rule-based engine against a sample of historical proxy labels:
```powershell
python run.py --evaluate --sample-size 1000
```

### 4. Running the Automated Test Suite
Execute the complete test suite:
```powershell
python -m pytest tests/ -v
```

---

## API Usage & Endpoints

### 1. `POST /prioritize`
Triage and score a single incident.

#### Example Request:
```json
{
  "incident_id": "ATL-2026-004921",
  "incident_type": "AGG ASSAULT",
  "immediate_danger": true,
  "serious_injury": true,
  "weapon_reported": true,
  "victim_count": 2,
  "neighborhood": "DOWNTOWN",
  "address": "100 PEACHTREE ST NW",
  "latitude": 33.7537,
  "longitude": -84.3863,
  "beat": "501"
}
```

#### Example Response:
```json
{
  "incident_id": "ATL-2026-004921",
  "priority_score": 100.0,
  "priority_level": "CRITICAL",
  "recommended_action": "IMMEDIATE_SUPERVISOR_TRIAGE [WEAPON_ACTIVE, EMS_PRIORITY, LIFE_THREAT, VICTIMS_2]: Elevate to top of active CAD queue. Alert Watch Commander and stage Tactical/EMS units. Human dispatcher review required; automated dispatch disabled.",
  "auto_dispatch_authorized": false,
  "disclaimer": "AUTOMATED DISPATCH DISABLED: This agent performs triage recommendation only. Dispatch authorization requires review and confirmation by a human 911 dispatcher or supervisor.",
  "scoring_breakdown": {
    "base_offense_score": 85.0,
    "matched_offense_type": "AGG ASSAULT",
    "emergency_modifier": 70.0,
    "victim_count_modifier": 6.0,
    "neighborhood_modifier": 7.5,
    "uncertainty_buffer": 0.0,
    "raw_computed_score": 168.5,
    "final_score": 100.0,
    "critical_override_triggered": true,
    "override_reason": "LIFE_SAFETY_OVERRIDE: Active immediate danger combined with confirmed weapon."
  },
  "field_status": {
    "immediate_danger_status": "VERIFIED_TRUE",
    "serious_injury_status": "VERIFIED_TRUE",
    "weapon_reported_status": "VERIFIED_TRUE",
    "missing_fields": [],
    "missing_fields_count": 0,
    "data_completeness_level": "HIGH",
    "confidence_assessment": "All emergency indicators verified by reporter/call-taker."
  },
  "geofencing_integration": {
    "ready_for_geofencing": true,
    "latitude": 33.7537,
    "longitude": -84.3863,
    "neighborhood": "DOWNTOWN",
    "location_context_band": "Q4_HIGHEST",
    "historical_count_percentile": 0.9917,
    "perimeter_alert_recommended": true,
    "suggested_geofence_radius_meters": 1000,
    "geofence_priority_weight": 1.0
  },
  "response_assignment_integration": {
    "ready_for_assignment": true,
    "priority_tier": "CRITICAL",
    "dispatch_queue": "QUEUE_1_EMERGENCY",
    "suggested_unit_types": [
      "PATROL_SUPERVISOR",
      "PRIMARY_PATROL",
      "BACKUP_PATROL",
      "TACTICAL_SUPPORT",
      "EMS_ADVANCED_LIFE_SUPPORT"
    ],
    "minimum_responders": 2,
    "minimum_personnel": 2,
    "staging_instructions": "Stage outside immediate line of sight; coordinate multi-unit synchronized arrival.",
    "supervisor_review_required": true,
    "auto_dispatch_authorized": false
  },
  "evaluated_at": "2026-11-24T07:10:00.000000Z"
}
```

### 2. `POST /prioritize/batch`
Prioritizes a list of incidents in a single call, returning aggregate counts (`critical_count`, `high_count`, `medium_count`, `low_count`) and list of results.

### 3. `GET /health`
Returns system status, auto dispatch safety status (`false`), and number of loaded neighborhood risk profiles.

### 4. `GET /neighborhoods` & `GET /neighborhoods/{name}`
Retrieves historical incident volume, risk quartile bands (`Q1` to `Q4`), and percentile rankings for Atlanta neighborhoods.

### 5. `GET /evaluation`
Runs baseline prototyping evaluation against historical incidents and returns concordance, precision, recall, and missing data audits.

---

## Agent Integration Interfaces

### Geofencing Agent Integration
Exposes:
- `ready_for_geofencing`: Boolean indicating valid coordinate availability.
- `perimeter_alert_recommended`: Automated flag recommending containment perimeter (True for CRITICAL/HIGH with coordinates).
- `suggested_geofence_radius_meters`: 1,000m for CRITICAL, 500m for HIGH, 250m for MEDIUM, 100m for LOW.
- `geofence_priority_weight`: Normalized priority factor (0.0 to 1.0).

### Response Assignment Agent Integration
Exposes:
- `ready_for_assignment`: True.
- `dispatch_queue`: `QUEUE_1_EMERGENCY`, `QUEUE_2_EXPEDITED`, `QUEUE_3_ROUTINE`, `QUEUE_4_ADMINISTRATIVE`.
- `suggested_unit_types`: Matching required skills (e.g. `TACTICAL_SUPPORT`, `EMS_ADVANCED_LIFE_SUPPORT`, `PATROL_SUPERVISOR`).
- `staging_instructions`: Tactical positioning and safety approach guidelines.
- `supervisor_review_required`: Strictly `True`.
- `auto_dispatch_authorized`: Strictly `False`.

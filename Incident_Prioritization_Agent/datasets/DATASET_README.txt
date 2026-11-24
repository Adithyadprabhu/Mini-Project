ATLANTA INCIDENT PRIORITIZATION DATASET
=============================================

Files:
- incident_prioritization_dataset.csv: unified historical incident features.
- neighborhood_risk_profile.csv: historical neighborhood counts and offense mix.
- daily_weather_context.csv: cleaned daily weather kept separate.
- hourly_weather_context.csv: cleaned hourly weather kept separate.

LABEL LIMITATION: priority_level_proxy and offense_severity_proxy_score are offense-category proxies only. They are not verified police dispatch priorities, real urgency outcomes, or ground truth. Immediate danger, serious injury and weapon fields are blank/unknown because the source files do not provide those facts. Do not train a production classifier as if these proxy labels were verified. Obtain expert-reviewed labels.

WEATHER LIMITATION: weather data begins in 2021; crime records are predominantly 2009-2017. Weather is not joined to those historical incidents. Match weather by local date/hour only for incidents that actually fall within the weather coverage period.

DEDUPLICATION: one row per exact key of date + normalized offense + beat + normalized address. atlcrime rows are preferred on exact matches. This does not guarantee all duplicates are identified. Coordinate values outside broad Atlanta bounds were set to missing, not imputed. Check date_quality_flag for anomalous dates.

SUMMARY
{
  "incident_rows": 290370,
  "atlcrime_original_rows": 270688,
  "crime_reports_original_rows": 26759,
  "neighborhoods": 242,
  "date_min": "1916-12-30",
  "date_max": "2017-12-31",
  "missing_coordinates": 225,
  "proxy_labels": {
    "LOW_PROXY": 194313,
    "MEDIUM_PROXY": 53851,
    "CRITICAL_PROXY": 22854,
    "HIGH_PROXY": 19352
  },
  "daily_weather_rows": 1797,
  "daily_weather_range": "2021-01-01 to 2025-12-02",
  "hourly_weather_rows": 43128,
  "hourly_weather_range": "2021-01-01 00:00:00 to 2025-12-02 23:00:00"
}
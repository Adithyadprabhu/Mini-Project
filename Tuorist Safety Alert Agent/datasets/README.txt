Atlanta Crime + Weather Project Dataset

Files:
- crime_incidents_clean.csv: canonical incident records from atlcrime.csv and crime reports.csv. Exact overlapping rows (event date + crime type + normalized location + beat) are deduplicated, preferring the richer 2017 crime reports row.
- crime_daily_counts.csv: daily incident totals and counts by crime type.
- weather_daily_clean.csv: daily weather records, unchanged features with normalized date.
- weather_hourly_clean.csv: hourly weather records, datetime normalized.
- daily_combined_timeline.csv: date panel with daily crime aggregates and weather features plus coverage flags.

Important limitation: crime records cover approximately 2009–2017, while the supplied weather records cover 2021 onward. There is no date overlap. Thus weather features cannot currently be paired with observed crime outcomes for supervised crime/weather modeling. The combined timeline deliberately uses coverage flags; missing crime counts outside crime coverage are not zero, and missing weather outside weather coverage is not an observation.

Suggested project use:
1. Crime risk prediction: use crime_daily_counts.csv or incidents with time, beat, neighborhood, NPU, coordinates.
2. Spatial risk mapping/geofencing: crime_incidents_clean.csv coordinates + neighborhood/beat/NPU.
3. Weather analysis: weather_daily_clean.csv / weather_hourly_clean.csv.
4. To train a weather-aware crime model, obtain crime incidents for 2021–present or weather for 2009–2017.

Coordinate fields: latitude/longitude in decimal degrees (Atlanta). Crime types are uppercased.

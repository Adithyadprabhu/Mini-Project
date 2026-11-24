"""
Weather Context Integration Agent (Module 5).
Safely retrieves and validates weather records for public safety incidents.

Strict Constraints:
- Checks date and time compatibility against 2021-01-01 to 2025-12-02 weather coverage.
- Never joins unrelated historical crime dates (e.g. 2009-2017) with modern weather records.
- Treats weather as contextual advisory, never as the primary determinant of emergency priority.
- Handles missing or unparseable timestamps gracefully.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd

from models.enums import WeatherCompatibility
from models.schemas import WeatherContext

# Resolve weather datasets
def _find_dataset(filename: str) -> Path:
    candidates = [
        Path("datasets") / filename,
        Path("dataset") / filename,
        Path(__file__).resolve().parent.parent / "datasets" / filename,
        Path(__file__).resolve().parent.parent / "dataset" / filename,
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherAgent:
    """
    Contextual weather integration engine with strict temporal isolation.
    """

    WEATHER_MIN_DATE = "2021-01-01"
    WEATHER_MAX_DATE = "2025-12-02"

    def __init__(self):
        self._daily_df: Optional[pd.DataFrame] = None
        self._hourly_df: Optional[pd.DataFrame] = None
        self._daily_cache: Dict[str, Dict[str, Any]] = {}
        self._load_datasets()

    def _load_datasets(self):
        """Loads daily and hourly weather datasets if present."""
        daily_path = _find_dataset("daily_weather_context.csv")
        hourly_path = _find_dataset("hourly_weather_context.csv")

        if daily_path.is_file():
            try:
                df_daily = pd.read_csv(daily_path)
                df_daily["date"] = df_daily["date"].astype(str).str.strip()
                self._daily_df = df_daily
                for _, row in df_daily.iterrows():
                    self._daily_cache[row["date"]] = row.to_dict()
            except Exception:
                pass

        if hourly_path.is_file():
            try:
                # Load hourly index
                df_hourly = pd.read_csv(hourly_path)
                df_hourly["datetime"] = df_hourly["datetime"].astype(str).str.strip()
                self._hourly_df = df_hourly
            except Exception:
                pass

    def get_weather_context(
        self,
        incident_date: Optional[str] = None,
        incident_time: Optional[str] = None,
        timestamp_str: Optional[str] = None,
    ) -> WeatherContext:
        """
        Validates date compatibility and returns contextual weather.
        Never joins mismatched dates.
        """
        # Parse target date and hour
        target_date = None
        target_hour = None

        if timestamp_str:
            try:
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                target_date = dt.strftime("%Y-%m-%d")
                target_hour = dt.hour
            except Exception:
                pass

        if not target_date and incident_date:
            try:
                # Normalise YYYY-MM-DD
                parts = incident_date.strip().split(" ")[0].split("T")[0]
                target_date = parts
            except Exception:
                pass

        if target_hour is None and incident_time:
            try:
                t_parts = incident_time.strip().split(":")
                target_hour = int(t_parts[0])
            except Exception:
                pass

        if not target_date:
            return WeatherContext(
                weather_compatibility=WeatherCompatibility.MISSING_DATA,
                weather_note="No incident date provided. Weather context safely omitted.",
            )

        # STRICT COMPATIBILITY CHECK:
        # Weather data only covers 2021-01-01 to 2025-12-02.
        # Historical Atlanta crime records (primarily 2009-2017) MUST NOT be joined.
        if target_date < self.WEATHER_MIN_DATE or target_date > self.WEATHER_MAX_DATE:
            return WeatherContext(
                weather_compatibility=WeatherCompatibility.OUT_OF_RANGE,
                weather_note=(
                    f"Incident date '{target_date}' falls outside the weather coverage window "
                    f"({self.WEATHER_MIN_DATE} to {self.WEATHER_MAX_DATE}). "
                    "Unrelated historical crime records are isolated without joining modern weather."
                ),
            )

        # Look up in cache
        daily_record = self._daily_cache.get(target_date)
        if not daily_record:
            return WeatherContext(
                weather_compatibility=WeatherCompatibility.MISSING_DATA,
                weather_note=f"Date '{target_date}' within coverage range but daily weather record not found.",
            )

        # Hourly lookup if available
        temp_f = float(daily_record.get("temp_mean_f", 65.0))
        precip_in = float(daily_record.get("rain_sum_in", 0.0))
        w_code = daily_record.get("weather_code_daily")
        apparent_temp = temp_f
        is_daylight = None
        matched_dt_str = target_date

        if self._hourly_df is not None and target_hour is not None:
            hourly_target_str = f"{target_date} {target_hour:02d}:00:00"
            matched_hourly = self._hourly_df[self._hourly_df["datetime"] == hourly_target_str]
            if not matched_hourly.empty:
                h_row = matched_hourly.iloc[0]
                temp_f = float(h_row.get("temp_f", temp_f))
                precip_in = float(h_row.get("precip_in", precip_in))
                apparent_temp = float(h_row.get("apparent_temp_f", temp_f))
                w_code = h_row.get("weather_code_hourly", w_code)
                is_daylight = bool(h_row.get("is_daylight", 1))
                matched_dt_str = hourly_target_str

        code_int = int(w_code) if pd.notna(w_code) else 0
        condition_desc = WMO_WEATHER_CODES.get(code_int, f"Weather Code {code_int}")

        tactical_notes = []
        if precip_in > 0.5:
            tactical_notes.append("Heavy precipitation may impact responder travel times.")
        if is_daylight is False:
            tactical_notes.append("Nighttime conditions: advise scene illumination.")

        extra_note = " " + " ".join(tactical_notes) if tactical_notes else ""

        return WeatherContext(
            weather_compatibility=WeatherCompatibility.COMPATIBLE,
            matched_datetime=matched_dt_str,
            temperature_f=round(temp_f, 1),
            precipitation_in=round(precip_in, 2),
            apparent_temp_f=round(apparent_temp, 1),
            weather_condition=condition_desc,
            is_daylight=is_daylight,
            weather_note=f"Context matched for {matched_dt_str}: {condition_desc}.{extra_note}",
        )


# Singleton
_weather_agent_instance: Optional[WeatherAgent] = None

def get_weather_agent() -> WeatherAgent:
    global _weather_agent_instance
    if _weather_agent_instance is None:
        _weather_agent_instance = WeatherAgent()
    return _weather_agent_instance

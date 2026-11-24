"""
Data Loader Module for Atlanta Incident Datasets.
Uses pandas to load, validate, and index incident records and neighborhood risk profiles.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from agent.config import (
    INCIDENT_DATASET_PATH,
    NEIGHBORHOOD_RISK_PATH,
    LocationContextBand,
    resolve_dataset_path,
)


class DataLoader:
    """
    Loads and provides indexed access to:
    1. neighborhood_risk_profile.csv: historical neighborhood risk bands and percentiles
    2. incident_prioritization_dataset.csv: historical incidents with proxy labels
    """

    def __init__(
        self,
        incident_dataset_path: Optional[Path] = None,
        neighborhood_risk_path: Optional[Path] = None,
        lazy_load_incidents: bool = True,
    ):
        self.incident_dataset_path = incident_dataset_path or INCIDENT_DATASET_PATH
        self.neighborhood_risk_path = neighborhood_risk_path or NEIGHBORHOOD_RISK_PATH
        self.lazy_load_incidents = lazy_load_incidents

        self._neighborhood_df: Optional[pd.DataFrame] = None
        self._neighborhood_map: Dict[str, Dict[str, Any]] = {}
        self._incidents_df: Optional[pd.DataFrame] = None

        self._load_neighborhood_profiles()
        if not self.lazy_load_incidents:
            self._load_incident_dataset()

    def _load_neighborhood_profiles(self) -> None:
        """Loads and indexes neighborhood risk profiles using pandas."""
        path = resolve_dataset_path(self.neighborhood_risk_path.name)
        if not path.is_file():
            # If path not found directly, check both datasets/ and dataset/
            raise FileNotFoundError(
                f"Neighborhood risk profile CSV not found at {path}. "
                "Ensure neighborhood_risk_profile.csv exists in datasets/ or dataset/ folder."
            )

        df = pd.read_csv(path)
        # Normalize columns and clean neighborhood names
        df["neighborhood_clean"] = df["neighborhood"].astype(str).str.strip().str.upper()
        
        # Build dictionary lookup for O(1) retrieval
        lookup = {}
        for _, row in df.iterrows():
            name = row["neighborhood_clean"]
            band_str = str(row.get("location_context_band", "UNKNOWN"))
            try:
                band = LocationContextBand(band_str)
            except ValueError:
                band = LocationContextBand.UNKNOWN

            lookup[name] = {
                "neighborhood": row["neighborhood"],
                "historical_incident_count": int(row.get("historical_incident_count", 0)),
                "critical_offense_count": int(row.get("critical_offense_count", 0)),
                "high_offense_count": int(row.get("high_offense_count", 0)),
                "medium_offense_count": int(row.get("medium_offense_count", 0)),
                "low_offense_count": int(row.get("low_offense_count", 0)),
                "historical_count_percentile": float(row.get("historical_count_percentile", 0.5)),
                "location_context_band": band,
                "first_recorded_date": str(row.get("first_recorded_date", "")),
                "last_recorded_date": str(row.get("last_recorded_date", "")),
                "interpretation_warning": str(row.get("interpretation_warning", "")),
            }

        self._neighborhood_df = df
        self._neighborhood_map = lookup

    def _load_incident_dataset(self, nrows: Optional[int] = None) -> pd.DataFrame:
        """
        Loads incident dataset with pandas.
        Explicitly treats unknown historical emergency fields as missing (NaN/None), NOT false.
        """
        path = resolve_dataset_path(self.incident_dataset_path.name)
        if not path.is_file():
            raise FileNotFoundError(
                f"Incident prioritization dataset CSV not found at {path}. "
                "Ensure incident_prioritization_dataset.csv exists in datasets/ or dataset/ folder."
            )

        # Columns to import with specified types to avoid warnings
        dtype_spec = {
            "incident_type": "str",
            "offense_severity_proxy_score": "float64",
            "priority_level_proxy": "str",
            "neighborhood": "str",
            "beat": "str",
            "victim_count": "float64",
            "source_record_id": "str",
        }

        # Note: immediate_danger, serious_injury, weapon_reported are blank/NaN in historical CSV.
        # Requirement 4: Treat unknown historical emergency fields as missing, not false.
        df = pd.read_csv(
            path,
            nrows=nrows,
            dtype=dtype_spec,
            low_memory=False,
            keep_default_na=True,  # Blank values become NaN / None, NOT False
        )

        # Verify emergency fields remain missing (NaN/None) and are never coerced to False
        for field in ["immediate_danger", "serious_injury", "weapon_reported"]:
            if field in df.columns:
                # Replace any unexpected string representation of nulls with np.nan
                df[field] = df[field].replace(["", "None", "NULL", "NaN"], np.nan)

        self._incidents_df = df
        return df

    def get_neighborhood_profile(self, neighborhood_name: Optional[str]) -> Dict[str, Any]:
        """
        Retrieves historical neighborhood context by name.
        Returns a conservative default profile if the neighborhood is unknown.
        """
        if not neighborhood_name:
            return self._default_neighborhood_profile("UNSPECIFIED")

        clean_name = str(neighborhood_name).strip().upper()
        if clean_name in self._neighborhood_map:
            return self._neighborhood_map[clean_name]

        # Fuzzy / partial fallback (e.g. "MIDTOWN ATLANTA" -> "MIDTOWN")
        for known_name, profile in self._neighborhood_map.items():
            if known_name in clean_name or clean_name in known_name:
                return profile

        return self._default_neighborhood_profile(clean_name)

    def _default_neighborhood_profile(self, name: str) -> Dict[str, Any]:
        """Provides neutral fallback context for unknown neighborhoods."""
        return {
            "neighborhood": name,
            "historical_incident_count": 0,
            "critical_offense_count": 0,
            "high_offense_count": 0,
            "medium_offense_count": 0,
            "low_offense_count": 0,
            "historical_count_percentile": 0.50,  # Median default
            "location_context_band": LocationContextBand.UNKNOWN,
            "first_recorded_date": "",
            "last_recorded_date": "",
            "interpretation_warning": (
                "Neighborhood not found in Atlanta historical risk profile. "
                "Using neutral baseline context without bias."
            ),
        }

    def list_neighborhoods(self) -> List[Dict[str, Any]]:
        """Returns list of all known neighborhood risk profiles."""
        return list(self._neighborhood_map.values())

    def get_sample_incidents(self, n: int = 1000) -> pd.DataFrame:
        """Returns a sample of the historical incidents for prototyping and baseline checks."""
        if self._incidents_df is None:
            return self._load_incident_dataset(nrows=n)
        return self._incidents_df.head(n)


# Global singleton instance
_loader_instance: Optional[DataLoader] = None

def get_data_loader() -> DataLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DataLoader()
    return _loader_instance

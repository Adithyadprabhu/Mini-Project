"""
Unit tests for DataLoader.
Tests loading incident_prioritization_dataset.csv and neighborhood_risk_profile.csv.
Verifies Requirement 4: Treat unknown historical emergency fields as missing, not false.
"""

import numpy as np
import pandas as pd
import pytest
from agent.config import LocationContextBand
from agent.data_loader import DataLoader, get_data_loader


def test_neighborhood_risk_profile_loading():
    loader = get_data_loader()
    neighborhoods = loader.list_neighborhoods()
    assert len(neighborhoods) >= 200, "Should load all Atlanta neighborhoods"

    # Check known neighborhood (e.g. DOWNTOWN or MIDTOWN)
    downtown = loader.get_neighborhood_profile("DOWNTOWN")
    assert downtown["neighborhood"] == "DOWNTOWN"
    assert downtown["location_context_band"] == LocationContextBand.Q4_HIGHEST
    assert downtown["historical_count_percentile"] > 0.90
    assert "interpretation_warning" in downtown


def test_unknown_neighborhood_fallback():
    loader = get_data_loader()
    profile = loader.get_neighborhood_profile("NON_EXISTENT_ZONE_XYZ")
    assert profile["location_context_band"] == LocationContextBand.UNKNOWN
    assert profile["historical_count_percentile"] == 0.50
    assert "not found" in profile["interpretation_warning"].lower()


def test_incident_dataset_emergency_fields_treated_as_missing_not_false():
    """
    Requirement 4: Treat unknown historical emergency fields as missing, not false.
    Verify that blank/unrecorded emergency fields in the historical dataset are NaN/missing,
    and NOT converted or filled with False.
    """
    loader = get_data_loader()
    df = loader.get_sample_incidents(n=500)
    assert not df.empty
    assert "incident_type" in df.columns
    assert "priority_level_proxy" in df.columns

    # Verify emergency fields are present and are NaN / missing
    for emergency_col in ["immediate_danger", "serious_injury", "weapon_reported"]:
        assert emergency_col in df.columns
        # None of the historical values should be False or True
        val_counts = df[emergency_col].value_counts(dropna=False)
        # All or virtually all values should be NaN/null in historical data
        null_count = df[emergency_col].isna().sum()
        assert null_count > 0, f"{emergency_col} should have missing values"
        # Confirm that missing values were NOT coerced to boolean False
        assert (df[emergency_col] == False).sum() == 0, f"{emergency_col} must NOT be falsely coerced to False"

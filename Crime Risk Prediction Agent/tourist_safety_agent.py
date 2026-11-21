"""
Tourist Safety & Crime Risk Prediction Agent
A modular integration agent built on top of Predspot for Tourist Safety Management Systems.
"""
from typing import Dict, Any, Optional
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sklearn.ensemble import RandomForestRegressor

from predspot import Dataset, PredictionPipeline
from predspot.crime_mapping import QuadratCount, create_gridhexagonal
from predspot.feature_engineering import AR, Diff
from predspot.utilities import PandasFeatureUnion
from predspot.pipeline import generate_testdata

class TouristSafetyAgent:
    """
    Crime Risk Prediction Agent for Tourist Safety Systems.
    Provides spatio-temporal risk forecasting and geofence generation for warning tourists.
    """
    def __init__(self, study_area_gdf: gpd.GeoDataFrame, resolution_km: float = 1.0, tfreq: str = "M"):
        self.study_area = study_area_gdf
        self.resolution_km = resolution_km
        self.tfreq = tfreq
        self.grid = create_gridhexagonal(study_area_gdf, resolution=resolution_km)
        
        self.pipeline = PredictionPipeline(
            mapping=QuadratCount(tfreq=tfreq, grid=self.grid),
            fextraction=PandasFeatureUnion([
                ("ar", AR(lags=3, tfreq=tfreq)),
                ("diff", Diff(lags=3, tfreq=tfreq)),
            ]),
            estimator=RandomForestRegressor(n_estimators=50, random_state=42)
        )
        self.forecast_gdf: Optional[gpd.GeoDataFrame] = None
        self.low_threshold: float = 0.0
        self.high_threshold: float = 0.0

    def fit_and_predict(self, crimes_df: pd.DataFrame) -> gpd.GeoDataFrame:
        """
        Fits the spatio-temporal model on historical crime records and generates risk forecasts.
        """
        dataset = Dataset(crimes_df, self.study_area)
        self.pipeline.fit(dataset)
        raw_forecast = self.pipeline.predict()

        df = raw_forecast.copy()
        col = df.columns[0]
        
        # 50th percentile = Low Risk boundary, 85th percentile = High Risk boundary
        self.low_threshold = float(df[col].quantile(0.50))
        self.high_threshold = float(df[col].quantile(0.85))

        def get_risk_label(val):
            if val <= self.low_threshold:
                return "Low Risk"
            elif val <= self.high_threshold:
                return "Medium Risk"
            else:
                return "High Risk"

        df["risk_score"] = df[col]
        df["risk_level"] = df[col].apply(get_risk_label)
        places = df.index.get_level_values("places")
        df["geometry"] = self.grid.loc[places, "geometry"].values

        self.forecast_gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=self.study_area.crs)
        return self.forecast_gdf

    def check_tourist_location(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Evaluates a tourist's real-time coordinate against the latest risk geofences.
        """
        if self.forecast_gdf is None:
            raise ValueError("Model has not been trained yet. Call fit_and_predict() first.")
        
        point = Point(lon, lat)
        match = self.forecast_gdf[self.forecast_gdf.geometry.contains(point)]
        
        if match.empty:
            return {
                "latitude": lat,
                "longitude": lon,
                "risk_level": "Unknown (Outside Study Area)",
                "risk_score": 0.0,
                "warning": False,
                "message": "Tourist is currently outside the monitored tourist zone."
            }
        
        row = match.iloc[0]
        level = row["risk_level"]
        score = float(row["risk_score"])
        is_high = (level == "High Risk")
        
        return {
            "latitude": lat,
            "longitude": lon,
            "risk_level": level,
            "risk_score": round(score, 2),
            "warning": is_high,
            "message": "WARNING: Tourist entered a High-Risk Crime Area! Advisory notification triggered." if is_high else f"Tourist is in a {level} area."
        }

    def export_high_risk_geofences(self, output_geojson_path: str = "high_risk_geofences.geojson") -> str:
        """
        Exports high-risk polygon boundaries as GeoJSON for the Geofencing Agent.
        """
        if self.forecast_gdf is None:
            raise ValueError("Model has not been trained yet.")
        
        high_risk = self.forecast_gdf[self.forecast_gdf["risk_level"] == "High Risk"]
        geojson_str = high_risk[["risk_level", "risk_score", "geometry"]].to_json()
        with open(output_geojson_path, "w") as f:
            f.write(geojson_str)
        return output_geojson_path

if __name__ == "__main__":
    print("Testing TouristSafetyAgent...")
    crimes, area = generate_testdata(1000, "2023-01-01", "2024-12-31", seed=42)
    agent = TouristSafetyAgent(area, resolution_km=2.0)
    agent.fit_and_predict(crimes)
    
    # Test sample coordinate
    sample_pt = area.geometry.iloc[0].centroid
    res = agent.check_tourist_location(sample_pt.y, sample_pt.x)
    print("Agent Query Result:", json.dumps(res, indent=2))

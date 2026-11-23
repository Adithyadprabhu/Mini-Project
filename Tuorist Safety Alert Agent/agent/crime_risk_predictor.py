"""
Module 2: Crime Risk Prediction Model
Trains and evaluates a machine learning classifier (Random Forest) to predict 4 risk categories:
  - Low Risk
  - Medium Risk
  - High Risk
  - Very High Risk

Enforces strict chronological train/test splitting to prevent future data leakage.
Exports model to joblib and metrics to JSON.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

logger = logging.getLogger(__name__)

RISK_LEVEL_MAP = {
    0: "Low Risk",
    1: "Medium Risk",
    2: "High Risk",
    3: "Very High Risk",
}
REVERSE_RISK_MAP = {v: k for k, v in RISK_LEVEL_MAP.items()}


class CrimeRiskPredictor:
    """
    Supervised Machine Learning predictor for spatio-temporal tourist crime risk in Atlanta.
    """

    FEATURE_COLS = [
        "grid_lat",
        "grid_lon",
        "month",
        "day_of_week_num",
        "hour_bin",
        "is_weekend",
        "is_night",
        "grid_historical_crimes",
    ]

    def __init__(self, model_dir: Optional[str] = None):
        base_dir = Path(__file__).resolve().parent.parent
        self.model_dir = Path(model_dir) if model_dir else (base_dir / "models")
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.model_path = self.model_dir / "crime_risk_model.joblib"
        self.metrics_path = self.model_dir / "model_metrics.json"

        self.model: Optional[RandomForestClassifier] = None
        self.metrics: Dict[str, Any] = {}
        self.grid_history_lookup: Dict[str, float] = {}
        self.default_grid_crime: float = 1.0
        self.grid_resolution_deg: float = 0.01

    def train_and_evaluate(
        self,
        ml_df: pd.DataFrame,
        split_year: int = 2016,
        n_estimators: int = 100,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """
        Trains the Random Forest model using chronological splitting to avoid data leakage.
        Train set: year < split_year (e.g. 2009-2015)
        Test set: year >= split_year (e.g. 2016-2017)
        """
        logger.info(f"Starting model training with chronological split at year {split_year}...")

        # Ensure sorted chronologically
        ml_df = ml_df.sort_values(by=["year", "month"]).reset_index(drop=True)

        # Chronological train/test split
        train_mask = ml_df["year"] < split_year
        test_mask = ml_df["year"] >= split_year

        # If test set is too small (e.g. on small sample), fallback to 80/20 time-ordered split
        if test_mask.sum() < 100 or train_mask.sum() < 100:
            logger.warning(
                f"Chronological split produced insufficient test samples ({test_mask.sum()}). "
                "Using chronological 80/20 index split."
            )
            split_idx = int(len(ml_df) * 0.8)
            train_df = ml_df.iloc[:split_idx].copy()
            test_df = ml_df.iloc[split_idx:].copy()
        else:
            train_df = ml_df[train_mask].copy()
            test_df = ml_df[test_mask].copy()

        logger.info(f"Train samples: {len(train_df)}, Test samples: {len(test_df)}")

        # To avoid data leakage, compute spatial crime history purely from train_df
        train_grid_counts = train_df.groupby("grid_id")["incident_count"].sum().to_dict()
        self.grid_history_lookup = train_grid_counts
        self.default_grid_crime = float(np.median(list(train_grid_counts.values()))) if train_grid_counts else 1.0

        train_df["grid_historical_crimes"] = (
            train_df["grid_id"].map(train_grid_counts).fillna(self.default_grid_crime)
        )
        test_df["grid_historical_crimes"] = (
            test_df["grid_id"].map(train_grid_counts).fillna(self.default_grid_crime)
        )

        X_train = train_df[self.FEATURE_COLS]
        y_train = train_df["risk_code"]

        X_test = test_df[self.FEATURE_COLS]
        y_test = test_df["risk_code"]

        # Train Random Forest Classifier with balanced class weights
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=12,
            min_samples_split=6,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)

        # Predictions on test set
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)

        # Metrics calculation
        target_names = [RISK_LEVEL_MAP[i] for i in sorted(RISK_LEVEL_MAP.keys())]
        report = classification_report(
            y_test,
            y_pred,
            target_names=target_names,
            output_dict=True,
            zero_division=0,
        )
        cm = confusion_matrix(y_test, y_pred).tolist()

        feature_importances = dict(
            zip(self.FEATURE_COLS, [round(float(v), 4) for v in self.model.feature_importances_])
        )

        self.metrics = {
            "model_type": "RandomForestClassifier",
            "train_samples": int(len(train_df)),
            "test_samples": int(len(test_df)),
            "split_method": f"Chronological split (Train < {split_year}, Test >= {split_year})",
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "macro_f1": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4),
            "weighted_f1": round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
            "macro_precision": round(float(precision_score(y_test, y_pred, average="macro", zero_division=0)), 4),
            "macro_recall": round(float(recall_score(y_test, y_pred, average="macro", zero_division=0)), 4),
            "classification_report": report,
            "confusion_matrix": cm,
            "feature_importances": feature_importances,
            "target_classes": target_names,
            "trained_at": datetime.now().isoformat(),
        }

        # Save artifacts
        self.save_model()
        logger.info(f"Model evaluation complete! Test Accuracy: {self.metrics['accuracy']}, Weighted F1: {self.metrics['weighted_f1']}")
        return self.metrics

    def save_model(self) -> None:
        """Persists trained model and lookup tables."""
        if self.model is None:
            raise ValueError("No model trained to save.")

        payload = {
            "model": self.model,
            "feature_cols": self.FEATURE_COLS,
            "grid_history_lookup": self.grid_history_lookup,
            "default_grid_crime": self.default_grid_crime,
            "grid_resolution_deg": self.grid_resolution_deg,
            "risk_level_map": RISK_LEVEL_MAP,
        }
        joblib.dump(payload, self.model_path)
        logger.info(f"Saved model artifact to {self.model_path}")

        with open(self.metrics_path, "w", encoding="utf-8") as f:
            json.dump(self.metrics, f, indent=4)
        logger.info(f"Saved metrics to {self.metrics_path}")

    def load_model(self) -> bool:
        """Loads serialized model and artifacts."""
        if not self.model_path.exists():
            return False

        try:
            payload = joblib.load(self.model_path)
            self.model = payload["model"]
            self.grid_history_lookup = payload.get("grid_history_lookup", {})
            self.default_grid_crime = payload.get("default_grid_crime", 1.0)
            self.grid_resolution_deg = payload.get("grid_resolution_deg", 0.01)

            if self.metrics_path.exists():
                with open(self.metrics_path, "r", encoding="utf-8") as f:
                    self.metrics = json.load(f)
            return True
        except Exception as e:
            logger.error(f"Failed to load model from {self.model_path}: {e}")
            return False

    def predict_risk(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Predicts crime risk level for a tourist coordinate and time.
        Returns:
          - risk_level: str ("Low Risk", "Medium Risk", "High Risk", "Very High Risk")
          - risk_code: int (0 to 3)
          - probabilities: Dict[str, float]
          - confidence: float
        """
        if self.model is None:
            if not self.load_model():
                raise RuntimeError("Model is not loaded or trained. Call train_and_evaluate() first.")

        dt = timestamp or datetime.now()
        month = dt.month
        day_of_week_num = dt.weekday()
        hour = dt.hour
        hour_bin = min(hour // 4, 5)
        is_weekend = 1 if day_of_week_num in [5, 6] else 0
        is_night = 1 if (hour >= 20 or hour <= 5) else 0

        grid_lat = round(round(latitude / self.grid_resolution_deg) * self.grid_resolution_deg, 4)
        grid_lon = round(round(longitude / self.grid_resolution_deg) * self.grid_resolution_deg, 4)
        grid_id = f"{grid_lat}_{grid_lon}"

        grid_hist = self.grid_history_lookup.get(grid_id, self.default_grid_crime)

        features = pd.DataFrame([{
            "grid_lat": grid_lat,
            "grid_lon": grid_lon,
            "month": month,
            "day_of_week_num": day_of_week_num,
            "hour_bin": hour_bin,
            "is_weekend": is_weekend,
            "is_night": is_night,
            "grid_historical_crimes": grid_hist,
        }])[self.FEATURE_COLS]

        code = int(self.model.predict(features)[0])
        probas = self.model.predict_proba(features)[0]

        # Map class probabilities
        prob_dict = {}
        for class_idx, class_name in RISK_LEVEL_MAP.items():
            if class_idx < len(probas):
                prob_dict[class_name] = round(float(probas[class_idx]), 4)
            else:
                prob_dict[class_name] = 0.0

        confidence = prob_dict.get(RISK_LEVEL_MAP[code], round(float(np.max(probas)), 4))

        return {
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": dt.isoformat(),
            "risk_level": RISK_LEVEL_MAP[code],
            "risk_code": code,
            "confidence": confidence,
            "probabilities": prob_dict,
            "grid_id": grid_id,
            "is_night": bool(is_night),
            "is_weekend": bool(is_weekend),
        }


if __name__ == "__main__":
    from crime_data_processor import CrimeDataProcessor
    logging.basicConfig(level=logging.INFO)

    proc = CrimeDataProcessor()
    df = proc.load_clean_data(sample_size=30000)
    ml_df, _ = proc.build_risk_training_features(df)

    predictor = CrimeRiskPredictor()
    metrics = predictor.train_and_evaluate(ml_df, split_year=2016)

    print("\n--- Model Metrics Summary ---")
    print(f"Accuracy: {metrics['accuracy']}")
    print(f"Macro F1: {metrics['macro_f1']}")
    print(f"Weighted F1: {metrics['weighted_f1']}")
    print("Feature Importances:", metrics["feature_importances"])

    # Test coordinate prediction: Downtown Atlanta
    res = predictor.predict_risk(33.7550, -84.3900)
    print("\nDowntown Atlanta Risk Prediction:")
    print(json.dumps(res, indent=2))

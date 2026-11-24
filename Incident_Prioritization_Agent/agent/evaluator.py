"""
Evaluation module for Incident Prioritization Agent.

Fulfills Requirement 5:
"Use the priority proxy labels only for initial rule-based prototyping and evaluation,
not as verified ground truth."
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from agent.config import PriorityLevel
from agent.data_loader import DataLoader, get_data_loader
from agent.schemas import EvaluationSummaryResponse, IncidentInput
from agent.scoring_engine import PriorityScoringEngine


PROXY_LABEL_MAPPING = {
    "CRITICAL_PROXY": PriorityLevel.CRITICAL,
    "HIGH_PROXY": PriorityLevel.HIGH,
    "MEDIUM_PROXY": PriorityLevel.MEDIUM,
    "LOW_PROXY": PriorityLevel.LOW,
}

PROTOTYPE_WARNING = (
    "PROTOTYPE LABEL LIMITATION: The 'priority_level_proxy' and 'offense_severity_proxy_score' "
    "are offense-category proxies from the Atlanta crime dataset. They are NOT verified 911 "
    "dispatch priorities or ground truth. Historical emergency fields (immediate danger, serious injury, "
    "weapon reported) are unrecorded and treated as missing. Use these evaluation metrics strictly "
    "for rule-based calibration, not as proof of production classification accuracy."
)


class PrototypeEvaluator:
    """
    Evaluates rule-based engine against historical proxy labels for prototyping calibration.
    """

    def __init__(
        self,
        engine: Optional[PriorityScoringEngine] = None,
        data_loader: Optional[DataLoader] = None,
    ):
        self.data_loader = data_loader or get_data_loader()
        self.engine = engine or PriorityScoringEngine(data_loader=self.data_loader)

    def evaluate_sample(self, sample_size: int = 2000) -> EvaluationSummaryResponse:
        """
        Runs a sample of historical incidents through the scoring engine and evaluates
        concordance against the proxy labels.
        """
        df = self.data_loader.get_sample_incidents(n=sample_size)
        
        # Filter for rows that have proxy labels
        df_valid = df.dropna(subset=["priority_level_proxy", "incident_type"]).copy()
        if df_valid.empty:
            raise ValueError("No valid historical rows found for evaluation.")

        total = len(df_valid)
        concordant = 0

        # Classes
        classes = [
            PriorityLevel.CRITICAL.value,
            PriorityLevel.HIGH.value,
            PriorityLevel.MEDIUM.value,
            PriorityLevel.LOW.value,
        ]

        confusion_matrix = {c_true: {c_pred: 0 for c_pred in classes} for c_true in classes}
        class_totals_true = {c: 0 for c in classes}
        class_totals_pred = {c: 0 for c in classes}

        # Track missing historical emergency fields
        missing_counts = {
            "immediate_danger_missing": int(df_valid["immediate_danger"].isna().sum()) if "immediate_danger" in df_valid else total,
            "serious_injury_missing": int(df_valid["serious_injury"].isna().sum()) if "serious_injury" in df_valid else total,
            "weapon_reported_missing": int(df_valid["weapon_reported"].isna().sum()) if "weapon_reported" in df_valid else total,
        }

        for idx, row in df_valid.iterrows():
            proxy_str = str(row["priority_level_proxy"]).strip()
            target_level = PROXY_LABEL_MAPPING.get(proxy_str)
            if not target_level:
                continue

            # Build IncidentInput with historical fields (emergency fields remain None / missing)
            # Note: Requirement 4: Treat unknown historical emergency fields as missing, not false!
            raw_danger = row.get("immediate_danger")
            immediate_danger = None if pd.isna(raw_danger) else bool(raw_danger)

            raw_injury = row.get("serious_injury")
            serious_injury = None if pd.isna(raw_injury) else bool(raw_injury)

            raw_weapon = row.get("weapon_reported")
            weapon_reported = None if pd.isna(raw_weapon) else bool(raw_weapon)

            raw_victims = row.get("victim_count")
            victim_count = 1 if pd.isna(raw_victims) else int(raw_victims)

            incident_input = IncidentInput(
                incident_id=f"HIST-{idx}",
                incident_type=str(row["incident_type"]),
                immediate_danger=immediate_danger,
                serious_injury=serious_injury,
                weapon_reported=weapon_reported,
                victim_count=victim_count,
                neighborhood=str(row.get("neighborhood", "")) if pd.notna(row.get("neighborhood")) else None,
            )

            result = self.engine.prioritize(incident_input)
            predicted_level = result.priority_level

            t_val = target_level.value
            p_val = predicted_level.value

            confusion_matrix[t_val][p_val] += 1
            class_totals_true[t_val] += 1
            class_totals_pred[p_val] += 1

            if t_val == p_val:
                concordant += 1

        overall_concordance = round(concordant / total, 4) if total > 0 else 0.0

        per_class_metrics = {}
        for c in classes:
            tp = confusion_matrix[c][c]
            fn = class_totals_true[c] - tp
            fp = class_totals_pred[c] - tp

            precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
            recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
            f1 = round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0

            per_class_metrics[c] = {
                "support_proxy_count": class_totals_true[c],
                "predicted_count": class_totals_pred[c],
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
            }

        return EvaluationSummaryResponse(
            prototype_warning=PROTOTYPE_WARNING,
            evaluated_sample_size=total,
            overall_proxy_concordance=overall_concordance,
            per_class_metrics=per_class_metrics,
            missing_emergency_fields_handled=missing_counts,
        )

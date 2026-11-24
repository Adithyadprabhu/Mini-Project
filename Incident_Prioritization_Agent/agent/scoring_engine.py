"""
Priority Scoring Engine for Atlanta Incident Prioritization Agent.

Combines:
1. Base offense severity score (calibrated against Atlanta historical proxy baseline)
2. Dynamic emergency factors (immediate danger, serious injury, weapon reported)
   - Treats unknown fields as missing (None), NOT as False (Requirement 4)
3. Victim count scaling (multi-victim and mass casualty impact)
4. Historical neighborhood location risk context (from neighborhood_risk_profile.csv)
5. Safety-critical overrides for acute life-safety threats
6. Classification into CRITICAL, HIGH, MEDIUM, and LOW (Requirement 7)
7. Triage action recommendations strictly requiring human supervisor review (Requirement 13)
8. Seamless payloads for Geofencing Agent and Response Assignment Agent (Requirement 12)
"""

from typing import Any, Dict, List, Optional, Tuple
from agent.config import (
    AUTO_DISPATCH_ENABLED,
    BASE_OFFENSE_SCORES,
    DEFAULT_OFFENSE_SCORE,
    DISPATCH_DISCLAIMER,
    EmergencyFieldState,
    LocationContextBand,
    PriorityLevel,
    SCORE_THRESHOLDS,
    WEIGHTS,
)
from agent.data_loader import DataLoader, get_data_loader
from agent.schemas import (
    FieldMissingStatus,
    GeofencingIntegration,
    IncidentInput,
    PrioritizationResponse,
    ResponseAssignmentIntegration,
    ScoringBreakdown,
)


class PriorityScoringEngine:
    """
    Deterministic, explainable Priority Scoring Engine for public safety incidents.
    """

    def __init__(self, data_loader: Optional[DataLoader] = None):
        self.data_loader = data_loader or get_data_loader()

    def prioritize(self, incident: IncidentInput) -> PrioritizationResponse:
        """
        Calculates priority score, assigns priority tier, and generates actionable recommendation.
        """
        # 1. Base Offense Severity Score
        base_score, matched_offense = self._calculate_base_offense_score(incident.incident_type)

        # 2. Emergency Modifiers & Missing Data Handling
        (
            emergency_modifier,
            uncertainty_buffer,
            field_status,
        ) = self._evaluate_emergency_fields(
            immediate_danger=incident.immediate_danger,
            serious_injury=incident.serious_injury,
            weapon_reported=incident.weapon_reported,
        )

        # 3. Victim Count Modifier
        victim_modifier = self._calculate_victim_modifier(incident.victim_count)

        # 4. Historical Neighborhood Location Context Modifier
        neighborhood_profile = self.data_loader.get_neighborhood_profile(incident.neighborhood)
        neighborhood_modifier = self._calculate_neighborhood_modifier(neighborhood_profile)

        # 5. Raw Score Aggregation
        raw_score = (
            base_score
            + emergency_modifier
            + victim_modifier
            + neighborhood_modifier
            + uncertainty_buffer
        )

        # 6. Safety-Critical Overrides
        final_score, override_triggered, override_reason = self._apply_critical_overrides(
            raw_score=raw_score,
            incident_type=matched_offense,
            immediate_danger=incident.immediate_danger,
            serious_injury=incident.serious_injury,
            weapon_reported=incident.weapon_reported,
            victim_count=incident.victim_count or 1,
        )

        # Ensure final score is clamped between 0.0 and 100.0
        final_score = max(0.0, min(100.0, round(final_score, 1)))

        # 7. Priority Level Classification (Requirement 7)
        priority_level = self._classify_priority_level(final_score, override_triggered)

        # 8. Actionable Dispatch Recommendation (Requirement 9, 13)
        recommended_action = self._determine_recommended_action(
            priority_level=priority_level,
            immediate_danger=incident.immediate_danger,
            weapon_reported=incident.weapon_reported,
            serious_injury=incident.serious_injury,
            victim_count=incident.victim_count or 1,
            missing_count=field_status.missing_fields_count,
        )

        # 9. Geofencing Agent Integration Payload (Requirement 12)
        geofencing_payload = self._build_geofencing_integration(
            incident=incident,
            neighborhood_profile=neighborhood_profile,
            priority_level=priority_level,
            final_score=final_score,
        )

        # 10. Response Assignment Agent Integration Payload (Requirement 12, 13)
        assignment_payload = self._build_assignment_integration(
            incident=incident,
            priority_level=priority_level,
            matched_offense=matched_offense,
            serious_injury=incident.serious_injury,
            weapon_reported=incident.weapon_reported,
            victim_count=incident.victim_count or 1,
        )

        scoring_breakdown = ScoringBreakdown(
            base_offense_score=round(base_score, 1),
            matched_offense_type=matched_offense,
            emergency_modifier=round(emergency_modifier, 1),
            victim_count_modifier=round(victim_modifier, 1),
            neighborhood_modifier=round(neighborhood_modifier, 1),
            uncertainty_buffer=round(uncertainty_buffer, 1),
            raw_computed_score=round(raw_score, 1),
            final_score=final_score,
            critical_override_triggered=override_triggered,
            override_reason=override_reason,
        )

        return PrioritizationResponse(
            incident_id=incident.incident_id,
            priority_score=final_score,
            priority_level=priority_level,
            recommended_action=recommended_action,
            auto_dispatch_authorized=AUTO_DISPATCH_ENABLED,
            disclaimer=DISPATCH_DISCLAIMER,
            scoring_breakdown=scoring_breakdown,
            field_status=field_status,
            geofencing_integration=geofencing_payload,
            response_assignment_integration=assignment_payload,
        )

    def _calculate_base_offense_score(self, incident_type: str) -> Tuple[float, str]:
        """Matches incident type against calibrated historical scores and aliases."""
        clean_type = incident_type.strip().upper()
        
        # Exact match
        if clean_type in BASE_OFFENSE_SCORES:
            return BASE_OFFENSE_SCORES[clean_type], clean_type

        # Substring / Alias matching
        for known_type, score in BASE_OFFENSE_SCORES.items():
            if known_type in clean_type or clean_type in known_type:
                return score, known_type

        # Keyword heuristics
        if any(w in clean_type for w in ["MURDER", "HOMICIDE", "SHOOTING"]):
            return 98.0, "HOMICIDE"
        if any(w in clean_type for w in ["RAPE", "SEXUAL ASSAULT"]):
            return 94.0, "RAPE"
        if any(w in clean_type for w in ["ASSAULT", "BATTERY", "STABBING", "ATTACK"]):
            return 88.0, "AGG ASSAULT"
        if any(w in clean_type for w in ["ROBBERY", "MUGGING", "HOLDUP"]):
            return 75.0, "ROBBERY-PEDESTRIAN"
        if any(w in clean_type for w in ["BURGLARY", "BREAK-IN", "INTRUDER"]):
            return 54.0, "BURGLARY-RESIDENCE"
        if any(w in clean_type for w in ["CAR THEFT", "AUTO THEFT", "STOLEN CAR"]):
            return 40.0, "AUTO THEFT"
        if any(w in clean_type for w in ["LARCENY", "THEFT", "SHOPLIFTING"]):
            return 28.0, "LARCENY-NON VEHICLE"

        return DEFAULT_OFFENSE_SCORE, clean_type

    def _evaluate_emergency_fields(
        self,
        immediate_danger: Optional[bool],
        serious_injury: Optional[bool],
        weapon_reported: Optional[bool],
    ) -> Tuple[float, float, FieldMissingStatus]:
        """
        Evaluates emergency fields strictly treating None/unknown as missing, NOT false.
        
        - Verified True adds urgency modifier.
        - Verified False adds 0.
        - Missing (None) adds an uncertainty buffer to avoid dangerously under-triaging unknown risk.
        """
        emergency_modifier = 0.0
        uncertainty_buffer = 0.0
        missing_fields: List[str] = []

        # 1. Immediate Danger
        if immediate_danger is True:
            danger_status = EmergencyFieldState.VERIFIED_TRUE
            emergency_modifier += WEIGHTS["immediate_danger_true"]
        elif immediate_danger is False:
            danger_status = EmergencyFieldState.VERIFIED_FALSE
        else:
            danger_status = EmergencyFieldState.MISSING_UNKNOWN
            missing_fields.append("immediate_danger")
            uncertainty_buffer += WEIGHTS["immediate_danger_missing_buffer"]

        # 2. Serious Injury
        if serious_injury is True:
            injury_status = EmergencyFieldState.VERIFIED_TRUE
            emergency_modifier += WEIGHTS["serious_injury_true"]
        elif serious_injury is False:
            injury_status = EmergencyFieldState.VERIFIED_FALSE
        else:
            injury_status = EmergencyFieldState.MISSING_UNKNOWN
            missing_fields.append("serious_injury")
            uncertainty_buffer += WEIGHTS["serious_injury_missing_buffer"]

        # 3. Weapon Reported
        if weapon_reported is True:
            weapon_status = EmergencyFieldState.VERIFIED_TRUE
            emergency_modifier += WEIGHTS["weapon_reported_true"]
        elif weapon_reported is False:
            weapon_status = EmergencyFieldState.VERIFIED_FALSE
        else:
            weapon_status = EmergencyFieldState.MISSING_UNKNOWN
            missing_fields.append("weapon_reported")
            uncertainty_buffer += WEIGHTS["weapon_reported_missing_buffer"]

        missing_count = len(missing_fields)
        if missing_count == 0:
            completeness = "HIGH"
            confidence = "All emergency indicators verified by reporter/call-taker."
        elif missing_count == 1:
            completeness = "MEDIUM"
            confidence = f"Minor uncertainty: '{missing_fields[0]}' unverified; precautionary buffer applied."
        elif missing_count == 2:
            completeness = "LOW"
            confidence = "Substantial uncertainty: 2 emergency indicators unknown; dispatcher inquiry advised."
        else:
            completeness = "MINIMAL"
            confidence = (
                "Historical/intake default: All 3 emergency fields missing. "
                "Triage reflects offense baseline with conservative safety buffer."
            )

        status_obj = FieldMissingStatus(
            immediate_danger_status=danger_status,
            serious_injury_status=injury_status,
            weapon_reported_status=weapon_status,
            missing_fields=missing_fields,
            missing_fields_count=missing_count,
            data_completeness_level=completeness,
            confidence_assessment=confidence,
        )

        return emergency_modifier, uncertainty_buffer, status_obj

    def _calculate_victim_modifier(self, victim_count: Optional[int]) -> float:
        """Scales score based on victim count and mass casualty risk."""
        if not victim_count or victim_count <= 1:
            return WEIGHTS["victim_single"]
        if victim_count == 2:
            return WEIGHTS["victim_two"]
        if 3 <= victim_count <= 4:
            return WEIGHTS["victim_three_to_four"]
        return WEIGHTS["victim_mass_casualty"]

    def _calculate_neighborhood_modifier(self, profile: Dict[str, Any]) -> float:
        """Calculates location context bonus from neighborhood risk profile."""
        band = profile.get("location_context_band", LocationContextBand.UNKNOWN)
        percentile = float(profile.get("historical_count_percentile", 0.50))

        if band == LocationContextBand.Q4_HIGHEST:
            base_band_score = WEIGHTS["neighborhood_q4"]
        elif band == LocationContextBand.Q3:
            base_band_score = WEIGHTS["neighborhood_q3"]
        elif band == LocationContextBand.Q2:
            base_band_score = WEIGHTS["neighborhood_q2"]
        elif band == LocationContextBand.Q1_LOWEST:
            base_band_score = WEIGHTS["neighborhood_q1"]
        else:
            base_band_score = WEIGHTS["neighborhood_unknown"]

        percentile_bonus = percentile * WEIGHTS["neighborhood_percentile_weight"]
        return base_band_score + percentile_bonus

    def _apply_critical_overrides(
        self,
        raw_score: float,
        incident_type: str,
        immediate_danger: Optional[bool],
        serious_injury: Optional[bool],
        weapon_reported: Optional[bool],
        victim_count: int,
    ) -> Tuple[float, bool, Optional[str]]:
        """
        Life-safety critical hard overrides to prevent triage failure on acute emergencies.
        """
        # Override 1: Active life danger + reported weapon -> Guaranteed CRITICAL
        if immediate_danger is True and weapon_reported is True:
            floor_score = 90.0
            if raw_score < floor_score:
                return (
                    floor_score,
                    True,
                    "LIFE_SAFETY_OVERRIDE: Active immediate danger combined with confirmed weapon.",
                )

        # Override 2: Serious injury with multiple victims -> Guaranteed CRITICAL
        if serious_injury is True and victim_count >= 2:
            floor_score = 88.0
            if raw_score < floor_score:
                return (
                    floor_score,
                    True,
                    "MASS_CASUALTY_OVERRIDE: Confirmed serious injury with multiple victims.",
                )

        # Override 3: Homicide, Rape, or Active Shooter with immediate danger -> Guaranteed CRITICAL
        if incident_type in ["HOMICIDE", "RAPE", "ACTIVE SHOOTER"] and immediate_danger is not False:
            floor_score = 92.0
            if raw_score < floor_score:
                return (
                    floor_score,
                    True,
                    f"VIOLENT_CRIME_OVERRIDE: Critical violent offense '{incident_type}' without danger ruled out.",
                )

        # Override 4: Active weapon reported in burglary or robbery -> Elevate to at least HIGH
        if weapon_reported is True and any(w in incident_type for w in ["ROBBERY", "BURGLARY"]):
            floor_score = 75.0
            if raw_score < floor_score:
                return (
                    floor_score,
                    True,
                    "ARMED_ENCOUNTER_OVERRIDE: Weapon present during property/encounter offense.",
                )

        return raw_score, False, None

    def _classify_priority_level(self, score: float, override_triggered: bool) -> PriorityLevel:
        """Assigns priority level based on calibrated score thresholds."""
        if score >= SCORE_THRESHOLDS[PriorityLevel.CRITICAL]:
            return PriorityLevel.CRITICAL
        if score >= SCORE_THRESHOLDS[PriorityLevel.HIGH]:
            return PriorityLevel.HIGH
        if score >= SCORE_THRESHOLDS[PriorityLevel.MEDIUM]:
            return PriorityLevel.MEDIUM
        return PriorityLevel.LOW

    def _determine_recommended_action(
        self,
        priority_level: PriorityLevel,
        immediate_danger: Optional[bool],
        weapon_reported: Optional[bool],
        serious_injury: Optional[bool],
        victim_count: int,
        missing_count: int,
    ) -> str:
        """
        Generates standard operating triage recommendations for dispatch personnel.
        Explicitly reinforces Requirement 13 (no automatic dispatch).
        """
        if priority_level == PriorityLevel.CRITICAL:
            hazard_tags = []
            if weapon_reported is True:
                hazard_tags.append("WEAPON_ACTIVE")
            if serious_injury is True:
                hazard_tags.append("EMS_PRIORITY")
            if immediate_danger is True:
                hazard_tags.append("LIFE_THREAT")
            if victim_count >= 2:
                hazard_tags.append(f"VICTIMS_{victim_count}")

            tag_str = f" [{', '.join(hazard_tags)}]" if hazard_tags else ""
            return (
                f"IMMEDIATE_SUPERVISOR_TRIAGE{tag_str}: Elevate to top of active CAD queue. "
                "Alert Watch Commander and stage Tactical/EMS units. Human dispatcher review required; "
                "automated dispatch disabled."
            )

        if priority_level == PriorityLevel.HIGH:
            return (
                "EXPEDITED_DISPATCHER_REVIEW: Place in priority dispatch queue. "
                "Verify responder safety protocols and assign nearest available patrol sector. "
                "Confirm scene safety before final unit dispatch."
            )

        if priority_level == PriorityLevel.MEDIUM:
            missing_note = " Verify unconfirmed emergency fields on callback." if missing_count > 0 else ""
            return (
                f"STANDARD_QUEUE: Route to routine patrol queue for non-emergency response.{missing_note} "
                "Pending available sector units."
            )

        return (
            "ROUTINE_ADMIN_REVIEW: Low urgency property/administrative event. "
            "Route to teleserve / online crime reporting or routine low-priority queue."
        )

    def _build_geofencing_integration(
        self,
        incident: IncidentInput,
        neighborhood_profile: Dict[str, Any],
        priority_level: PriorityLevel,
        final_score: float,
    ) -> GeofencingIntegration:
        """Builds Geofencing Agent payload for spatial boundary & containment checks."""
        has_coords = incident.latitude is not None and incident.longitude is not None
        band = neighborhood_profile.get("location_context_band", LocationContextBand.UNKNOWN)
        percentile = float(neighborhood_profile.get("historical_count_percentile", 0.50))

        # Recommend geofence alert for CRITICAL / HIGH incidents with valid coordinates
        perimeter_alert = has_coords and priority_level in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]

        # Suggested radius based on severity
        if priority_level == PriorityLevel.CRITICAL:
            radius = 1000  # 1km containment
        elif priority_level == PriorityLevel.HIGH:
            radius = 500   # 500m alert zone
        elif priority_level == PriorityLevel.MEDIUM:
            radius = 250
        else:
            radius = 100

        return GeofencingIntegration(
            ready_for_geofencing=has_coords,
            latitude=incident.latitude,
            longitude=incident.longitude,
            neighborhood=neighborhood_profile.get("neighborhood"),
            location_context_band=band,
            historical_count_percentile=percentile,
            perimeter_alert_recommended=perimeter_alert,
            suggested_geofence_radius_meters=radius,
            geofence_priority_weight=round(final_score / 100.0, 2),
        )

    def _build_assignment_integration(
        self,
        incident: IncidentInput,
        priority_level: PriorityLevel,
        matched_offense: str,
        serious_injury: Optional[bool],
        weapon_reported: Optional[bool],
        victim_count: int,
    ) -> ResponseAssignmentIntegration:
        """Builds Response Assignment Agent payload for unit capability matching."""
        suggested_units = []
        min_responders = 1

        if priority_level == PriorityLevel.CRITICAL:
            suggested_units.extend(["PATROL_SUPERVISOR", "PRIMARY_PATROL", "BACKUP_PATROL"])
            min_responders = 2
            if weapon_reported is True:
                suggested_units.append("TACTICAL_SUPPORT")
            if serious_injury is True or victim_count >= 2:
                suggested_units.append("EMS_ADVANCED_LIFE_SUPPORT")
            staging = "Stage outside immediate line of sight; coordinate multi-unit synchronized arrival."
            queue = "QUEUE_1_EMERGENCY"

        elif priority_level == PriorityLevel.HIGH:
            suggested_units.extend(["PRIMARY_PATROL", "BACKUP_PATROL"])
            min_responders = 2
            if serious_injury is True:
                suggested_units.append("EMS_BASIC_LIFE_SUPPORT")
            staging = "Proceed with caution; verify caller updates en route."
            queue = "QUEUE_2_EXPEDITED"

        elif priority_level == PriorityLevel.MEDIUM:
            suggested_units.append("PRIMARY_PATROL")
            min_responders = 1
            staging = "Standard response when unit available."
            queue = "QUEUE_3_ROUTINE"

        else:
            suggested_units.append("COMMUNITY_SERVICE_OFFICER")
            min_responders = 1
            staging = "Teleserve / non-emergency response."
            queue = "QUEUE_4_ADMINISTRATIVE"

        return ResponseAssignmentIntegration(
            ready_for_assignment=True,
            priority_tier=priority_level,
            dispatch_queue=queue,
            suggested_unit_types=suggested_units,
            minimum_responders=min_responders,
            minimum_personnel=min_responders,
            staging_instructions=staging,
            supervisor_review_required=True,
            auto_dispatch_authorized=False,
        )

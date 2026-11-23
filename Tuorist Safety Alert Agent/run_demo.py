"""
Quick Demonstration Runner for Tourist Safety Alert Agent
"""
from agent.tourist_safety_agent import TouristSafetyAgent

def run_demonstration():
    agent = TouristSafetyAgent()

    print("=" * 65)
    print("🤖 ATLANTA TOURIST SAFETY ALERT AGENT — LIVE DEMONSTRATION")
    print("=" * 65)

    # 1. Tourist in Safe Haven
    print("\n📍 SCENARIO 1: Tourist arrives at Centennial Olympic Park (Safe Haven)")
    r1 = agent.monitor_tourist("Tourist-Demo", 33.7603, -84.3931)
    print(f"  • Risk Level      : {r1['effective_risk_level']}")
    print(f"  • Geofence Zone   : {r1['effective_zone_name']}")
    print(f"  • Transition Event: {r1['geofence_status']['event_type']}")
    print(f"  • Alert Fired     : {r1['new_alert_generated']}")

    # 2. Tourist enters High-Risk Area
    print("\n📍 SCENARIO 2: Tourist enters Downtown High-Theft Commercial Sector")
    r2 = agent.monitor_tourist("Tourist-Demo", 33.7530, -84.3880)
    print(f"  • Risk Level      : {r2['effective_risk_level']}")
    print(f"  • Geofence Zone   : {r2['effective_zone_name']}")
    print(f"  • Transition Event: {r2['geofence_status']['event_type']}")
    print(f"  • Alert Header    : {r2['active_alert']['alert_type']}")
    print(f"  • Warning Message : {r2['active_alert']['message']}")
    print(f"  • Recommended Act : {r2['active_alert']['recommended_action']}")
    print(f"  • Safe Evasion To : {r2['safe_route_recommendation']['destination']['name']}")
    print(f"  • Route Distance  : {r2['safe_route_recommendation']['total_distance_m']} m (~{r2['safe_route_recommendation']['estimated_walking_time_min']} mins walk)")
    print(f"  • Safety Score    : {r2['safe_route_recommendation']['safety_score_pct']}%")

    # 3. Tourist remains in the same zone (Suppression Verification)
    print("\n📍 SCENARIO 3: Tourist takes 3 steps inside Downtown (Alert Suppression Test)")
    r3 = agent.monitor_tourist("Tourist-Demo", 33.7525, -84.3875)
    print(f"  • Transition Event: {r3['geofence_status']['event_type']}")
    print(f"  • Alert Fired     : {r3['new_alert_generated']} (Alert suppressed to prevent spamming!)")
    print(f"  • Status Message  : {r3['geofence_status']['status_message']}")

    # 4. Tourist breaches Restricted Zone
    print("\n📍 SCENARIO 4: Tourist approaches Restricted Inman Industrial Rail Yard")
    r4 = agent.monitor_tourist("Tourist-Demo", 33.8000, -84.4360, auto_dispatch_emergency=True)
    print(f"  • Zone Type       : {r4['effective_zone_type']}")
    print(f"  • Alert Type      : {r4['active_alert']['alert_type']}")
    print(f"  • Warning Message : {r4['active_alert']['message']}")
    print(f"  • Emergency Dispatch Success: {r4['emergency_dispatch']['dispatch_success']}")
    unit = r4['emergency_dispatch']['dispatched_unit']
    print(f"  • Dispatched Unit : {unit['unit_id']} ({unit['station_name']})")
    print(f"  • Dispatch ETA    : {unit['eta_minutes']} minutes (Distance: {unit['distance_km']} km)")

    # 5. Manual SOS Trigger
    print("\n📍 SCENARIO 5: Tourist Triggers Emergency SOS Panic Button")
    sos = agent.trigger_sos("Tourist-Demo", 33.7550, -84.3900)
    print(f"  • SOS Status      : {sos['status']}")
    print(f"  • Unit Assigned   : {sos['dispatch']['dispatched_unit']['unit_id']}")
    print(f"  • Immediate Safe Route To: {sos['evasive_route']['destination']['name']}")

    print("\n" + "=" * 65)
    print("✅ All modules executed seamlessly!")
    print("=" * 65)

if __name__ == "__main__":
    run_demonstration()

from shapely.geometry import Point, shape


def check_location(latitude, longitude, zones):
    tourist_point = Point(longitude, latitude)

    for zone in zones:
        geometry = shape(zone["geometry"])

        if geometry.contains(tourist_point):
            return {
                "inside": True,
                "zone_name": zone["name"],
                "risk_level": zone["risk_level"],
                "zone_type": zone["zone_type"],
                "message": f"You entered {zone['name']}"
            }

    return {
        "inside": False,
        "zone_name": None,
        "risk_level": "LOW",
        "zone_type": "SAFE",
        "message": "You are currently outside the monitored danger zones."
    }
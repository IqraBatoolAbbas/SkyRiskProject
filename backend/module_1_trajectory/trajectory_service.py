"""
Module 1: Flight & 4D Trajectory Management
Implements 4D Trajectory representation (Latitude, Longitude, Altitude, Time).
Supports Great-Circle interpolation, waypoint generation, speed/heading calculation,
and telemetry integration (ADS-B / OpenSky / AviationStack schemas).
"""

import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

# Standard Aerodrome coordinates database (Pakistani & Regional)
AERODROMES = {
    "OPKC": {"name": "Jinnah Intl, Karachi", "lat": 24.9065, "lon": 67.1608, "elev_ft": 100},
    "OPLA": {"name": "Allama Iqbal Intl, Lahore", "lat": 31.5216, "lon": 74.4036, "elev_ft": 712},
    "OPIS": {"name": "Islamabad Intl, Islamabad", "lat": 33.5651, "lon": 72.8517, "elev_ft": 1762},
    "OPPS": {"name": "Bacha Khan Intl, Peshawar", "lat": 33.9939, "lon": 71.5146, "elev_ft": 1178},
    "OPQT": {"name": "Quetta Intl, Quetta", "lat": 30.2515, "lon": 66.9378, "elev_ft": 5262},
    "OPST": {"name": "Sialkot Intl, Sialkot", "lat": 32.5356, "lon": 74.3644, "elev_ft": 837},
    "OPFA": {"name": "Faisalabad Intl, Faisalabad", "lat": 31.3653, "lon": 72.9950, "elev_ft": 607},
    "OPMT": {"name": "Multan Intl, Multan", "lat": 30.2033, "lon": 71.4189, "elev_ft": 407},
    "OMDB": {"name": "Dubai Intl, UAE", "lat": 25.2532, "lon": 55.3657, "elev_ft": 62},
    "OTHH": {"name": "Hamad Intl, Doha", "lat": 25.2731, "lon": 51.6081, "elev_ft": 13},
    "OEDF": {"name": "King Fahd Intl, Dammam", "lat": 26.4712, "lon": 49.7978, "elev_ft": 72},
}

# Standard FIR Airway En-route fixes
AIRWAY_FIXES = {
    "RK": {"name": "Rahim Yar Khan VOR", "lat": 28.42, "lon": 70.30},
    "SULOM": {"name": "SULOM (Multan Sector Fix)", "lat": 30.15, "lon": 71.45},
    "TRK": {"name": "Toba Tek Singh Fix", "lat": 30.97, "lon": 72.48},
    "BAHWL": {"name": "Bahawalpur Waypoint", "lat": 29.39, "lon": 71.68},
    "NH": {"name": "Nawabshah VOR", "lat": 26.25, "lon": 68.37},
    "JHANG": {"name": "Jhang Fix", "lat": 31.27, "lon": 72.33},
    "SUKKUR": {"name": "Sukkur VOR", "lat": 27.70, "lon": 68.85},
    "KORAL": {"name": "Koral Waypoint", "lat": 29.80, "lon": 71.90},
    "OKARA": {"name": "Okara Fix", "lat": 30.80, "lon": 73.45},
    "KALAT": {"name": "Kalat Waypoint", "lat": 29.03, "lon": 66.59},
}

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance between two coordinates in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

def calculate_initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial magnetic/true bearing in degrees (0-360)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

def interpolate_segment(p1: Dict[str, Any], p2: Dict[str, Any], num_samples: int = 4) -> List[Dict[str, Any]]:
    """Interpolates coordinates, altitude, and timestamp between two 4D waypoints."""
    samples = []
    for i in range(1, num_samples):
        ratio = i / float(num_samples)
        lat = p1["lat"] + ratio * (p2["lat"] - p1["lat"])
        lon = p1["lon"] + ratio * (p2["lon"] - p1["lon"])
        alt = int(p1["alt"] + ratio * (p2["alt"] - p1["alt"]))
        time_min = round(p1["time_min"] + ratio * (p2["time_min"] - p1["time_min"]), 1)
        speed = round(p1["speed"] + ratio * (p2["speed"] - p1["speed"]), 1)
        bearing = round(calculate_initial_bearing(p1["lat"], p1["lon"], p2["lat"], p2["lon"]), 1)

        samples.append({
            "name": f"{p1['name']}+{int(ratio*100)}%",
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "alt": alt,
            "time_min": time_min,
            "speed_kts": speed,
            "heading_deg": bearing,
            "is_synthetic": True,
        })
    return samples

def generate_4d_trajectory(
    origin_icao: str,
    dest_icao: str,
    cruise_fl: int = 360,
    cruise_speed_kts: int = 450,
    custom_waypoints: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Builds a full 4D trajectory model consisting of:
    - 4 dimensions: Latitude, Longitude, Altitude (ft), Time (offset minutes / UTC).
    - Climb, cruise, and descent profile.
    - Airway fixes and waypoint distances.
    """
    origin = AERODROMES.get(origin_icao, {"name": f"Aerodrome {origin_icao}", "lat": 24.9, "lon": 67.1, "elev_ft": 100})
    dest = AERODROMES.get(dest_icao, {"name": f"Aerodrome {dest_icao}", "lat": 31.5, "lon": 74.4, "elev_ft": 700})

    target_cruise_alt = cruise_fl * 100
    total_direct_km = calculate_distance_km(origin["lat"], origin["lon"], dest["lat"], dest["lon"])

    waypoints = []

    if custom_waypoints and len(custom_waypoints) >= 2:
        # Use provided waypoints
        current_time = 0.0
        for i, wp in enumerate(custom_waypoints):
            if i > 0:
                prev = custom_waypoints[i - 1]
                leg_dist = calculate_distance_km(prev["lat"], prev["lon"], wp["lat"], wp["lon"])
                leg_time = (leg_dist / (cruise_speed_kts * 1.852)) * 60.0
                current_time += leg_time

            waypoints.append({
                "sequence": i + 1,
                "name": wp.get("name", f"WPT-{i+1}"),
                "lat": wp["lat"],
                "lon": wp["lon"],
                "alt": wp.get("alt", target_cruise_alt),
                "time_min": round(current_time, 1),
                "speed_kts": cruise_speed_kts if 0 < i < len(custom_waypoints) - 1 else 160,
                "heading_deg": wp.get("heading", 40.0),
                "is_hotspot": wp.get("is_hotspot", False),
            })
    else:
        # Generate default airway corridor (e.g. OPKC -> OPIS / OPLA)
        # Climb fix at 25% of route, cruise midpoints, descent fix at 80%
        w1 = {
            "sequence": 1,
            "name": origin_icao,
            "lat": origin["lat"],
            "lon": origin["lon"],
            "alt": origin["elev_ft"],
            "time_min": 0.0,
            "speed_kts": 160,
            "heading_deg": calculate_initial_bearing(origin["lat"], origin["lon"], dest["lat"], dest["lon"]),
            "is_hotspot": False,
        }

        # Step 2: Climb / Top of Climb (TOC)
        mid_lat = origin["lat"] + 0.35 * (dest["lat"] - origin["lat"])
        mid_lon = origin["lon"] + 0.35 * (dest["lon"] - origin["lon"])
        d1 = calculate_distance_km(origin["lat"], origin["lon"], mid_lat, mid_lon)
        t1 = (d1 / (320 * 1.852)) * 60.0  # slower climb speed

        w2 = {
            "sequence": 2,
            "name": "TOC / RK Sector",
            "lat": round(mid_lat, 4),
            "lon": round(mid_lon, 4),
            "alt": target_cruise_alt,
            "time_min": round(t1, 1),
            "speed_kts": cruise_speed_kts,
            "heading_deg": calculate_initial_bearing(mid_lat, mid_lon, dest["lat"], dest["lon"]),
            "is_hotspot": False,
        }

        # Step 3: En-route Midpoint
        mid2_lat = origin["lat"] + 0.65 * (dest["lat"] - origin["lat"])
        mid2_lon = origin["lon"] + 0.65 * (dest["lon"] - origin["lon"])
        d2 = calculate_distance_km(mid_lat, mid_lon, mid2_lat, mid2_lon)
        t2 = t1 + (d2 / (cruise_speed_kts * 1.852)) * 60.0

        w3 = {
            "sequence": 3,
            "name": "SULOM / Midpoint",
            "lat": round(mid2_lat, 4),
            "lon": round(mid2_lon, 4),
            "alt": target_cruise_alt,
            "time_min": round(t2, 1),
            "speed_kts": cruise_speed_kts,
            "heading_deg": calculate_initial_bearing(mid2_lat, mid2_lon, dest["lat"], dest["lon"]),
            "is_hotspot": False,
        }

        # Step 4: Top of Descent (TOD)
        mid3_lat = origin["lat"] + 0.85 * (dest["lat"] - origin["lat"])
        mid3_lon = origin["lon"] + 0.85 * (dest["lon"] - origin["lon"])
        d3 = calculate_distance_km(mid2_lat, mid2_lon, mid3_lat, mid3_lon)
        t3 = t2 + (d3 / (cruise_speed_kts * 1.852)) * 60.0

        w4 = {
            "sequence": 4,
            "name": "TOD / Inbound Fix",
            "lat": round(mid3_lat, 4),
            "lon": round(mid3_lon, 4),
            "alt": int(target_cruise_alt * 0.5),
            "time_min": round(t3, 1),
            "speed_kts": 340,
            "heading_deg": calculate_initial_bearing(mid3_lat, mid3_lon, dest["lat"], dest["lon"]),
            "is_hotspot": False,
        }

        # Step 5: Destination Touchdown
        d4 = calculate_distance_km(mid3_lat, mid3_lon, dest["lat"], dest["lon"])
        t4 = t3 + (d4 / (240 * 1.852)) * 60.0

        w5 = {
            "sequence": 5,
            "name": dest_icao,
            "lat": dest["lat"],
            "lon": dest["lon"],
            "alt": dest["elev_ft"],
            "time_min": round(t4, 1),
            "speed_kts": 140,
            "heading_deg": calculate_initial_bearing(mid3_lat, mid3_lon, dest["lat"], dest["lon"]),
            "is_hotspot": False,
        }

        waypoints = [w1, w2, w3, w4, w5]

    total_time_min = waypoints[-1]["time_min"]

    return {
        "origin": origin_icao,
        "destination": dest_icao,
        "cruise_altitude_ft": target_cruise_alt,
        "cruise_speed_kts": cruise_speed_kts,
        "total_distance_km": round(total_direct_km, 1),
        "total_time_enroute_min": round(total_time_min, 1),
        "waypoint_count": len(waypoints),
        "waypoints": waypoints,
    }


from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import csv
import json
import math
import statistics

# ============================================================
# SkyRisk Auditor - Recovery Decision Support Prototype
# Uses existing flight and hazard data.
# Generates exploratory lateral route alternatives.
# NOT for operational flight planning or real-world clearance.
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT / "flight_data" / "processed"
    / "hazard_indicators_oct20_22.csv"
)
OUTPUT_DIR = ROOT / "flight_data" / "processed"
REPORT_DIR = ROOT / "flight_data" / "reports"

FLIGHT_OUTPUT = OUTPUT_DIR / "recovery_flight_assessment_oct20_22.csv"
ROUTE_OUTPUT = OUTPUT_DIR / "recovery_route_candidates_oct20_22.csv"
REPORT_OUTPUT = REPORT_DIR / "recovery_decision_support_report_oct20_22.json"

# Prototype configuration, not aviation safety thresholds.
HOTSPOT_PERCENTILE = 90
DETOUR_DISTANCES_KM = [15, 25]
EARTH_RADIUS_KM = 6371.0

FEATURES = {
    "precipitation": "precipitation_percentile",
    "wind_gusts": "wind_gusts_percentile",
    "wind_speed_10m": "wind_speed_10m_percentile",
    "wind_speed_100m": "wind_speed_100m_percentile",
    "cloud_cover": "cloud_cover_percentile",
    "space_weather_kp": "space_weather_kp_percentile",
}


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found:\n{path}"
        )
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def num(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def quantile(values, q):
    """Linearly interpolated quantile, without extra dependencies."""
    ordered = sorted(values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * q
    low = int(math.floor(position))
    high = int(math.ceil(position))

    if low == high:
        return ordered[low]

    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = p2 - p1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(
        min(1.0, math.sqrt(a))
    )


def interpolate_point(lat1, lon1, lat2, lon2, fraction):
    return (
        lat1 + (lat2 - lat1) * fraction,
        lon1 + (lon2 - lon1) * fraction,
    )


def offset_point(lat, lon, bearing_degrees, distance_km):
    """Move a coordinate by a distance along a bearing."""
    angular_distance = distance_km / EARTH_RADIUS_KM
    bearing = math.radians(bearing_degrees)
    lat1, lon1 = math.radians(lat), math.radians(lon)

    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_distance)
        + math.cos(lat1) * math.sin(angular_distance)
        * math.cos(bearing)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angular_distance)
        * math.cos(lat1),
        math.cos(angular_distance)
        - math.sin(lat1) * math.sin(lat2),
    )

    lon2 = (lon2 + 3 * math.pi) % (2 * math.pi) - math.pi
    return math.degrees(lat2), math.degrees(lon2)


def total_distance(points):
    total = 0.0
    for a, b in zip(points, points[1:]):
        total += haversine_km(a[0], a[1], b[0], b[1])
    return total


def feature_evidence(row):
    evidence = []
    for name, column in FEATURES.items():
        value = num(row.get(column))
        if value is not None:
            evidence.append((value, name))
    return sorted(evidence, reverse=True)


def main():
    rows = read_csv(INPUT_FILE)
    if not rows:
        raise ValueError("Input CSV is empty.")

    grouped = defaultdict(list)
    all_scores = []

    for row in rows:
        flight_id = (row.get("flight_id") or "").strip()
        lat = num(row.get("latitude"))
        lon = num(row.get("longitude"))
        score = num(row.get("relative_hazard_indicator"))

        if not flight_id or lat is None or lon is None:
            continue

        item = dict(row)
        item["_lat"] = lat
        item["_lon"] = lon
        item["_score"] = score

        grouped[flight_id].append(item)
        if score is not None:
            all_scores.append(score)

    if not all_scores:
        raise ValueError(
            "No usable relative_hazard_indicator values found."
        )

    # Relative hotspot cutoff derived from this dataset.
    cutoff = quantile(all_scores, HOTSPOT_PERCENTILE / 100)

    flight_assessments = []
    route_candidates = []

    for flight_id, points in grouped.items():
        points.sort(
            key=lambda p: (
                num(p.get("segment_index")) or 0,
                num(p.get("point_index")) or 0,
                p.get("timestamp_utc", ""),
            )
        )

        valid_points = [p for p in points if p["_score"] is not None]
        hotspots = [
            p for p in valid_points if p["_score"] >= cutoff
        ]

        original_coords = [(p["_lat"], p["_lon"]) for p in points]
        original_distance = total_distance(original_coords)

        notam_points = [
            p for p in points
            if p.get("notam_evidence_indicator")
            == "UNCONFIRMED_NOTAM_CANDIDATE"
        ]

        if not valid_points:
            status = "INSUFFICIENT_HAZARD_DATA"
        elif hotspots:
            status = "RELATIVE_HOTSPOT_REQUIRES_REVIEW"
        else:
            status = "NO_TOP_DECILE_HOTSPOT_IDENTIFIED"

        # Flight-level assessment.
        scores = [p["_score"] for p in valid_points]
        flight_assessments.append({
            "flight_id": flight_id,
            "point_count": len(points),
            "points_with_indicator": len(valid_points),
            "hotspot_point_count": len(hotspots),
            "max_relative_indicator": (
                round(max(scores), 2) if scores else ""
            ),
            "mean_relative_indicator": (
                round(statistics.mean(scores), 2) if scores else ""
            ),
            "notam_candidate_point_count": len(notam_points),
            "notam_numbers": ";".join(sorted({
                n.strip()
                for p in notam_points
                for n in (p.get("notam_numbers") or "").split(";")
                if n.strip()
            })),
            "original_track_distance_km": round(original_distance, 2),
            "recovery_status": status,
            "interpretation": (
                "Relative statistical screening only; not a validated "
                "aviation risk prediction or confirmed conflict."
            ),
        })

        # Each high-indicator point becomes a candidate waypoint
        # for an exploratory lateral detour.
        for hotspot in hotspots:
            try:
                index = points.index(hotspot)
            except ValueError:
                continue

            lat, lon = hotspot["_lat"], hotspot["_lon"]

            # Estimate local direction from adjacent trajectory points.
            if len(points) >= 2:
                prev = points[max(0, index - 1)]
                nxt = points[min(len(points) - 1, index + 1)]
                direction = math.degrees(math.atan2(
                    (nxt["_lon"] - prev["_lon"])
                    * math.cos(math.radians(lat)),
                    nxt["_lat"] - prev["_lat"],
                ))
            else:
                direction = 0.0

            evidence = feature_evidence(hotspot)
            top_features = ";".join(
                f"{name}:{value:.1f}"
                for value, name in evidence[:3]
            )

            notam_status = (
                hotspot.get("notam_evidence_indicator") or ""
            )
            notam_numbers = hotspot.get("notam_numbers") or ""

            for distance_km in DETOUR_DISTANCES_KM:
                for side, bearing in [
                    ("LEFT_CANDIDATE", direction - 90),
                    ("RIGHT_CANDIDATE", direction + 90),
                ]:
                    new_lat, new_lon = offset_point(
                        lat, lon, bearing, distance_km
                    )

                    # Illustrative modified track: replace the hotspot
                    # point with a displaced waypoint. This does not
                    # prove that the resulting route avoids a hazard.
                    candidate_coords = list(original_coords)
                    candidate_coords[index] = (new_lat, new_lon)

                    candidate_distance = total_distance(candidate_coords)

                    route_candidates.append({
                        "flight_id": flight_id,
                        "hotspot_timestamp_utc":
                            hotspot.get("timestamp_utc", ""),
                        "hotspot_latitude": lat,
                        "hotspot_longitude": lon,
                        "relative_hazard_indicator":
                            round(hotspot["_score"], 2),
                        "dataset_hotspot_cutoff":
                            round(cutoff, 2),
                        "top_contributing_features": top_features,
                        "notam_evidence_status": notam_status,
                        "notam_numbers": notam_numbers,
                        "candidate_id":
                            f"{side}_{int(distance_km)}KM",
                        "candidate_waypoint_latitude":
                            round(new_lat, 6),
                        "candidate_waypoint_longitude":
                            round(new_lon, 6),
                        "lateral_offset_km": distance_km,
                        "original_track_distance_km":
                            round(original_distance, 2),
                        "modified_track_distance_km":
                            round(candidate_distance, 2),
                        "distance_change_km":
                            round(candidate_distance - original_distance, 2),
                        "route_status":
                            "EXPLORATORY_GEOMETRIC_CANDIDATE",
                        "operational_clearance":
                            "NOT_CHECKED",
                        "limitations": (
                            "Single waypoint displacement; not a validated "
                            "route. Airspace, terrain, aircraft performance, "
                            "altitude, actual weather avoidance and NOTAM "
                            "applicability are not validated."
                        ),
                    })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    def write_csv(path, data):
        if not data:
            print(f"No rows to write: {path}")
            return
        with path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=list(data[0].keys())
            )
            writer.writeheader()
            writer.writerows(data)

    write_csv(FLIGHT_OUTPUT, flight_assessments)
    write_csv(ROUTE_OUTPUT, route_candidates)

    report = {
        "project": "SkyRisk Auditor",
        "report_type": "prototype_recovery_decision_support",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_FILE),
        "flight_assessment_file": str(FLIGHT_OUTPUT),
        "route_candidate_file": str(ROUTE_OUTPUT),
        "flights_processed": len(flight_assessments),
        "flights_with_relative_hotspots": sum(
            f["hotspot_point_count"] > 0
            for f in flight_assessments
        ),
        "total_hotspot_points": sum(
            f["hotspot_point_count"]
            for f in flight_assessments
        ),
        "exploratory_route_candidates": len(route_candidates),
        "dataset_relative_hotspot_percentile": HOTSPOT_PERCENTILE,
        "calculated_hotspot_cutoff": round(cutoff, 4),
        "candidate_lateral_offsets_km": DETOUR_DISTANCES_KM,
        "limitations": [
            "Hotspots are relative percentiles from the available dataset.",
            "A high relative indicator is not a calibrated safety risk.",
            "Candidate paths are geometric illustrations, not flyable routes.",
            "No official airway, FIR, terrain, altitude or clearance validation.",
            "NOTAM candidates remain unconfirmed unless independently validated.",
            "Weather observations are grid estimates and not cruise-altitude data.",
            "No actual diversion or delay outcomes are inferred.",
        ],
    }

    with REPORT_OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\nSKYRISK RECOVERY DECISION SUPPORT COMPLETE")
    print(f"Flights processed: {report['flights_processed']}")
    print(
        "Flights with relative hotspots: "
        f"{report['flights_with_relative_hotspots']}"
    )
    print(f"Hotspot points: {report['total_hotspot_points']}")
    print(f"Route candidates: {report['exploratory_route_candidates']}")
    print(f"Dataset-derived hotspot cutoff: {cutoff:.2f}")
    print(f"\nFlight assessments:\n{FLIGHT_OUTPUT}")
    print(f"\nRoute candidates:\n{ROUTE_OUTPUT}")
    print(f"\nReport:\n{REPORT_OUTPUT}")
    print(
        "\nReminder: candidate routes are illustrative and are not "
        "approved or validated for actual flight."
    )


if __name__ == "__main__":
    main()

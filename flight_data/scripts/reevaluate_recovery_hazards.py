
import csv
import json
import math
import sys
from bisect import bisect_left, bisect_right
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CANDIDATE_FILE = (
    ROOT / "flight_data" / "processed"
    / "recovery_route_candidates_oct20_22.csv"
)
HAZARD_FILE = (
    ROOT / "flight_data" / "processed"
    / "hazard_indicators_oct20_22.csv"
)
OUTPUT_FILE = (
    ROOT / "flight_data" / "processed"
    / "recovery_hazard_reevaluation_oct20_22.csv"
)
REPORT_FILE = (
    ROOT / "flight_data" / "reports"
    / "recovery_hazard_reevaluation_report_oct20_22.json"
)

MAX_DISTANCE_KM = 30.0
MAX_TIME_GAP_MINUTES = 60.0
EARTH_RADIUS_KM = 6371.0


def log(message):
    print(message, flush=True)


def parse_time(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def first_value(row, names):
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return value
    return None


def as_float(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def haversine_km(lat1, lon1, lat2, lon2):
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1) * math.cos(p2)
        * math.sin(dlon / 2) ** 2
    )
    a = min(1.0, max(0.0, a))
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))



def get_candidate_details(row):
    # Use the displaced waypoint, NOT the original hotspot coordinates.
    timestamp = parse_time(first_value(
        row,
        ["hotspot_timestamp_utc", "candidate_timestamp_utc",
         "timestamp_utc", "timestamp", "original_timestamp_utc"]
    ))

    lat = as_float(first_value(
        row,
        ["candidate_waypoint_latitude", "candidate_latitude",
         "candidate_lat", "candidate_latitude_deg"]
    ))

    lon = as_float(first_value(
        row,
        ["candidate_waypoint_longitude", "candidate_longitude",
         "candidate_lon", "candidate_longitude_deg"]
    ))

    return timestamp, lat, lon


    lat = as_float(first_value(
        row, ["candidate_latitude", "candidate_lat",
              "candidate_latitude_deg", "latitude",
              "hotspot_latitude", "hotspot_lat",
              "original_latitude", "lat"]
    ))
    lon = as_float(first_value(
        row, ["candidate_longitude", "candidate_lon",
              "candidate_longitude_deg", "longitude",
              "hotspot_longitude", "hotspot_lon",
              "original_longitude", "lon"]
    ))

    # Some candidate files name the original hotspot explicitly.
    # If candidate coordinates were used above, fall back to hotspot
    # coordinates when necessary.
    if lat is None:
        lat = as_float(first_value(
            row, ["hotspot_latitude", "hotspot_lat", "original_latitude"]
        ))
    if lon is None:
        lon = as_float(first_value(
            row, ["hotspot_longitude", "hotspot_lon", "original_longitude"]
        ))

    return timestamp, lat, lon


def build_hazard_index(rows):
    points = []
    invalid = 0

    for row in rows:
        timestamp = parse_time(row.get("timestamp_utc"))
        lat = as_float(row.get("latitude"))
        lon = as_float(row.get("longitude"))
        indicator = as_float(row.get("relative_hazard_indicator"))

        if (
            timestamp is None or lat is None or lon is None
            or not (-90 <= lat <= 90)
            or not (-180 <= lon <= 180)
        ):
            invalid += 1
            continue

        points.append({
            "_time": timestamp,
            "_seconds": timestamp.timestamp(),
            "_lat": lat,
            "_lon": lon,
            "_indicator": indicator,
            "flight_id": row.get("flight_id", ""),
            "weather_match_status": row.get("weather_match_status", ""),
            "space_weather_match_status": row.get(
                "space_weather_match_status", ""
            ),
            "combined_coverage_status": row.get(
                "combined_coverage_status", ""
            ),
            "relative_hazard_indicator_status": row.get(
                "relative_hazard_indicator_status", ""
            ),
        })

    points.sort(key=lambda p: p["_seconds"])
    seconds = [p["_seconds"] for p in points]
    return points, seconds, invalid


def find_nearest_proxy(candidate, points, seconds):
    timestamp, lat, lon = get_candidate_details(candidate)

    if timestamp is None or lat is None or lon is None:
        return None, "INSUFFICIENT_CANDIDATE_TIME_OR_COORDINATES"

    center = timestamp.timestamp()
    gap_seconds = MAX_TIME_GAP_MINUTES * 60
    left = bisect_left(seconds, center - gap_seconds)
    right = bisect_right(seconds, center + gap_seconds)

    if left == right:
        return None, "INSUFFICIENT_DATA_NO_TIME_NEARBY_OBSERVATION"

    # Fast geographic bounding box before expensive haversine calculation.
    lat_delta = MAX_DISTANCE_KM / 110.5
    cos_lat = max(0.05, abs(math.cos(math.radians(lat))))
    lon_delta = MAX_DISTANCE_KM / (111.0 * cos_lat)

    best = None
    best_distance = float("inf")

    for i in range(left, right):
        point = points[i]

        if abs(point["_lat"] - lat) > lat_delta:
            continue
        if abs(point["_lon"] - lon) > lon_delta:
            continue

        distance = haversine_km(
            lat, lon, point["_lat"], point["_lon"]
        )
        if distance <= MAX_DISTANCE_KM and distance < best_distance:
            best = point
            best_distance = distance

    if best is None:
        return None, "INSUFFICIENT_DATA_NO_SPATIAL_TEMPORAL_MATCH"

    result = dict(best)
    result["_distance_km"] = best_distance
    result["_gap_minutes"] = abs(
        center - best["_seconds"]
    ) / 60.0

    return result, "NEARBY_FLIGHT_OBSERVATION_PROXY"


def main():
    log("SkyRisk recovery hazard reevaluation — optimized version")
    log(f"Reading candidates: {CANDIDATE_FILE}")
    candidates = read_csv(CANDIDATE_FILE)
    log(f"Candidates loaded: {len(candidates):,}")

    log(f"Reading hazard points: {HAZARD_FILE}")
    hazard_rows = read_csv(HAZARD_FILE)
    log(f"Hazard rows loaded: {len(hazard_rows):,}")

    points, seconds, invalid_hazards = build_hazard_index(hazard_rows)
    log(f"Valid indexed hazard points: {len(points):,}")
    log(f"Invalid hazard rows skipped: {invalid_hazards:,}")
    log("Starting candidate reevaluation...")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    counts = Counter()
    written = 0
    score_differences = []

    with OUTPUT_FILE.open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = None

        for number, candidate in enumerate(candidates, start=1):
            proxy, status = find_nearest_proxy(candidate, points, seconds)

            original_indicator = as_float(first_value(
                candidate,
                ["relative_hazard_indicator",
                 "hotspot_relative_hazard_indicator",
                 "original_relative_hazard_indicator"]
            ))

            proxy_indicator = proxy.get("_indicator") if proxy else None
            difference = (
                proxy_indicator - original_indicator
                if proxy_indicator is not None
                and original_indicator is not None
                else None
            )

            row = dict(candidate)
            row.update({
                "proxy_observation_status": status,
                "proxy_flight_id": proxy.get("flight_id", "") if proxy else "",
                "proxy_timestamp_utc": (
                    proxy["_time"].isoformat() if proxy else ""
                ),
                "proxy_latitude": proxy.get("_lat", "") if proxy else "",
                "proxy_longitude": proxy.get("_lon", "") if proxy else "",
                "proxy_distance_km": (
                    round(proxy["_distance_km"], 3) if proxy else ""
                ),
                "proxy_time_gap_minutes": (
                    round(proxy["_gap_minutes"], 3) if proxy else ""
                ),
                "proxy_relative_hazard_indicator": (
                    proxy_indicator if proxy_indicator is not None else ""
                ),
                "original_relative_hazard_indicator": (
                    original_indicator if original_indicator is not None else ""
                ),
                "proxy_minus_original_indicator": (
                    round(difference, 3) if difference is not None else ""
                ),
                "proxy_weather_match_status": (
                    proxy.get("weather_match_status", "") if proxy else ""
                ),
                "proxy_space_weather_match_status": (
                    proxy.get("space_weather_match_status", "") if proxy else ""
                ),
                "proxy_combined_coverage_status": (
                    proxy.get("combined_coverage_status", "") if proxy else ""
                ),
                "safety_validation_status": "NOT_VALIDATED",
                "operational_clearance": "NOT_CHECKED",
                "interpretation_note": (
                    "Nearby observation proxy only; this does not evaluate "
                    "the complete proposed route or establish safety."
                ),
            })

            if writer is None:
                writer = csv.DictWriter(
                    f, fieldnames=list(row.keys()), extrasaction="ignore"
                )
                writer.writeheader()

            writer.writerow(row)
            written += 1
            counts[status] += 1

            if difference is not None:
                score_differences.append(difference)

            if number % 500 == 0 or number == len(candidates):
                log(f"Progress: {number:,}/{len(candidates):,} candidates")

    report = {
        "module": "SkyRisk recovery hazard reevaluation",
        "method": "Time-indexed search, then spatial filtering and haversine",
        "candidate_input": str(CANDIDATE_FILE),
        "hazard_input": str(HAZARD_FILE),
        "output_csv": str(OUTPUT_FILE),
        "candidate_rows": len(candidates),
        "hazard_rows": len(hazard_rows),
        "valid_indexed_hazard_points": len(points),
        "invalid_hazard_rows_skipped": invalid_hazards,
        "output_rows": written,
        "maximum_time_gap_minutes": MAX_TIME_GAP_MINUTES,
        "maximum_distance_km": MAX_DISTANCE_KM,
        "status_counts": dict(counts),
        "proxy_indicator_difference_count": len(score_differences),
        "mean_proxy_minus_original_indicator": (
            round(sum(score_differences) / len(score_differences), 3)
            if score_differences else None
        ),
        "safety_validation": "NOT_VALIDATED",
        "operational_clearance": "NOT_CHECKED",
        "limitations": [
            "Nearby observations can belong to another flight.",
            "A nearby observation is a proxy, not a hazard measurement "
            "at the proposed route coordinate.",
            "This does not sample the entire candidate route.",
            "This does not validate airspace, terrain, altitude, airway, "
            "ATC, NOTAM applicability, or operational clearance.",
            "The relative hazard indicator is exploratory and is not "
            "a calibrated probability of aviation risk."
        ]
    }

    with REPORT_FILE.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    log("")
    log("REEVALUATION COMPLETE")
    log(f"Output rows: {written:,}")
    log(f"CSV: {OUTPUT_FILE}")
    log(f"Report: {REPORT_FILE}")
    log(f"Statuses: {dict(counts)}")
    log("Safety validation: NOT_VALIDATED")
    log("Operational clearance: NOT_CHECKED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log(f"ERROR: {type(exc).__name__}: {exc}")
        sys.exit(1)

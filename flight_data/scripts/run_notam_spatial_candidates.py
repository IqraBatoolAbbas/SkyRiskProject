
import csv
import json
import math
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "flight_data" / "processed"
REPORTS = ROOT / "flight_data" / "reports"

DECISIONS = PROCESSED / "notam_decisions_oct20_22.csv"
AIRPORTS = PROCESSED / "notam_airport_coordinate_candidates.csv"

OUTPUT = PROCESSED / "notam_spatial_candidates_oct20_22.csv"
REPORT = REPORTS / "notam_spatial_candidates_report.json"

# Exploratory threshold only; not an aviation safety threshold.
RADIUS_KM = 25.0

def distance_km(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance using the haversine formula."""
    earth_radius_km = 6371.0088

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    )
    a = min(1.0, max(0.0, a))
    return 2 * earth_radius_km * math.asin(math.sqrt(a))


for path in (DECISIONS, AIRPORTS):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

# Load only uniquely mapped airport reference points.
airport_map = {}
with AIRPORTS.open("r", encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        code = (row.get("ident") or "").strip().upper()
        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
        except (ValueError, TypeError, KeyError):
            continue

        if code:
            airport_map[code] = {
                "name": row.get("name", ""),
                "latitude": lat,
                "longitude": lon,
                "source": row.get("source", "OurAirports"),
            }

REPORTS.mkdir(parents=True, exist_ok=True)

counts = Counter()
unmatched_codes = set()
candidate_flights = set()
candidate_notams = set()
minimum_distance = {}

output_fields = [
    "flight_id", "callsign", "icao_type",
    "point_timestamp_utc", "latitude", "longitude", "altitude_ft",
    "notam_number", "notam_location", "notam_effective_start_utc",
    "notam_effective_end_utc", "decision", "decision_reason",
    "airport_name", "airport_latitude", "airport_longitude",
    "distance_to_airport_km", "candidate_radius_km",
    "evidence_status",
]

with DECISIONS.open("r", encoding="utf-8-sig", newline="") as src:
    reader = csv.DictReader(src)
    required = {
        "flight_id", "point_timestamp_utc", "latitude", "longitude",
        "notam_location", "notam_number", "decision",
    }
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"Required columns missing: {sorted(missing)}")

    with OUTPUT.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=output_fields)
        writer.writeheader()

        for row in reader:
            counts["input_decision_rows"] += 1

            code = (row.get("notam_location") or "").strip().upper()
            decision = (row.get("decision") or "").strip()

            if decision == "REJECTED_TIME":
                counts["rejected_time_rows_skipped"] += 1
                continue

            airport = airport_map.get(code)
            if airport is None:
                if code:
                    unmatched_codes.add(code)
                counts["rows_without_airport_coordinate"] += 1
                continue

            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Coordinates outside valid range")
            except (ValueError, TypeError, KeyError):
                counts["rows_with_invalid_coordinates"] += 1
                continue

            dist = distance_km(
                lat, lon,
                airport["latitude"], airport["longitude"]
            )

            old = minimum_distance.get(code)
            if old is None or dist < old:
                minimum_distance[code] = dist

            counts["coordinate_comparisons"] += 1

            if dist > RADIUS_KM:
                continue

            counts["spatial_candidate_rows"] += 1
            candidate_flights.add(row.get("flight_id", ""))
            candidate_notams.add(
                (row.get("notam_number", ""), code)
            )

            result = {
                key: row.get(key, "")
                for key in [
                    "flight_id", "callsign", "icao_type",
                    "point_timestamp_utc", "latitude", "longitude",
                    "altitude_ft", "notam_number", "notam_location",
                    "notam_effective_start_utc", "notam_effective_end_utc",
                    "decision", "decision_reason",
                ]
            }
            result.update({
                "airport_name": airport["name"],
                "airport_latitude": airport["latitude"],
                "airport_longitude": airport["longitude"],
                "distance_to_airport_km": round(dist, 3),
                "candidate_radius_km": RADIUS_KM,
                "evidence_status": (
                    "SPATIAL_AND_PRIOR_DECISION_CANDIDATE_NOT_VALIDATED"
                ),
            })
            writer.writerow(result)

report = {
    "engine": "notam_spatial_candidate_screen_v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "input_decisions": str(DECISIONS),
    "airport_reference": str(AIRPORTS),
    "airport_coordinate_source": (
        "https://davidmegginson.github.io/ourairports-data/airports.csv"
    ),
    "exploratory_radius_km": RADIUS_KM,
    "counts": dict(counts),
    "unique_candidate_flights": len(candidate_flights),
    "unique_candidate_notam_location_pairs": len(candidate_notams),
    "unmatched_location_codes": sorted(unmatched_codes),
    "closest_observed_point_to_each_mapped_airport_km": {
        code: round(dist, 3)
        for code, dist in sorted(minimum_distance.items())
    },
    "limitations": [
        "25 km is an exploratory screening radius, not an operational threshold.",
        "Airport reference points are not runway coordinates.",
        "Nearby trajectory points do not prove airport arrival or departure.",
        "A spatial candidate does not prove that a NOTAM affected a flight.",
        "OPKR and OPLR remain unmatched unless a verified reference is added.",
        "No validated operational-impact matches are created.",
        "Source decision CSV, airport reference CSV and database are not modified.",
    ],
}

REPORT.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("\nSPATIAL CANDIDATE SCREEN COMPLETE")
for key, value in counts.items():
    print(f"{key}: {value}")
print("Unique candidate flights:", len(candidate_flights))
print("Unique NOTAM/location pairs with candidate points:", len(candidate_notams))
print("Unmatched location codes:", sorted(unmatched_codes))
print("CSV:", OUTPUT)
print("Report:", REPORT)
print("No database writes performed.")


"""
SkyRisk Auditor - Recovery Candidate Comparison
Standard-library version: does not require pandas.

Selects the minimum-distance geometric candidate for each hotspot.
This does not validate aviation safety or operational clearance.
"""

from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import csv
import json
import statistics


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT / "flight_data" / "processed"
    / "recovery_route_candidates_oct20_22.csv"
)
OUTPUT_DIR = ROOT / "flight_data" / "processed"
REPORT_DIR = ROOT / "flight_data" / "reports"

HOTSPOT_OUT = (
    OUTPUT_DIR / "recovery_hotspot_candidate_comparison_oct20_22.csv"
)
FLIGHT_OUT = (
    OUTPUT_DIR / "recovery_candidate_flight_summary_oct20_22.csv"
)
REPORT_OUT = (
    REPORT_DIR / "recovery_candidate_comparison_report_oct20_22.json"
)

REQUIRED = [
    "flight_id",
    "hotspot_timestamp_utc",
    "relative_hazard_indicator",
    "candidate_id",
    "hotspot_latitude",
    "hotspot_longitude",
    "candidate_waypoint_latitude",
    "candidate_waypoint_longitude",
    "original_track_distance_km",
    "modified_track_distance_km",
    "distance_change_km",
    "route_status",
]


def number(value):
    try:
        result = float(value)
        return result if result == result else None
    except (TypeError, ValueError):
        return None


def rounded(value, digits=2):
    return round(value, digits) if value is not None else ""


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {INPUT_FILE}\n"
            "Run recovery_decision_support.py first."
        )

    with INPUT_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        missing = [
            name for name in REQUIRED
            if name not in (reader.fieldnames or [])
        ]
        if missing:
            raise ValueError(
                "Missing CSV columns: " + ", ".join(missing)
            )

        records = list(reader)

    if not records:
        raise ValueError("Input candidate CSV is empty.")

    valid = []
    for row in records:
        distance_change = number(row.get("distance_change_km"))
        modified_distance = number(
            row.get("modified_track_distance_km")
        )
        original_distance = number(
            row.get("original_track_distance_km")
        )

        if (
            not row.get("flight_id")
            or not row.get("hotspot_timestamp_utc")
            or not row.get("candidate_id")
            or distance_change is None
            or modified_distance is None
            or original_distance is None
        ):
            continue

        row["_distance_change"] = distance_change
        row["_modified_distance"] = modified_distance
        row["_original_distance"] = original_distance
        row["_indicator"] = number(
            row.get("relative_hazard_indicator")
        )
        valid.append(row)

    if not valid:
        raise ValueError("No valid candidate records found.")

    # Group candidates by flight and hotspot timestamp.
    hotspot_groups = defaultdict(list)
    flight_groups = defaultdict(list)

    for row in valid:
        hotspot_key = (
            row["flight_id"],
            row["hotspot_timestamp_utc"],
        )
        hotspot_groups[hotspot_key].append(row)
        flight_groups[row["flight_id"]].append(row)

    hotspot_rows = []

    for (flight_id, timestamp), options in sorted(
        hotspot_groups.items()
    ):
        # Minimum detour, with modified distance as tie-breaker.
        best = min(
            options,
            key=lambda row: (
                row["_distance_change"],
                row["_modified_distance"],
            ),
        )

        hotspot_rows.append({
            "flight_id": flight_id,
            "hotspot_timestamp_utc": timestamp,
            "relative_hazard_indicator": rounded(
                best["_indicator"]
            ),
            "candidate_options_evaluated": len(options),
            "minimum_detour_candidate_id": best["candidate_id"],
            "hotspot_latitude": best["hotspot_latitude"],
            "hotspot_longitude": best["hotspot_longitude"],
            "selected_waypoint_latitude":
                best["candidate_waypoint_latitude"],
            "selected_waypoint_longitude":
                best["candidate_waypoint_longitude"],
            "original_track_distance_km": rounded(
                best["_original_distance"]
            ),
            "selected_modified_track_distance_km": rounded(
                best["_modified_distance"]
            ),
            "minimum_geometric_distance_change_km": rounded(
                best["_distance_change"]
            ),
            "comparison_status":
                "MINIMUM_DISTANCE_GEOMETRIC_OPTION_ONLY",
            "safety_validation_status": "NOT_VALIDATED",
            "operational_clearance": "NOT_CHECKED",
        })

    with HOTSPOT_OUT.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=list(hotspot_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(hotspot_rows)

    # Build one summary row per flight.
    flight_rows = []

    for flight_id, group in flight_groups.items():
        selected = [
            row for row in hotspot_rows
            if row["flight_id"] == flight_id
        ]

        detours = [
            float(row["minimum_geometric_distance_change_km"])
            for row in selected
            if row["minimum_geometric_distance_change_km"] != ""
        ]

        indicators = [
            row["_indicator"] for row in group
            if row["_indicator"] is not None
        ]

        flight_rows.append({
            "flight_id": flight_id,
            "hotspot_count": len(selected),
            "candidate_records_evaluated": len(group),
            "original_track_distance_km": rounded(
                group[0]["_original_distance"]
            ),
            "mean_minimum_geometric_detour_km": rounded(
                statistics.mean(detours) if detours else None
            ),
            "max_minimum_geometric_detour_km": rounded(
                max(detours) if detours else None
            ),
            "relative_indicator_max": rounded(
                max(indicators) if indicators else None
            ),
            "safety_validation_status": "NOT_VALIDATED",
            "operational_clearance": "NOT_CHECKED",
        })

    flight_rows.sort(
        key=lambda row: (
            number(row["relative_indicator_max"])
            if number(row["relative_indicator_max"]) is not None
            else -1
        ),
        reverse=True,
    )

    with FLIGHT_OUT.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=list(flight_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(flight_rows)

    report = {
        "project": "SkyRisk Auditor",
        "module": "Recovery Candidate Comparison and Audit",
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "input_file": str(INPUT_FILE),
        "input_records": len(records),
        "valid_candidate_records": len(valid),
        "unique_flights": len(flight_groups),
        "unique_hotspots": len(hotspot_groups),
        "outputs": {
            "hotspot_comparison_csv": str(HOTSPOT_OUT),
            "flight_summary_csv": str(FLIGHT_OUT),
        },
        "selection_rule": (
            "Minimum distance change, then minimum modified distance"
        ),
        "interpretation": (
            "Geometric comparison only; no claim of reduced hazard."
        ),
        "safety_validation_status": "NOT_VALIDATED",
        "operational_clearance": "NOT_CHECKED",
        "not_performed": [
            "Hazard re-evaluation along modified route",
            "Official airway/FIR validation",
            "Terrain and altitude checks",
            "NOTAM applicability validation",
            "ATC clearance validation",
        ],
    }

    with REPORT_OUT.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\nSKYRISK RECOVERY CANDIDATE COMPARISON COMPLETE")
    print(f"Input records: {len(records):,}")
    print(f"Valid candidate records: {len(valid):,}")
    print(f"Flights: {len(flight_groups):,}")
    print(f"Hotspots compared: {len(hotspot_groups):,}")
    print(f"\nHotspot CSV: {HOTSPOT_OUT}")
    print(f"Flight summary CSV: {FLIGHT_OUT}")
    print(f"JSON report: {REPORT_OUT}")
    print("\nSafety validation: NOT_VALIDATED")
    print("Operational clearance: NOT_CHECKED")


if __name__ == "__main__":
    main()

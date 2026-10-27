
import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REEVALUATION_FILE = (
    ROOT / "flight_data" / "processed"
    / "recovery_hazard_reevaluation_oct20_22.csv"
)
OUTPUT_DIR = ROOT / "flight_data" / "processed"
REPORT_DIR = ROOT / "flight_data" / "reports"

SUMMARY_CSV = OUTPUT_DIR / "recovery_evaluation_summary_oct20_22.csv"
REPORT_JSON = REPORT_DIR / "recovery_evaluation_report_oct20_22.json"

CANDIDATES = [
    "LEFT_CANDIDATE_15KM",
    "RIGHT_CANDIDATE_15KM",
    "LEFT_CANDIDATE_25KM",
    "RIGHT_CANDIDATE_25KM",
]


def number(row, field):
    value = row.get(field, "")
    if value is None or str(value).strip() == "":
        return None
    try:
        result = float(value)
        return result if result == result else None
    except (TypeError, ValueError):
        return None


def median(values):
    return round(statistics.median(values), 3) if values else None


def main():
    if not REEVALUATION_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {REEVALUATION_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    grouped = defaultdict(list)
    total_rows = 0

    with REEVALUATION_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.DictReader(file):
            total_rows += 1
            grouped[row.get("candidate_id", "UNKNOWN")].append(row)

    summary_rows = []
    candidate_reports = []

    for candidate in CANDIDATES:
        rows = grouped.get(candidate, [])

        differences = [
            value for row in rows
            if (value := number(
                row, "proxy_minus_original_indicator"
            )) is not None
        ]

        distances = [
            value for row in rows
            if (value := number(row, "proxy_distance_km")) is not None
        ]

        time_gaps = [
            value for row in rows
            if (value := number(
                row, "proxy_time_gap_minutes"
            )) is not None
        ]

        lower = sum(value < 0 for value in differences)
        same = sum(value == 0 for value in differences)
        higher = sum(value > 0 for value in differences)

        statuses = defaultdict(int)
        for row in rows:
            status = row.get("reevaluation_status", "").strip()
            statuses[status or "MISSING_STATUS"] += 1

        item = {
            "candidate_id": candidate,
            "total_records": len(rows),
            "valid_indicator_comparisons": len(differences),
            "indicator_lower_count": lower,
            "indicator_same_count": same,
            "indicator_higher_count": higher,
            "indicator_lower_percent": round(
                100 * lower / len(differences), 2
            ) if differences else None,
            "median_proxy_distance_km": median(distances),
            "median_proxy_time_gap_minutes": median(time_gaps),
            "mean_indicator_difference": round(
                statistics.mean(differences), 3
            ) if differences else None,
            "reevaluation_status_counts": dict(statuses),
        }

        candidate_reports.append(item)
        summary_rows.append({
            key: value for key, value in item.items()
            if key != "reevaluation_status_counts"
        })

    with SUMMARY_CSV.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        if summary_rows:
            writer = csv.DictWriter(
                file, fieldnames=list(summary_rows[0].keys())
            )
            writer.writeheader()
            writer.writerows(summary_rows)

    report = {
        "project": "SkyRisk Auditor",
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "input_file": str(REEVALUATION_FILE.relative_to(ROOT)),
        "input_records": total_rows,
        "candidate_types": candidate_reports,
        "interpretation": {
            "purpose": (
                "Exploratory comparison of nearby flight-observation "
                "proxies for recovery waypoint candidates."
            ),
            "safety_validation": "NOT_VALIDATED",
            "operational_clearance": "NOT_CHECKED",
            "proxy_is_actual_candidate_weather": False,
            "full_route_hazard_validation": False,
            "limitations": [
                "Nearby observations may belong to different flights.",
                "Proxy indicator is not a calibrated safety probability.",
                "Candidate comparisons do not establish a safe route.",
                "Airway, FIR, altitude, terrain, ATC and NOTAM clearance "
                "are not validated by this evaluation."
            ],
        },
    }

    with REPORT_JSON.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("RECOVERY EVALUATION COMPLETE")
    print(f"Input records: {total_rows}")
    print(f"Summary CSV: {SUMMARY_CSV}")
    print(f"JSON report: {REPORT_JSON}")
    print("Safety validation: NOT_VALIDATED")
    print("Operational clearance: NOT_CHECKED")


if __name__ == "__main__":
    main()

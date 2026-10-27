
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import json

# SkyRisk Auditor
# Integrates existing flight, weather, space-weather and NOTAM evidence.
# This script does NOT invent a risk score or confirm operational impacts.

ROOT = Path(__file__).resolve().parents[2]

FLIGHT_FILE = (
    ROOT / "backend" / "weather_module" / "processed"
    / "combined_hazard_coverage_audit_oct20_22.csv"
)
NOTAM_FILE = (
    ROOT / "flight_data" / "processed"
    / "notam_spatial_candidates_oct20_22.csv"
)

OUTPUT_DIR = ROOT / "flight_data" / "processed"
REPORT_DIR = ROOT / "flight_data" / "reports"

OUTPUT_FILE = OUTPUT_DIR / "multihazard_dataset_oct20_22.csv"
REPORT_FILE = REPORT_DIR / "multihazard_dataset_report_oct20_22.json"


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def clean(value):
    return (value or "").strip()


def main():
    flight_rows = read_csv(FLIGHT_FILE)
    notam_rows = read_csv(NOTAM_FILE)

    if not flight_rows:
        raise ValueError("Combined flight-hazard CSV is empty.")

    required_flight_columns = {
        "flight_id",
        "timestamp_utc",
        "latitude",
        "longitude",
        "weather_match_status",
        "space_weather_match_status",
        "combined_coverage_status",
    }

    missing = required_flight_columns - set(flight_rows[0])
    if missing:
        raise ValueError(
            f"Missing flight-hazard columns: {sorted(missing)}"
        )

    required_notam_columns = {
        "flight_id",
        "point_timestamp_utc",
        "notam_number",
        "decision",
        "decision_reason",
        "evidence_status",
    }

    if notam_rows:
        missing = required_notam_columns - set(notam_rows[0])
        if missing:
            raise ValueError(
                f"Missing NOTAM columns: {sorted(missing)}"
            )

    # Index NOTAM evidence by flight ID.
    notams_by_flight = defaultdict(list)

    for row in notam_rows:
        flight_id = clean(row.get("flight_id"))
        if flight_id:
            notams_by_flight[flight_id].append(row)

    output_rows = []
    coverage_counts = Counter()
    notam_status_counts = Counter()
    exact_link_count = 0

    combined_keys = {
        (
            clean(row.get("flight_id")),
            clean(row.get("timestamp_utc")),
        )
        for row in flight_rows
    }

    unmatched_notam_rows = sum(
        (
            clean(row.get("flight_id")),
            clean(row.get("point_timestamp_utc")),
        ) not in combined_keys
        for row in notam_rows
    )

    for flight in flight_rows:
        flight_id = clean(flight.get("flight_id"))
        timestamp = clean(flight.get("timestamp_utc"))

        coverage = clean(
            flight.get("combined_coverage_status")
        ) or "MISSING_COVERAGE_STATUS"

        coverage_counts[coverage] += 1

        # Link only when both flight ID and timestamp match exactly.
        candidates = [
            row
            for row in notams_by_flight.get(flight_id, [])
            if clean(row.get("point_timestamp_utc")) == timestamp
        ]

        if candidates:
            exact_link_count += len(candidates)
            link_status = "EXACT_FLIGHT_POINT_CANDIDATE_LINK"
            notam_status = "UNCONFIRMED_NOTAM_CANDIDATE"
        elif flight_id in notams_by_flight:
            link_status = "NO_EXACT_POINT_CANDIDATE_LINK"
            notam_status = "NO_EXACT_POINT_CANDIDATE_LINK"
        else:
            link_status = "NO_NOTAM_CANDIDATE_FOR_FLIGHT"
            notam_status = "NO_NOTAM_CANDIDATE_FOR_FLIGHT"

        numbers = sorted({
            clean(row.get("notam_number"))
            for row in candidates
            if clean(row.get("notam_number"))
        })

        locations = sorted({
            clean(row.get("notam_location"))
            for row in candidates
            if clean(row.get("notam_location"))
        })

        decisions = sorted({
            clean(row.get("decision"))
            for row in candidates
            if clean(row.get("decision"))
        })

        evidence = sorted({
            clean(row.get("evidence_status"))
            for row in candidates
            if clean(row.get("evidence_status"))
        })

        reasons = sorted({
            clean(row.get("decision_reason"))
            for row in candidates
            if clean(row.get("decision_reason"))
        })

        notam_status_counts[notam_status] += 1

        result = dict(flight)

        result.update({
            "notam_link_status": link_status,
            "notam_candidate_status": notam_status,
            "notam_candidate_count": len(candidates),
            "notam_numbers": ";".join(numbers),
            "notam_locations": ";".join(locations),
            "notam_candidate_decisions": ";".join(decisions),
            "notam_evidence_statuses": ";".join(evidence),
            "notam_candidate_reasons": " | ".join(reasons),

            # Deliberately not calculated in this integration step.
            "risk_score": "",
            "risk_level": "NOT_CALCULATED",
            "operational_impact_status": "NOT_VERIFIED",

            "risk_assessment_note": (
                "Preliminary data integration only. Weather values are "
                "grid estimates, Kp is a global preliminary index, and "
                "NOTAM candidates are not confirmed operational impacts."
            ),
        })

        output_rows.append(result)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    extra_columns = [
        "notam_link_status",
        "notam_candidate_status",
        "notam_candidate_count",
        "notam_numbers",
        "notam_locations",
        "notam_candidate_decisions",
        "notam_evidence_statuses",
        "notam_candidate_reasons",
        "risk_score",
        "risk_level",
        "operational_impact_status",
        "risk_assessment_note",
    ]

    columns = list(flight_rows[0].keys())
    columns.extend(
        column for column in extra_columns
        if column not in columns
    )

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(output_rows)

    report = {
        "project": "SkyRisk Auditor",
        "report_type": "preliminary_multihazard_integration",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_files": {
            "flight_weather_space_weather": str(FLIGHT_FILE),
            "notam_candidates": str(NOTAM_FILE),
        },
        "output_file": str(OUTPUT_FILE),
        "counts": {
            "flight_hazard_rows": len(flight_rows),
            "unique_flight_point_keys": len(combined_keys),
            "notam_candidate_rows": len(notam_rows),
            "output_rows": len(output_rows),
            "exact_point_candidate_links": exact_link_count,
            "notam_rows_without_exact_point_link": unmatched_notam_rows,
        },
        "coverage_status_counts": dict(coverage_counts),
        "notam_status_counts": dict(notam_status_counts),
        "limitations": [
            "This step does not calculate a risk score.",
            "Weather values are grid estimates, not exact aircraft-local observations.",
            "Weather variables are not cruise-altitude measurements.",
            "Kp is a global space-weather index, not direct evidence of flight impact.",
            "NOTAM candidates are not confirmed operational impacts.",
            "A missing NOTAM candidate does not prove that no NOTAM applies.",
            "Only exact flight ID and timestamp matches are linked.",
            "Original input files are not modified.",
        ],
    }

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\nMULTI-HAZARD DATASET BUILD COMPLETE")
    print(f"Flight-hazard rows: {len(flight_rows)}")
    print(f"NOTAM candidate rows: {len(notam_rows)}")
    print(f"Exact point candidate links: {exact_link_count}")
    print(f"NOTAM rows without exact point link: {unmatched_notam_rows}")
    print(f"\nOutput CSV:\n{OUTPUT_FILE}")
    print(f"\nReport JSON:\n{REPORT_FILE}")
    print("\nCoverage:")
    for key, value in sorted(coverage_counts.items()):
        print(f"  {key}: {value}")

    print("\nNOTAM status:")
    for key, value in sorted(notam_status_counts.items()):
        print(f"  {key}: {value}")

    print("\nRisk score was not calculated in this step.")


if __name__ == "__main__":
    main()

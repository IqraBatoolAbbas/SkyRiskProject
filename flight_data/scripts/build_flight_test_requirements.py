
import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "flight_data"
    / "reports"
    / "notam_requirements_report.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "flight_data"
    / "reports"
    / "flight_test_requirements.json"
)

# Manually selected NOTAMs for the first matching tests.
TEST_CASES = [
    {
        "test_id": "RUNWAY_RESTRICTION_OPKC",
        "location_code": "OPKC",
        "notam_number": "A0541/26",
        "purpose": "Test airport-area trajectory matching for a runway restriction.",
        "required_checks": [
            "flight timestamp overlaps NOTAM effective window",
            "aircraft position is near the airport",
            "flight track and altitude are available if possible",
        ],
    },
    {
        "test_id": "RUNWAY_CLOSURE_OPSD",
        "location_code": "OPSD",
        "notam_number": "A0596/26",
        "purpose": "Test airport-area trajectory matching for a runway closure.",
        "required_checks": [
            "flight timestamp overlaps NOTAM effective window",
            "aircraft position is near the airport",
            "do not assume the aircraft used the closed runway",
        ],
    },
    {
        "test_id": "SURVEILLANCE_OUTAGE_OPKR",
        "location_code": "OPKR",
        "notam_number": "A0595/26",
        "purpose": "Identify available trajectory data during a surveillance outage.",
        "required_checks": [
            "flight timestamp overlaps NOTAM effective window",
            "check timestamp gaps and position availability",
            "do not treat missing ADS-B points as proof of no flight",
        ],
    },
]


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input report not found: {INPUT_FILE}\n"
            "Run inspect_notam_requirements.py first."
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        report = json.load(file)

    notams = report.get("notams", [])
    index = {
        (item.get("location_code"), item.get("notam_number")): item
        for item in notams
    }

    matched_tests = []
    unmatched_tests = []

    for test in TEST_CASES:
        key = (test["location_code"], test["notam_number"])
        notam = index.get(key)

        if not notam:
            unmatched_tests.append({
                **test,
                "match_status": "NOT_FOUND_IN_REPORT",
            })
            continue

        matched_tests.append({
            **test,
            "match_status": "FOUND_IN_REPORT",
            "notam_status": notam.get("status"),
            "effective_start": notam.get("effective_start"),
            "effective_end": notam.get("effective_end"),
            "notam_text": notam.get("notam_text"),
            "trajectory_data_available": "NOT_CHECKED",
            "operational_applicability": "UNKNOWN",
        })

    location_counts = Counter(
        item.get("location_code") or "UNKNOWN"
        for item in notams
    )

    output = {
        "purpose": (
            "Define preliminary tests for matching flight trajectories "
            "against selected NOTAM records."
        ),
        "source_report": str(INPUT_FILE),
        "read_only": True,
        "required_flight_fields": [
            "timestamp",
            "latitude",
            "longitude",
            "altitude",
            "ground_speed",
            "track_or_heading",
            "flight_or_aircraft_identifier",
        ],
        "notam_record_count": len(notams),
        "location_codes_in_report": dict(location_counts),
        "matched_test_count": len(matched_tests),
        "unmatched_test_count": len(unmatched_tests),
        "tests": matched_tests,
        "unmatched_tests": unmatched_tests,
        "limitations": [
            "This script does not download or inspect flight trajectories.",
            "A nearby aircraft position does not prove runway usage.",
            "A NOTAM match does not by itself prove operational impact.",
            "Missing ADS-B observations do not prove no aircraft was present.",
        ],
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    print("\n===== FLIGHT TEST REQUIREMENTS =====")
    print(f"NOTAM records read: {len(notams)}")
    print(f"Tests matched: {len(matched_tests)}")
    print(f"Tests not found: {len(unmatched_tests)}")

    for item in matched_tests:
        print(
            f"\n{item['test_id']}: "
            f"{item['location_code']} / {item['notam_number']}"
        )
        print(f"  Status: {item['notam_status']}")
        print(f"  Starts: {item['effective_start']}")
        print(f"  Ends:   {item['effective_end']}")

    print(f"\nReport saved to:\n{OUTPUT_FILE}")
    print("\nNo database changes were made.")


if __name__ == "__main__":
    main()

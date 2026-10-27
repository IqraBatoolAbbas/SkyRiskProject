
import csv
import json
from pathlib import Path
from datetime import datetime, timezone

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
FLIGHT_DATA_DIR = PROJECT_DIR / "flight_data" / "processed"
WEATHER_REPORT_DIR = BACKEND_DIR / "weather_module" / "reports"


def read_csv_count(path):
    if not path.is_file():
        return None

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return sum(1 for _ in csv.DictReader(file))


def read_json(path):
    if not path.is_file():
        return None

    try:
        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


def get_dashboard_overview():
    notams = read_json(BACKEND_DIR / "notam_validation_report.json")
    weather = read_json(
        WEATHER_REPORT_DIR / "flight_weather_match_report.json"
    )
    space_weather = read_json(
        WEATHER_REPORT_DIR / "flight_space_weather_match_report.json"
    )
    hazard_quality = read_json(
        WEATHER_REPORT_DIR / "combined_hazard_quality_report_oct20_22.json"
    )

    flight_count = read_csv_count(
        FLIGHT_DATA_DIR / "recovery_flight_assessment_oct20_22.csv"
    )
    candidate_count = read_csv_count(
        FLIGHT_DATA_DIR / "recovery_route_candidates_oct20_22.csv"
    )

    valid_notams = notams if isinstance(notams, list) else []
    notam_count = len(valid_notams)

    matched_weather = (
        weather.get("matched_flight_points")
        if weather else None
    )
    matched_space_weather = (
        space_weather.get("matched_flight_points")
        if space_weather else None
    )

    return {
        "status": "success",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "SkyRisk Auditor",
        "data_mode": "Historical research datasets",
        "metrics": {
            "flight_assessments": flight_count,
            "recovery_candidates": candidate_count,
            "notam_records": notam_count,
            "notams_with_validation_issues": sum(
                bool(item.get("validation_issues"))
                for item in valid_notams
            ),
            "weather_matched_points": matched_weather,
            "space_weather_matched_points": matched_space_weather,
            "combined_hazard_rows": (
                hazard_quality.get("total_rows")
                if hazard_quality else None
            ),
        },
        "sources": {
            "notam": {
                "available": notams is not None,
                "name": "NOTAC validation report",
            },
            "weather": {
                "available": weather is not None,
                "name": "Open-Meteo historical weather match report",
            },
            "space_weather": {
                "available": space_weather is not None,
                "name": "GFZ/NOAA space-weather match report",
            },
            "recovery_dataset": {
                "available": flight_count is not None,
                "name": "Historical recovery assessment CSV",
            },
        },
        "validation": {
            "operational_safety_validated": False,
            "live_monitoring_enabled": False,
            "note": (
                "Historical research metrics only. These counts do not "
                "represent live flights or validated operational risk."
            ),
        },
    }

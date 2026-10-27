
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "flight_data" / "processed"

CANDIDATE_FILE = (
    PROCESSED_DIR / "recovery_route_candidates_oct20_22.csv"
)
REEVALUATION_FILE = (
    PROCESSED_DIR / "recovery_hazard_reevaluation_oct20_22.csv"
)
FLIGHT_FILE = (
    PROCESSED_DIR / "recovery_flight_assessment_oct20_22.csv"
)
SUMMARY_FILE = (
    PROCESSED_DIR / "recovery_evaluation_summary_oct20_22.csv"
)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(f"Required dataset not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def read_number(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def public_candidate(row):
    """Return a documented, JSON-compatible candidate record."""
    numeric_fields = {
        "hotspot_latitude",
        "hotspot_longitude",
        "relative_hazard_indicator",
        "dataset_hotspot_cutoff",
        "candidate_waypoint_latitude",
        "candidate_waypoint_longitude",
        "lateral_offset_km",
        "original_track_distance_km",
        "modified_track_distance_km",
        "distance_change_km",
        "proxy_latitude",
        "proxy_longitude",
        "proxy_distance_km",
        "proxy_time_gap_minutes",
        "proxy_relative_hazard_indicator",
        "original_relative_hazard_indicator",
        "proxy_minus_original_indicator",
    }

    result = {}
    for key, value in row.items():
        if key in numeric_fields:
            result[key] = read_number(value)
        else:
            result[key] = value if value != "" else None

    result["safety_validation_status"] = "NOT_VALIDATED"
    result["operational_clearance"] = "NOT_CHECKED"
    result["is_operationally_approved"] = False

    return result


def get_recovery_summary():
    flight_rows = read_csv(FLIGHT_FILE)
    evaluation_rows = read_csv(SUMMARY_FILE)

    return {
        "status": "success",
        "project": "SkyRisk Auditor",
        "dataset_period": "2026-10-20 to 2026-10-22",
        "flight_assessment_count": len(flight_rows),
        "recovery_candidate_evaluation": [
            {
                "candidate_id": row["candidate_id"],
                "total_records": int(row["total_records"]),
                "valid_indicator_comparisons": int(
                    row["valid_indicator_comparisons"]
                ),
                "indicator_lower_count": int(
                    row["indicator_lower_count"]
                ),
                "indicator_same_count": int(
                    row["indicator_same_count"]
                ),
                "indicator_higher_count": int(
                    row["indicator_higher_count"]
                ),
                "indicator_lower_percent": read_number(
                    row["indicator_lower_percent"]
                ),
                "median_proxy_distance_km": read_number(
                    row["median_proxy_distance_km"]
                ),
                "median_proxy_time_gap_minutes": read_number(
                    row["median_proxy_time_gap_minutes"]
                ),
                "mean_indicator_difference": read_number(
                    row["mean_indicator_difference"]
                ),
            }
            for row in evaluation_rows
        ],
        "safety_validation_status": "NOT_VALIDATED",
        "operational_clearance": "NOT_CHECKED",
        "interpretation": (
            "Exploratory statistical comparison only. Proxy observations "
            "do not establish alternate-route safety."
        ),
    }


def get_flight_recovery(flight_id):
    candidate_rows = read_csv(CANDIDATE_FILE)
    reevaluation_rows = read_csv(REEVALUATION_FILE)
    flight_rows = read_csv(FLIGHT_FILE)

    assessment = next(
        (row for row in flight_rows if row["flight_id"] == flight_id),
        None,
    )

    if assessment is None:
        return None

    candidates = [
        public_candidate(row)
        for row in candidate_rows
        if row.get("flight_id") == flight_id
    ]

    reevaluations = [
        public_candidate(row)
        for row in reevaluation_rows
        if row.get("flight_id") == flight_id
    ]

    return {
        "status": "success",
        "flight_id": flight_id,
        "flight_assessment": assessment,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "hazard_proxy_reevaluations": reevaluations,
        "safety_validation_status": "NOT_VALIDATED",
        "operational_clearance": "NOT_CHECKED",
        "warning": (
            "These are exploratory single-waypoint geometric candidates. "
            "Nearby flight observations are proxies, not actual weather "
            "measurements at every proposed waypoint. Complete-route "
            "airspace, terrain, altitude, ATC, aircraft-performance and "
            "NOTAM applicability checks have not been validated."
        ),
    }

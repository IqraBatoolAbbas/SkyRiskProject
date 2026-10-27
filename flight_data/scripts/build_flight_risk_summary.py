
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
import csv
import json
import math
import statistics

ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT / "flight_data" / "processed"
    / "hazard_indicators_oct20_22.csv"
)
OUTPUT_DIR = ROOT / "flight_data" / "processed"
REPORT_DIR = ROOT / "flight_data" / "reports"

OUTPUT_FILE = OUTPUT_DIR / "flight_risk_summary_oct20_22.csv"
REPORT_FILE = REPORT_DIR / "flight_risk_summary_report_oct20_22.json"


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def main():
    rows = read_csv(INPUT_FILE)
    if not rows:
        raise ValueError("Hazard indicator dataset is empty.")

    groups = defaultdict(list)
    for row in rows:
        flight_id = (row.get("flight_id") or "").strip()
        if flight_id:
            groups[flight_id].append(row)

    if not groups:
        raise ValueError("No flight IDs were found.")

    output_rows = []

    feature_columns = [
        "precipitation_percentile",
        "wind_gusts_percentile",
        "wind_speed_10m_percentile",
        "wind_speed_100m_percentile",
        "cloud_cover_percentile",
        "space_weather_kp_percentile",
    ]

    for flight_id, points in groups.items():
        point_scores = [
            value
            for point in points
            if (value := number(
                point.get("relative_hazard_indicator")
            )) is not None
        ]

        feature_summary = {}
        for column in feature_columns:
            values = [
                value
                for point in points
                if (value := number(point.get(column))) is not None
            ]
            name = column.removesuffix("_percentile")

            feature_summary[f"{name}_mean_percentile"] = (
                round(statistics.mean(values), 2) if values else ""
            )
            feature_summary[f"{name}_max_percentile"] = (
                round(max(values), 2) if values else ""
            )

        coverage_counts = Counter(
            point.get("hazard_data_coverage") or "UNKNOWN"
            for point in points
        )

        notam_candidates = sum(
            1
            for point in points
            if point.get("notam_evidence_indicator")
            == "UNCONFIRMED_NOTAM_CANDIDATE"
        )

        distinct_notams = sorted({
            notam.strip()
            for point in points
            for notam in (point.get("notam_numbers") or "").split(";")
            if notam.strip()
        })

        timestamps = sorted(
            point.get("timestamp_utc", "")
            for point in points
            if point.get("timestamp_utc")
        )

        score_count = len(point_scores)

        summary = {
            "flight_id": flight_id,
            "point_count": len(points),
            "points_with_relative_indicator": score_count,
            "points_without_relative_indicator": len(points) - score_count,
            "mean_relative_hazard_indicator": (
                round(statistics.mean(point_scores), 2)
                if point_scores else ""
            ),
            "max_relative_hazard_indicator": (
                round(max(point_scores), 2) if point_scores else ""
            ),
            "min_relative_hazard_indicator": (
                round(min(point_scores), 2) if point_scores else ""
            ),
            "notam_candidate_point_count": notam_candidates,
            "notam_numbers": ";".join(distinct_notams),
            "coverage_both_matched_points": coverage_counts["BOTH_MATCHED"],
            "coverage_weather_only_points": coverage_counts["WEATHER_ONLY"],
            "coverage_neither_matched_points": coverage_counts["NEITHER_MATCHED"],
            "first_timestamp_utc": timestamps[0] if timestamps else "",
            "last_timestamp_utc": timestamps[-1] if timestamps else "",
            "summary_status": (
                "RELATIVE_SUMMARY_AVAILABLE"
                if point_scores else "INSUFFICIENT_HAZARD_DATA"
            ),
            "interpretation_note": (
                "Exploratory flight-level summary of point percentiles; "
                "not a calibrated aviation safety score or probability. "
                "NOTAM candidates remain unconfirmed."
            ),
        }

        summary.update(feature_summary)
        output_rows.append(summary)

    output_rows.sort(
        key=lambda row: (
            number(row["max_relative_hazard_indicator"])
            if number(row["max_relative_hazard_indicator"]) is not None
            else -1
        ),
        reverse=True,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    columns = list(output_rows[0].keys())
    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(output_rows)

    valid_means = [
        value
        for row in output_rows
        if (value := number(
            row["mean_relative_hazard_indicator"]
        )) is not None
    ]

    report = {
        "project": "SkyRisk Auditor",
        "report_type": "exploratory_flight_level_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_FILE),
        "flight_count": len(output_rows),
        "point_count": len(rows),
        "flights_with_indicator": sum(
            row["summary_status"] == "RELATIVE_SUMMARY_AVAILABLE"
            for row in output_rows
        ),
        "flights_without_indicator": sum(
            row["summary_status"] == "INSUFFICIENT_HAZARD_DATA"
            for row in output_rows
        ),
        "flights_with_notam_candidates": sum(
            row["notam_candidate_point_count"] > 0
            for row in output_rows
        ),
        "mean_flight_indicator_distribution": {
            "min": round(min(valid_means), 2) if valid_means else None,
            "median": round(statistics.median(valid_means), 2)
            if valid_means else None,
            "max": round(max(valid_means), 2) if valid_means else None,
        },
        "limitations": [
            "Percentiles are relative to the current dataset.",
            "Flight summaries can be affected by differing point counts and sampling.",
            "High relative indicator values do not establish actual aviation danger.",
            "NOTAM candidates are not confirmed applicable hazards.",
            "This summary does not recommend diversions or recovery routes.",
        ],
    }

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\nFLIGHT-LEVEL SUMMARY COMPLETE")
    print(f"Flight count: {len(output_rows)}")
    print(f"Total points: {len(rows)}")
    print(f"Flights with indicator: {report['flights_with_indicator']}")
    print(f"Flights with NOTAM candidates: {report['flights_with_notam_candidates']}")
    print(f"\nOutput CSV:\n{OUTPUT_FILE}")
    print(f"\nReport JSON:\n{REPORT_FILE}")
    print("\nTop 10 flights by maximum relative indicator:")
    for row in output_rows[:10]:
        print(
            f"{row['flight_id']} | "
            f"points={row['point_count']} | "
            f"max={row['max_relative_hazard_indicator']} | "
            f"NOTAM candidates={row['notam_candidate_point_count']}"
        )


if __name__ == "__main__":
    main()


from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import json
import math
import statistics

ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT / "flight_data" / "processed"
    / "multihazard_dataset_oct20_22.csv"
)
OUTPUT_DIR = ROOT / "flight_data" / "processed"
REPORT_DIR = ROOT / "flight_data" / "reports"

OUTPUT_FILE = OUTPUT_DIR / "hazard_indicators_oct20_22.csv"
REPORT_FILE = REPORT_DIR / "hazard_indicators_report_oct20_22.json"

# Higher values indicate relatively higher values within this dataset.
# These are exploratory indicators, NOT aviation safety thresholds.
FEATURES = {
    "precipitation": "precipitation",
    "wind_gusts": "wind_gusts_10m",
    "wind_speed_10m": "wind_speed_10m",
    "wind_speed_100m": "wind_speed_100m",
    "cloud_cover": "cloud_cover",
    "space_weather_kp": "Kp",
}


def read_rows(path):
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


def percentile_ranks(values):
    """Empirical percentile ranks, calculated only from available values."""
    ordered = sorted(values)
    n = len(ordered)
    ranks = {}

    if n == 0:
        return ranks

    # Tied values receive their average rank.
    start = 0
    while start < n:
        end = start
        while end + 1 < n and ordered[end + 1] == ordered[start]:
            end += 1

        percentile = (
            ((start + end) / 2) / (n - 1) * 100
            if n > 1 else 50.0
        )
        ranks[ordered[start]] = round(percentile, 2)
        start = end + 1

    return ranks


def main():
    rows = read_rows(INPUT_FILE)
    if not rows:
        raise ValueError("Input dataset contains no rows.")

    # Calculate distribution-based ranks from available dataset values.
    ranks_by_feature = {}
    feature_values = {}
    feature_missing = {}

    for feature, column in FEATURES.items():
        values = [number(row.get(column)) for row in rows]
        valid = [value for value in values if value is not None]

        feature_values[feature] = values
        feature_missing[feature] = len(values) - len(valid)
        ranks_by_feature[feature] = percentile_ranks(valid)

    output_rows = []
    score_counts = Counter()
    notam_counts = Counter()
    coverage_counts = Counter()
    score_values = []

    for index, row in enumerate(rows):
        result = dict(row)
        available_indicators = []

        for feature, column in FEATURES.items():
            value = feature_values[feature][index]

            if value is None:
                result[f"{feature}_percentile"] = ""
                continue

            percentile = ranks_by_feature[feature][value]
            result[f"{feature}_percentile"] = percentile
            available_indicators.append(percentile)

        # Missing variables are excluded, not treated as zero.
        if available_indicators:
            score = round(
                statistics.mean(available_indicators), 2
            )
            score_status = "RELATIVE_SCORE_AVAILABLE"
            score_values.append(score)
        else:
            score = ""
            score_status = "INSUFFICIENT_HAZARD_DATA"

        result["relative_hazard_indicator"] = score
        result["relative_hazard_indicator_status"] = score_status
        result["indicator_count"] = len(available_indicators)

        # Candidate evidence is kept separate from the numeric score.
        candidate_count = number(row.get("notam_candidate_count"))
        candidate_count = int(candidate_count or 0)

        if candidate_count > 0:
            notam_status = "UNCONFIRMED_NOTAM_CANDIDATE"
        elif row.get("notam_candidate_status") == (
            "NO_NOTAM_CANDIDATE_FOR_FLIGHT"
        ):
            notam_status = "NO_CANDIDATE_FOUND_NOT_PROOF_OF_ABSENCE"
        else:
            notam_status = "NOTAM_LINK_UNRESOLVED"

        result["notam_evidence_indicator"] = notam_status

        coverage = row.get(
            "combined_coverage_status", "UNKNOWN"
        ) or "UNKNOWN"

        result["hazard_data_coverage"] = coverage
        result["indicator_method"] = (
            "Mean empirical percentile of available weather/Kp "
            "variables; dataset-relative, not calibrated safety risk."
        )

        output_rows.append(result)
        score_counts[score_status] += 1
        notam_counts[notam_status] += 1
        coverage_counts[coverage] += 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    extra_columns = []
    for feature in FEATURES:
        extra_columns.append(f"{feature}_percentile")

    extra_columns.extend([
        "relative_hazard_indicator",
        "relative_hazard_indicator_status",
        "indicator_count",
        "notam_evidence_indicator",
        "hazard_data_coverage",
        "indicator_method",
    ])

    columns = list(rows[0].keys())
    columns.extend(c for c in extra_columns if c not in columns)

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=columns, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(output_rows)

    def stats(values):
        if not values:
            return None
        return {
            "min": round(min(values), 2),
            "median": round(statistics.median(values), 2),
            "max": round(max(values), 2),
            "mean": round(statistics.mean(values), 2),
        }

    feature_summary = {}
    for feature, values in feature_values.items():
        valid = [v for v in values if v is not None]
        feature_summary[feature] = {
            "source_column": FEATURES[feature],
            "available_rows": len(valid),
            "missing_rows": feature_missing[feature],
            "min": min(valid) if valid else None,
            "median": statistics.median(valid) if valid else None,
            "max": max(valid) if valid else None,
        }

    report = {
        "project": "SkyRisk Auditor",
        "report_type": "exploratory_relative_hazard_indicators",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_FILE),
        "total_rows": len(rows),
        "feature_summary": feature_summary,
        "relative_indicator_summary": stats(score_values),
        "score_status_counts": dict(score_counts),
        "notam_evidence_counts": dict(notam_counts),
        "coverage_counts": dict(coverage_counts),
        "method": {
            "normalization": "Empirical percentile ranks from this dataset",
            "aggregation": "Arithmetic mean of available feature percentiles",
            "weights": "Equal weight for each available feature",
            "missing_data": (
                "Missing values are excluded from the row mean and "
                "reported separately; no missing value is replaced by zero."
            ),
            "notam": (
                "NOTAM candidate evidence is reported separately and "
                "does not add points to the numeric indicator."
            ),
        },
        "limitations": [
            "This is a relative exploratory indicator, not a calibrated aviation risk score.",
            "Percentiles depend on the current sample and may change with new data.",
            "Weather fields include grid estimates and near-surface wind measurements.",
            "Kp is a global index and does not prove local flight impact.",
            "NOTAM candidates do not establish applicability or operational impact.",
            "No route recovery or diversion recommendation is generated here.",
        ],
    }

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\nRELATIVE HAZARD INDICATORS BUILT")
    print(f"Input rows: {len(rows)}")
    print(f"Output rows: {len(output_rows)}")
    print(f"Rows with indicator: {len(score_values)}")
    print(f"Rows without usable hazard values: {score_counts['INSUFFICIENT_HAZARD_DATA']}")
    print(f"\nIndicator CSV:\n{OUTPUT_FILE}")
    print(f"\nReport JSON:\n{REPORT_FILE}")
    print("\nFeature availability:")
    for feature, details in feature_summary.items():
        print(
            f"  {feature}: {details['available_rows']} available, "
            f"{details['missing_rows']} missing"
        )


if __name__ == "__main__":
    main()

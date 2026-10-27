"""Validate generated historical outputs and write a compact evidence report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
PROCESSED = ROOT / "processed"
REPORTS = ROOT / "reports"
KEY = ["flight_id", "segment_index", "point_index"]


def check(name: str, status: str, count: int, detail: str) -> dict:
    return {"check": name, "status": status, "count": int(count), "detail": detail}


def main() -> None:
    points_path = PROCESSED / "trajectory_point_indicators.csv"
    integrated_path = PROCESSED / "historical_trajectory_quality_integrated.csv"
    points = pd.read_csv(points_path, parse_dates=["timestamp_utc"])
    integrated = pd.read_csv(integrated_path, parse_dates=["timestamp_utc"])
    rows = []
    duplicate_keys = int(points.duplicated(KEY).sum())
    rows.append(check(
        "trajectory_composite_key_duplicates",
        "pass" if duplicate_keys == 0 else "fail",
        duplicate_keys,
        "flight_id + segment_index + point_index",
    ))
    invalid_time = int(points["timestamp_utc"].isna().sum())
    rows.append(check(
        "trajectory_invalid_timestamps",
        "pass" if invalid_time == 0 else "fail",
        invalid_time,
        "UTC timestamps parse successfully",
    ))
    invalid_coordinates = int(
        (~points["longitude"].between(-180, 180)
         | ~points["latitude"].between(-90, 90)).sum()
    )
    rows.append(check(
        "trajectory_invalid_coordinates",
        "pass" if invalid_coordinates == 0 else "fail",
        invalid_coordinates,
        "WGS84 coordinate ranges",
    ))
    rows.append(check(
        "kp_unmatched_rows",
        "warning" if integrated["Kp"].isna().any() else "pass",
        int(integrated["Kp"].isna().sum()),
        "Missing Kp remains missing; no zero fill",
    ))
    rows.append(check(
        "swips_unmatched_quality_rows",
        "warning" if integrated["flags_raw"].isna().any() else "pass",
        int(integrated["flags_raw"].isna().sum()),
        "Time-only L1 indicator match; not an aviation hazard label",
    ))
    rows.append(check(
        "trajectory_row_count_preserved",
        "pass" if len(points) == len(integrated) else "fail",
        abs(len(points) - len(integrated)),
        f"points={len(points)}, integrated={len(integrated)}",
    ))
    frame = pd.DataFrame(rows)
    frame.to_csv(REPORTS / "final_validation_report.csv", index=False)
    summary = {
        "checks": len(frame),
        "failures": int((frame["status"] == "fail").sum()),
        "warnings": int((frame["status"] == "warning").sum()),
        "trajectory_rows": len(points),
        "integrated_rows": len(integrated),
        "trajectory_key": "flight_id + segment_index + point_index",
    }
    (REPORTS / "final_validation_report.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

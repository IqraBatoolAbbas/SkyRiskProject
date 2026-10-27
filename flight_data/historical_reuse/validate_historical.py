"""Validate locally available SkyRisk Auditor historical datasets.

This module is deliberately conservative: it reports problems and coverage
without fabricating values or silently dropping records. It is also used by
the appended validation section in the historical notebook.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

TRAJECTORY_KEY = ["flight_id", "segment_index", "point_index"]
TRAJECTORY_COLUMNS = TRAJECTORY_KEY + [
    "timestamp_utc",
    "longitude",
    "latitude",
]
TIME_NAMES = ("timestamp", "time", "datetime", "date")


def _read_table(path: Path) -> pd.DataFrame | None:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    return pd.DataFrame(value)
        return pd.DataFrame()
    return None


def inventory(data_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        record: dict[str, Any] = {
            "path": str(path.relative_to(data_dir)),
            "extension": path.suffix.lower(),
            "bytes": path.stat().st_size,
            "rows": None,
            "columns": None,
            "min_timestamp_utc": None,
            "max_timestamp_utc": None,
            "read_error": None,
        }
        try:
            frame = _read_table(path)
            if frame is not None:
                record["rows"] = len(frame)
                record["columns"] = "|".join(map(str, frame.columns))
                time_columns = [
                    c for c in frame.columns
                    if any(name in str(c).lower() for name in TIME_NAMES)
                ]
                if time_columns:
                    parsed = pd.to_datetime(
                        frame[time_columns[0]], utc=True, errors="coerce"
                    ).dropna()
                    if not parsed.empty:
                        record["min_timestamp_utc"] = parsed.min().isoformat()
                        record["max_timestamp_utc"] = parsed.max().isoformat()
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            record["read_error"] = f"{type(exc).__name__}: {exc}"
        rows.append(record)
    return rows


def validate_frame(frame: pd.DataFrame, path: str) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check: str, status: str, count: int, detail: str) -> None:
        checks.append({
            "dataset": path,
            "check": check,
            "status": status,
            "count": int(count),
            "detail": detail,
        })

    missing_columns = [c for c in TRAJECTORY_COLUMNS if c not in frame.columns]
    is_trajectory = not missing_columns
    if is_trajectory:
        null_key = int(frame[TRAJECTORY_KEY].isna().any(axis=1).sum())
        add(
            "trajectory_composite_key_nulls",
            "pass" if null_key == 0 else "fail",
            null_key,
            "Key is flight_id + segment_index + point_index",
        )
        duplicate_key = int(frame.duplicated(TRAJECTORY_KEY, keep=False).sum())
        add(
            "trajectory_composite_key_duplicates",
            "pass" if duplicate_key == 0 else "fail",
            duplicate_key,
            "Duplicates are checked on the full trajectory key",
        )

        parsed = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
        invalid_time = int(parsed.isna().sum())
        add(
            "invalid_timestamp_utc",
            "pass" if invalid_time == 0 else "fail",
            invalid_time,
            "Timestamps must parse as UTC",
        )
        for column, low, high in (
            ("longitude", -180, 180),
            ("latitude", -90, 90),
        ):
            numeric = pd.to_numeric(frame[column], errors="coerce")
            invalid = int((numeric.isna() | ~numeric.between(low, high)).sum())
            add(
                f"invalid_{column}",
                "pass" if invalid == 0 else "fail",
                invalid,
                f"Expected range [{low}, {high}]",
            )

        ordered = frame.assign(_timestamp=parsed).sort_values(
            ["flight_id", "segment_index", "point_index"]
        )
        time_diff = ordered.groupby(
            ["flight_id", "segment_index"], sort=False
        )["_timestamp"].diff().dt.total_seconds()
        backwards = int((time_diff < 0).sum())
        add(
            "trajectory_timestamp_order",
            "pass" if backwards == 0 else "fail",
            backwards,
            "Point order must not move backward in time",
        )
    else:
        add(
            "schema_classification",
            "info",
            len(missing_columns),
            "Not classified as trajectory; missing candidates: "
            + "|".join(missing_columns),
        )
    return checks


def run(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    inventory_rows = inventory(data_dir)
    checks: list[dict[str, Any]] = []
    for entry in inventory_rows:
        path = data_dir / entry["path"]
        frame = _read_table(path)
        if frame is not None:
            checks.extend(validate_frame(frame, entry["path"]))
    return pd.DataFrame(inventory_rows), pd.DataFrame(checks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()
    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    source_dir = data_dir / "raw"
    source_dir.mkdir(parents=True, exist_ok=True)
    inventory_frame, validation_frame = run(source_dir)
    inventory_frame.to_csv(reports_dir / "dataset_inventory.csv", index=False)
    validation_frame.to_csv(reports_dir / "validation_report.csv", index=False)
    summary = {
        "data_dir": str(source_dir),
        "files_seen": len(inventory_frame),
        "checks_run": len(validation_frame),
        "failures": int((validation_frame["status"] == "fail").sum())
        if not validation_frame.empty else 0,
        "source_files_available": len(inventory_frame) > 0,
        "note": "No observations are fabricated and raw files are not modified.",
    }
    (reports_dir / "validation_report.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    log = pd.DataFrame([{
        "stage": "workspace_inventory_and_validation",
        "status": "complete",
        "inputs": str(data_dir),
        "outputs": "reports/dataset_inventory.csv|reports/validation_report.csv|reports/validation_report.json",
        "notes": json.dumps(summary),
    }])
    log.to_csv(reports_dir / "processing_log.csv", index=False)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

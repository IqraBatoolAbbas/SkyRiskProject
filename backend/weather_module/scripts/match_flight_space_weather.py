
import bisect
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent.parent

FLIGHT_FILE = (
    PROJECT_DIR
    / "flight_data"
    / "processed"
    / "pakistan_region_candidate_points_oct20_22.csv"
)

KP_FILE = BASE_DIR / "data" / "gfz_kp_2026-10-20_2026-10-22.csv"

OUTPUT_FILE = (
    BASE_DIR
    / "processed"
    / "flight_space_weather_matched_oct20_22.csv"
)

REPORT_FILE = (
    BASE_DIR
    / "reports"
    / "flight_space_weather_match_report.json"
)

# Kp observations are at 3-hour intervals.
# A nearest-observation match is accepted only within 90 minutes.
MAX_GAP_SECONDS = 90 * 60


def parse_utc(value):
    value = (value or "").strip()
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not FLIGHT_FILE.exists():
        raise FileNotFoundError(f"Flight input not found: {FLIGHT_FILE}")
    if not KP_FILE.exists():
        raise FileNotFoundError(f"Kp input not found: {KP_FILE}")

    with KP_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        kp_rows = list(csv.DictReader(file))

    observations = []
    for row in kp_rows:
        dt = parse_utc(row.get("timestamp_utc"))
        try:
            kp = float(row["Kp"])
        except (ValueError, TypeError, KeyError):
            continue

        if dt is not None:
            observations.append({
                "dt": dt,
                "timestamp_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Kp": kp,
                "status": row.get("status", "not_provided"),
                "source": row.get("source", "GFZ Potsdam"),
            })

    observations.sort(key=lambda item: item["dt"])
    times = [item["dt"] for item in observations]

    if not observations:
        raise ValueError("No valid Kp observations found in the input CSV.")

    output_rows = []
    matched_gaps = []
    status_counts = Counter()
    date_counts = Counter()
    unmatched_reasons = Counter()

    with FLIGHT_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        flight_rows = list(csv.DictReader(file))
        flight_columns = list(flight_rows[0].keys()) if flight_rows else []

    for flight in flight_rows:
        flight_dt = parse_utc(flight.get("timestamp_utc"))
        result = dict(flight)

        result.update({
            "kp_timestamp_utc": "",
            "Kp": "",
            "kp_status": "",
            "kp_source": "",
            "kp_gap_minutes": "",
            "space_weather_match_status": "",
        })

        if flight_dt is None:
            result["space_weather_match_status"] = "INVALID_FLIGHT_TIMESTAMP"
            unmatched_reasons["INVALID_FLIGHT_TIMESTAMP"] += 1
            output_rows.append(result)
            continue

        pos = bisect.bisect_left(times, flight_dt)
        candidate_indices = []

        if pos < len(times):
            candidate_indices.append(pos)
        if pos > 0:
            candidate_indices.append(pos - 1)

        nearest = min(
            (observations[i] for i in candidate_indices),
            key=lambda item: (
                abs((item["dt"] - flight_dt).total_seconds()),
                item["dt"],
            ),
        )

        gap_seconds = abs((nearest["dt"] - flight_dt).total_seconds())

        if gap_seconds > MAX_GAP_SECONDS:
            result["space_weather_match_status"] = (
                "NO_KP_OBSERVATION_WITHIN_90_MIN"
            )
            unmatched_reasons["NO_KP_OBSERVATION_WITHIN_90_MIN"] += 1
        else:
            result["kp_timestamp_utc"] = nearest["timestamp_utc"]
            result["Kp"] = nearest["Kp"]
            result["kp_status"] = nearest["status"]
            result["kp_source"] = nearest["source"]
            result["kp_gap_minutes"] = round(gap_seconds / 60, 3)
            result["space_weather_match_status"] = (
                "MATCHED_GLOBAL_KP_PRELIMINARY"
                if nearest["status"] == "pre"
                else "MATCHED_GLOBAL_KP_STATUS_RETAINED"
            )

            matched_gaps.append(gap_seconds / 60)
            status_counts[nearest["status"]] += 1
            date_counts[flight_dt.date().isoformat()] += 1

        output_rows.append(result)

    output_columns = flight_columns + [
        "kp_timestamp_utc",
        "Kp",
        "kp_status",
        "kp_source",
        "kp_gap_minutes",
        "space_weather_match_status",
    ]

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(output_rows)

    total = len(output_rows)
    matched = len(matched_gaps)

    report = {
        "source": "GFZ Potsdam",
        "flight_input": str(FLIGHT_FILE),
        "kp_input": str(KP_FILE),
        "output_csv": str(OUTPUT_FILE),
        "total_flight_points": total,
        "valid_kp_observations": len(observations),
        "matched_flight_points": matched,
        "unmatched_flight_points": total - matched,
        "match_rate_percent": round(matched / total * 100, 2) if total else 0,
        "maximum_allowed_gap_minutes": MAX_GAP_SECONDS / 60,
        "maximum_observed_match_gap_minutes": (
            round(max(matched_gaps), 3) if matched_gaps else None
        ),
        "matched_by_kp_status": dict(status_counts),
        "matched_flight_points_by_date_utc": dict(date_counts),
        "unmatched_reasons": dict(unmatched_reasons),
        "limitations": [
            "Kp is a global geomagnetic index, not a local flight hazard measurement.",
            "All source observations currently have preliminary status 'pre'.",
            "Nearest-time matching does not establish causation or operational impact.",
            "A match does not calculate or validate a flight-risk score.",
            "The flight points are candidates within an approximate geographic bounding box, not verified official FIR coverage.",
        ],
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nMatched CSV saved: {OUTPUT_FILE}")
    print(f"Report saved: {REPORT_FILE}")


if __name__ == "__main__":
    main()

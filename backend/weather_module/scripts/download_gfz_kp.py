
import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"

START_DATE = "2026-10-20"
END_DATE = "2026-10-22"

URL = (
    "https://kp.gfz.de/app/json/"
    f"?start={START_DATE}T00:00:00Z"
    f"&end={END_DATE}T23:59:59Z"
    "&index=Kp"
)

CSV_PATH = DATA_DIR / f"gfz_kp_{START_DATE}_{END_DATE}.csv"
RAW_PATH = DATA_DIR / "gfz_kp_raw.json"
REPORT_PATH = REPORT_DIR / "gfz_kp_download_report.json"


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "SkyRisk-Auditor-FYP/1.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    RAW_PATH.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8"
    )

    datetimes = payload.get("datetime", [])
    kp_values = payload.get("Kp", [])
    statuses = payload.get("status", [])

    if len(datetimes) != len(kp_values):
        raise ValueError("GFZ datetime aur Kp arrays ki lengths match nahi kartin.")

    if statuses and len(statuses) != len(datetimes):
        raise ValueError("GFZ status array ki length match nahi karti.")

    rows = []
    for i, timestamp in enumerate(datetimes):
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        if dt.date().isoformat() < START_DATE:
            continue
        if dt.date().isoformat() > END_DATE:
            continue

        kp = float(kp_values[i])
        status = statuses[i] if statuses else "not_provided"

        rows.append({
            "timestamp_utc": dt.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "date_utc": dt.date().isoformat(),
            "Kp": kp,
            "status": status,
            "source": "GFZ Potsdam",
        })

    rows.sort(key=lambda row: row["timestamp_utc"])

    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp_utc",
                "date_utc",
                "Kp",
                "status",
                "source",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    rows_by_date = {}
    for row in rows:
        date = row["date_utc"]
        rows_by_date[date] = rows_by_date.get(date, 0) + 1

    expected_dates = [
        "2026-10-20",
        "2026-10-21",
        "2026-10-22",
    ]

    report = {
        "source": "GFZ Potsdam",
        "source_url": URL,
        "license": payload.get("meta", {}).get("license"),
        "requested_dates_utc": [START_DATE, END_DATE],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(rows),
        "rows_by_date": rows_by_date,
        "missing_dates": [
            date for date in expected_dates
            if rows_by_date.get(date, 0) == 0
        ],
        "status_counts": {
            status: sum(1 for row in rows if row["status"] == status)
            for status in sorted({row["status"] for row in rows})
        },
        "date_coverage_complete": all(
            rows_by_date.get(date, 0) > 0 for date in expected_dates
        ),
        "csv_file": str(CSV_PATH),
        "raw_response_file": str(RAW_PATH),
        "limitations": [
            "Kp is a global geomagnetic index, not a direct local flight hazard.",
            "GFZ status values must be retained to distinguish preliminary "
            "from definitive data.",
            "This script does not calculate flight risk.",
            "Date presence does not by itself validate every observation.",
        ],
    }

    REPORT_PATH.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nCSV saved: {CSV_PATH}")
    print(f"Report saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()

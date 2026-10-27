
import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "backend" / "weather_module" / "data"
REPORT_DIR = ROOT / "backend" / "weather_module" / "reports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = "2026-10-20"
END_DATE = "2026-10-22"

URL = (
    "https://services.swpc.noaa.gov/"
    "products/noaa-planetary-k-index.json"
)


def parse_utc(value):
    if not value:
        return None

    value = str(value).strip()

    formats = (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
    )

    for fmt in formats:
        try:
            return datetime.strptime(
                value, fmt
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None

def main():
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "SkyRiskAuditor-FYP/1.0"}
    )

    with urllib.request.urlopen(request, timeout=40) as response:
        raw = json.loads(response.read().decode("utf-8"))

    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError("NOAA response format unexpected.")

    raw_file = DATA_DIR / "noaa_planetary_k_index_raw.json"
    raw_file.write_text(
        json.dumps(raw, indent=2),
        encoding="utf-8"
    )

    headers = [str(x).strip() for x in raw[0]]
    time_key = next(
        (x for x in ("time_tag", "time") if x in headers),
        None
    )
    kp_key = next(
        (x for x in ("Kp", "kp_index") if x in headers),
        None
    )

    if time_key is None or kp_key is None:
        raise ValueError(
            f"Expected time/Kp columns not found. "
            f"NOAA columns received: {headers}"
        )

    output_rows = []

    for values in raw[1:]:
        if not isinstance(values, list):
            continue

        record = dict(zip(headers, values))
        timestamp = parse_utc(record.get(time_key))

        if timestamp is None:
            continue

        day = timestamp.strftime("%Y-%m-%d")
        if not START_DATE <= day <= END_DATE:
            continue

        try:
            kp = float(record[kp_key])
            if not 0 <= kp <= 9:
                kp = None
        except (ValueError, TypeError, KeyError):
            kp = None

        output_rows.append({
            "timestamp_utc": timestamp.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "Kp": kp,
            "source": "NOAA SWPC",
            "source_url": URL
        })

    output_rows.sort(key=lambda row: row["timestamp_utc"])

    csv_file = DATA_DIR / "noaa_kp_2026-10-20_2026-10-22.csv"

    with csv_file.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp_utc", "Kp", "source", "source_url"
            ]
        )
        writer.writeheader()
        writer.writerows(output_rows)

    by_date = {}
    for row in output_rows:
        date = row["timestamp_utc"][:10]
        by_date.setdefault(date, {"rows": 0, "valid_kp": 0})
        by_date[date]["rows"] += 1
        if row["Kp"] is not None:
            by_date[date]["valid_kp"] += 1

    report = {
        "source": "NOAA Space Weather Prediction Center",
        "source_url": URL,
        "requested_dates_utc": [START_DATE, END_DATE],
        "retrieved_at_utc": datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_rows_in_date_range": len(output_rows),
        "valid_numeric_kp_rows": sum(
            row["Kp"] is not None for row in output_rows
        ),
        "rows_by_date": by_date,
        "csv_file": str(csv_file),
        "raw_response_file": str(raw_file),
        "limitations": [
            "The endpoint may provide recent data rather than a complete archive.",
            "Check that all requested dates are present before matching.",
            "Planetary Kp is a global geomagnetic index, not a direct local flight hazard measurement.",
            "This script does not calculate flight risk."
        ]
    }

    report_file = REPORT_DIR / "space_weather_kp_download_report.json"
    report_file.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))
    print("\nCSV saved:", csv_file)
    print("Report saved:", report_file)

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("SPACE WEATHER DOWNLOAD FAILED")
        print(type(error).__name__ + ":", error)
        raise

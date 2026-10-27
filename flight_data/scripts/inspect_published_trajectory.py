
import csv
import json
import urllib.request
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "flight_data" / "data" / "external"
REPORT_DIR = ROOT / "flight_data" / "reports"

CSV_FILE = DATA_DIR / "tartanaviation_adsb_19k_clean.csv"
REPORT_FILE = REPORT_DIR / "tartanaviation_dataset_inspection.json"

URL = (
    "https://huggingface.co/datasets/"
    "SANIKKI/tartanaviation-adsb-19k-clean/"
    "resolve/main/tartanaviation_adsb_19k_clean.csv"
)

REQUIRED = [
    "aircraft_id", "year", "month", "day",
    "hour", "minute", "second", "latitude",
    "longitude", "altitude_ft",
    "ground_speed_kts", "heading_deg",
]


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not CSV_FILE.exists():
        print("Downloading published CSV dataset...")
        request = urllib.request.Request(
            URL,
            headers={"User-Agent": "SkyRisk-FYP-Inspection/1.0"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            CSV_FILE.write_bytes(response.read())
    else:
        print("Using existing dataset file; no download needed.")

    rows = 0
    missing = Counter()
    aircraft_ids = set()
    samples = []
    columns = []

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []

        for row in reader:
            rows += 1

            for column in columns:
                if row.get(column) is None or row[column].strip() == "":
                    missing[column] += 1

            if row.get("aircraft_id"):
                aircraft_ids.add(row["aircraft_id"])

            if len(samples) < 5:
                samples.append(row)

    report = {
        "source": "TartanAviation ADS-B dataset",
        "source_url": URL,
        "local_file": str(CSV_FILE),
        "row_count": rows,
        "column_count": len(columns),
        "columns": columns,
        "required_fields_present": {
            field: field in columns for field in REQUIRED
        },
        "missing_values_by_column": dict(missing),
        "unique_aircraft_ids": len(aircraft_ids),
        "sample_rows": samples,
        "geographic_scope": "Ohio, USA; not Pakistan",
        "historical_notam_match_confirmed": False,
        "database_changed": False,
    }

    with REPORT_FILE.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\nRows:", rows)
    print("Columns:", len(columns))
    print("Unique aircraft IDs:", len(aircraft_ids))
    print("\nRequired fields:")
    for field, present in report["required_fields_present"].items():
        print(f"  {field}: {'YES' if present else 'NO'}")

    print("\nMissing values:", dict(missing))
    print("\nReport saved to:", REPORT_FILE)
    print("No database changes were made.")


if __name__ == "__main__":
    main()


from pathlib import Path
import csv
import json

root = Path(__file__).resolve().parents[2]

files = [
    root / "flight_data" / "processed"
    / "pakistan_region_candidate_points_oct20_22.csv",

    root / "flight_data" / "processed"
    / "adsbaero_trajectories_oct20_22_segment_audited.csv",
]

for path in files:
    print("\n" + "=" * 70)
    print("FILE:", path.name)

    if not path.exists():
        print("NOT FOUND")
        continue

    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:
        reader = csv.DictReader(f)
        print("COLUMNS:", reader.fieldnames)

        samples = {}
        count = 0

        for row in reader:
            count += 1
            flight_id = row.get("flight_id", "")

            if flight_id and flight_id not in samples:
                samples[flight_id] = row

            if len(samples) >= 3:
                break

    print("Rows scanned for samples:", count)
    print("Sample records:")

    for flight_id, row in samples.items():
        print(json.dumps(row, indent=2, ensure_ascii=False))

print("\nInspection complete. No files modified.")

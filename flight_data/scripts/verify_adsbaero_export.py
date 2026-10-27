
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CSV_FILE = (
    ROOT
    / "flight_data"
    / "processed"
    / "adsbaero_trajectories_oct20_22.csv"
)


def main():
    if not CSV_FILE.exists():
        print(f"CSV file not found: {CSV_FILE}")
        return

    total_rows = 0
    flight_ids = set()
    date_counts = Counter()
    region_counts = Counter()
    missing_timestamps = 0
    invalid_coordinates = 0

    with CSV_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            total_rows += 1

            flight_id = row.get("flight_id", "").strip()
            if flight_id:
                flight_ids.add(flight_id)

            timestamp = row.get("timestamp_utc", "").strip()
            if timestamp:
                date_counts[timestamp[:10]] += 1
            else:
                missing_timestamps += 1

            region_counts[
                row.get("inside_approx_region", "missing")
            ] += 1

            try:
                lon = float(row["longitude"])
                lat = float(row["latitude"])

                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    invalid_coordinates += 1
            except (ValueError, KeyError, TypeError):
                invalid_coordinates += 1

    print("=== ADSB.aero CSV VERIFICATION ===")
    print("Total trajectory rows:", total_rows)
    print("Unique flight IDs:", len(flight_ids))
    print("Missing timestamps:", missing_timestamps)
    print("Invalid coordinates:", invalid_coordinates)

    print("\nRows by UTC date:")
    for day, count in sorted(date_counts.items()):
        print(f"  {day}: {count}")

    print("\nApproximate-region flag:")
    for flag, count in sorted(region_counts.items()):
        print(f"  {flag}: {count}")

    print("\nCSV:", CSV_FILE)


if __name__ == "__main__":
    main()

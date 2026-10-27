
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES = [
    ROOT / "flight_data" / "historical_reuse" / "processed"
    / "historical_trajectory_kp_integrated.csv",

    ROOT / "flight_data" / "historical_reuse" / "processed"
    / "noaa_kp_2026-10-10_2026-10-15.csv",

    ROOT / "flight_data" / "historical_reuse" / "processed"
    / "open_meteo_reference_hourly.csv",
]

TIME_HINTS = (
    "time", "date", "timestamp", "datetime"
)

def inspect_csv(path):
    print("\n" + "=" * 75)
    print(f"FILE: {path.name}")
    print("=" * 75)

    if not path.exists():
        print("STATUS: FILE NOT FOUND")
        return

    row_count = 0
    first_rows = []
    time_ranges = {}

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames or []

            print("COLUMNS:")
            print(", ".join(headers) if headers else "No column headers")

            time_columns = [
                name for name in headers
                if any(hint in name.lower() for hint in TIME_HINTS)
            ]

            for row in reader:
                row_count += 1

                if len(first_rows) < 3:
                    first_rows.append(row)

                for column in time_columns:
                    value = (row.get(column) or "").strip()
                    if value:
                        bounds = time_ranges.setdefault(
                            column, {"min": value, "max": value}
                        )
                        if value < bounds["min"]:
                            bounds["min"] = value
                        if value > bounds["max"]:
                            bounds["max"] = value

        print(f"DATA ROWS: {row_count}")

        if time_ranges:
            print("TIME/DATE VALUE RANGES (lexical; verify formats):")
            for column, bounds in time_ranges.items():
                print(
                    f"  {column}: {bounds['min']} -> {bounds['max']}"
                )

        print("SAMPLE ROWS:")
        for index, row in enumerate(first_rows, start=1):
            print(f"\nRow {index}:")
            for key, value in row.items():
                print(f"  {key}: {value}")

    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}")


def main():
    for path in FILES:
        inspect_csv(path)

    print("\nInspection complete. No input files were modified.")


if __name__ == "__main__":
    main()

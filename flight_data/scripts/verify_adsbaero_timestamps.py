
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "flight_data" / "reports" / "adsbaero_oct20_22_test.json"


def count_coordinates(path_data):
    """Count coordinates across common path structures."""
    if isinstance(path_data, list):
        # A list may be a coordinate list or a list of segments.
        if path_data and isinstance(path_data[0], (list, tuple)):
            first = path_data[0]
            if len(first) >= 2 and all(
                isinstance(v, (int, float)) for v in first[:2]
            ):
                return len(path_data)

            return sum(count_coordinates(item) for item in path_data)

        return 0

    if isinstance(path_data, dict):
        total = 0
        for key in ("coordinates", "coords", "points"):
            if key in path_data:
                total += count_coordinates(path_data[key])
        if total:
            return total

    return 0


def main():
    if not SOURCE.exists():
        print(f"ERROR: Source JSON not found:\n{SOURCE}")
        return

    with SOURCE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = None
        for key in ("flights", "results", "data", "records"):
            if isinstance(data.get(key), list):
                records = data[key]
                break

        if records is None:
            print("Top-level JSON keys:", list(data.keys()))
            print("Could not automatically identify the flight-record list.")
            return
    else:
        print("Unexpected JSON format:", type(data).__name__)
        return

    print("Flight records:", len(records))
    print("Top-level keys:", list(data.keys()) if isinstance(data, dict) else "list")

    mismatch_count = 0
    missing_timestamp_count = 0
    total_coordinates = 0
    total_timestamps = 0
    examples = []

    for i, flight in enumerate(records):
        if not isinstance(flight, dict):
            continue

        path_data = flight.get("path")
        timestamps = flight.get("timestamps")

        coordinate_count = count_coordinates(path_data)
        timestamp_count = len(timestamps) if isinstance(timestamps, list) else 0

        total_coordinates += coordinate_count
        total_timestamps += timestamp_count

        if not isinstance(timestamps, list) or timestamp_count == 0:
            missing_timestamp_count += 1

        if coordinate_count != timestamp_count:
            mismatch_count += 1
            if len(examples) < 15:
                examples.append({
                    "record_index": i,
                    "flight_id": flight.get("flight_id", flight.get("id")),
                    "coordinate_count": coordinate_count,
                    "timestamp_count": timestamp_count,
                    "path_type": type(path_data).__name__,
                    "path_keys": list(path_data.keys())
                    if isinstance(path_data, dict) else None,
                })

    print("\n--- ALIGNMENT SUMMARY ---")
    print("Total path coordinates:", total_coordinates)
    print("Total timestamps:", total_timestamps)
    print("Records with coordinate/timestamp count mismatch:", mismatch_count)
    print("Records with missing timestamps:", missing_timestamp_count)

    print("\n--- FIRST MISMATCH EXAMPLES ---")
    if examples:
        for item in examples:
            print(item)
    else:
        print("No count mismatches detected.")

    print(
        "\nNote: equal counts do not prove timestamps correspond "
        "to coordinates in the correct order."
    )


if __name__ == "__main__":
    main()

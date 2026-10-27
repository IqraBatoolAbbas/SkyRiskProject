
import json
from pathlib import Path

SOURCE = Path("flight_data/reports/adsbaero_oct20_22_test.json")


def flatten_coordinates(value):
    """Flatten nested coordinate arrays without changing their order."""
    result = []

    if isinstance(value, list):
        if (
            len(value) >= 2
            and isinstance(value[0], (int, float))
            and isinstance(value[1], (int, float))
        ):
            result.append(value)
        else:
            for item in value:
                result.extend(flatten_coordinates(item))

    return result


def flatten_numbers(value):
    """Flatten nested numeric lists while preserving order."""
    result = []

    if isinstance(value, list):
        for item in value:
            result.extend(flatten_numbers(item))
    elif isinstance(value, (int, float)):
        result.append(value)

    return result


def main():
    if not SOURCE.exists():
        print(f"Source file not found: {SOURCE}")
        return

    with SOURCE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    flights = data.get("flights", [])
    print(f"Total flight records: {len(flights)}")

    for index, flight in enumerate(flights[:3]):
        path = flight.get("path") or {}
        coordinates = flatten_coordinates(path.get("coordinates", []))
        timestamps = flatten_numbers(flight.get("timestamps", []))

        print("\n" + "=" * 60)
        print(f"Record {index + 1}")
        print("Flight ID:", flight.get("flight_id"))
        print("Start timestamp:", flight.get("start_ts"))
        print("End timestamp:", flight.get("end_ts"))
        print("Point count field:", flight.get("point_count"))
        print("Raw point count:", flight.get("raw_point_count"))
        print("Path type:", path.get("type"))
        print("Coordinate count:", len(coordinates))
        print("Timestamp count after flattening:", len(timestamps))

        print("First 5 flattened timestamps:", timestamps[:5])
        print("Last 5 flattened timestamps:", timestamps[-5:])

        print("Field summaries:")
        for field in (
            "path_tracks",
            "path_gs",
            "path_vr",
            "path_ias",
            "path_agl_ft",
            "alt_correction_ft",
        ):
            value = flight.get(field)

            if isinstance(value, list):
                print(
                    f"  {field}: list, length={len(value)}, "
                    f"first_items={value[:3]}"
                )
            else:
                print(f"  {field}: {value!r}")

        print("Coordinate samples:")
        print("  First:", coordinates[:2])
        print("  Last:", coordinates[-2:])


if __name__ == "__main__":
    main()

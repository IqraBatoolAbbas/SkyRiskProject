
import json
from pathlib import Path
from datetime import datetime, timezone

SOURCE = Path("flight_data/reports/adsbaero_oct20_22_test.json")


def flatten_coordinates(value):
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
    result = []
    if isinstance(value, list):
        for item in value:
            result.extend(flatten_numbers(item))
    elif isinstance(value, (int, float)):
        result.append(float(value))
    return result


def to_epoch(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).timestamp()
    except (ValueError, AttributeError):
        return None


def main():
    with SOURCE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    flights = data.get("flights", [])
    exact_count = 0
    ordered_count = 0
    endpoint_count = 0

    print("Flights checked:", len(flights))

    for index, flight in enumerate(flights):
        path = flight.get("path") or {}
        coords = flatten_coordinates(path.get("coordinates", []))
        times = flatten_numbers(flight.get("timestamps", []))

        if len(coords) == len(times):
            exact_count += 1

            # Check whether timestamps are non-decreasing.
            if all(times[i] <= times[i + 1] for i in range(len(times) - 1)):
                ordered_count += 1

        start = to_epoch(flight.get("start_ts"))
        end = to_epoch(flight.get("end_ts"))

        if times and start is not None and end is not None:
            if (
                abs(times[0] - start) <= 2
                and abs(times[-1] - end) <= 2
            ):
                endpoint_count += 1

        if index < 10:
            print("\nFlight:", flight.get("flight_id"))
            print("Coordinates:", len(coords), "Timestamps:", len(times))
            print("Timestamps ordered:", bool(times) and all(
                times[i] <= times[i + 1]
                for i in range(len(times) - 1)
            ))
            print("Start/end match:",
                  bool(times and start is not None and end is not None)
                  and abs(times[0] - start) <= 2
                  and abs(times[-1] - end) <= 2)

    print("\n--- SUMMARY ---")
    print("Coordinate/timestamp counts equal:", exact_count)
    print("Timestamps in non-decreasing order:", ordered_count)
    print("First/last timestamps match start/end:", endpoint_count)
    print("\nNote: passing these checks does not prove every timestamp")
    print("belongs to the corresponding coordinate.")


if __name__ == "__main__":
    main()

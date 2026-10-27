
import json
from pathlib import Path
from pprint import pprint

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "flight_data" / "reports" / "adsbaero_oct20_22_test.json"


def main():
    with SOURCE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    flights = data.get("flights", [])

    print("Total flights:", len(flights))

    if not flights:
        print("No flight records found.")
        print("Top-level keys:", list(data.keys()))
        return

    # Inspect one record only; do not print the whole dataset.
    flight = flights[0]

    print("\n--- FLIGHT RECORD KEYS ---")
    print(list(flight.keys()))

    print("\n--- FLIGHT ID ---")
    print(flight.get("flight_id", flight.get("id")))

    print("\n--- TIMESTAMPS ---")
    pprint(flight.get("timestamps"))

    print("\n--- PATH STRUCTURE ---")
    path = flight.get("path")
    if isinstance(path, dict):
        print("Path keys:", list(path.keys()))
        print("Path type:", path.get("type"))

        coordinates = path.get("coordinates", [])
        print("Coordinate structure type:", type(coordinates).__name__)
        print("Number of top-level coordinate entries:",
              len(coordinates) if isinstance(coordinates, list) else "N/A")

        print("\nFirst 3 coordinate entries:")
        pprint(coordinates[:3] if isinstance(coordinates, list) else coordinates)
        print("\nLast 3 coordinate entries:")
        pprint(coordinates[-3:] if isinstance(coordinates, list) else coordinates)
    else:
        pprint(path)

    print("\n--- OTHER POSSIBLE TIME FIELDS ---")
    for key, value in flight.items():
        if "time" in key.lower() or "date" in key.lower():
            print(f"{key}:")
            pprint(value)


if __name__ == "__main__":
    main()

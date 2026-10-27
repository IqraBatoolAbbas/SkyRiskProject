
import json
import csv
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "flight_data" / "reports" / "adsbaero_oct20_22_test.json"
OUTPUT = ROOT / "flight_data" / "processed" / "adsbaero_trajectories_oct20_22.csv"

def main():
    report = json.loads(SOURCE.read_text(encoding="utf-8"))
    flights = report.get("flights", [])
    rows = []
    skipped = 0

    for flight in flights:
        path = flight.get("path") or {}
        coordinates = path.get("coordinates") or []
        timestamps = flight.get("timestamps") or []

        point_index = 0
        for segment in coordinates:
            if not isinstance(segment, list):
                continue

            for point in segment:
                if not isinstance(point, list) or len(point) < 2:
                    continue

                lon, lat = point[0], point[1]
                altitude = point[2] if len(point) > 2 else None

                if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                    skipped += 1
                    continue

                # Approximate Pakistan-region bounding check.
                in_region = 60 <= lon <= 78 and 23 <= lat <= 38

                timestamp = None
                if point_index < len(timestamps):
                    timestamp = timestamps[point_index]

                rows.append({
                    "flight_id": flight.get("flight_id"),
                    "icao24": flight.get("icao24"),
                    "callsign": flight.get("callsign"),
                    "timestamp_utc": timestamp,
                    "longitude": lon,
                    "latitude": lat,
                    "altitude_ft_or_source_units": altitude,
                    "point_index": point_index,
                    "inside_approx_region": in_region,
                    "trajectory_source": "ADSB.aero"
                })
                point_index += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "flight_id", "icao24", "callsign", "timestamp_utc",
        "longitude", "latitude", "altitude_ft_or_source_units",
        "point_index", "inside_approx_region", "trajectory_source"
    ]

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    inside = sum(row["inside_approx_region"] for row in rows)
    print("Flight records in source:", len(flights))
    print("CSV trajectory points exported:", len(rows))
    print("Points inside approximate region:", inside)
    print("Invalid coordinate points skipped:", skipped)
    print("CSV saved:", OUTPUT)

if __name__ == "__main__":
    main()

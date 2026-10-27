
import csv
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]

SOURCE = ROOT / "flight_data" / "reports" / "adsbaero_oct20_22_test.json"
OUTPUT = ROOT / "flight_data" / "processed" / "pakistan_region_candidate_points_oct20_22.csv"
REPORT = ROOT / "flight_data" / "reports" / "pakistan_region_candidate_report.json"

# Approximate geographic bounding box only; NOT an official Pakistan FIR boundary.
MIN_LON, MAX_LON = 60.0, 78.0
MIN_LAT, MAX_LAT = 23.0, 38.0


def flatten_segments(value):
    """Flatten nested arrays while retaining segment-level data separately elsewhere."""
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, list):
            result.extend(flatten_segments(item))
        else:
            result.append(item)
    return result


def to_segments(value):
    """Return list of segments for MultiLineString coordinates or nested timestamps."""
    if not isinstance(value, list):
        return []
    if not value:
        return []
    if all(isinstance(v, (int, float)) for v in value):
        return [value]
    return [v for v in value if isinstance(v, list)]


def utc_text(epoch):
    return datetime.fromtimestamp(float(epoch), timezone.utc).isoformat()


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Input JSON not found: {SOURCE}")

    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    flights = data.get("flights", [])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    candidate_flights = set()
    dates = set()

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
        fields = [
            "flight_id", "icao24", "callsign", "icao_type",
            "timestamp_utc", "longitude", "latitude", "altitude_ft",
            "segment_index", "point_index", "source_tile",
            "region_filter"
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for flight in flights:
            path = flight.get("path") or {}
            coords = path.get("coordinates", [])
            timestamps = flight.get("timestamps", [])

            coord_segments = to_segments(coords)
            time_segments = to_segments(timestamps)

            if len(coord_segments) != len(time_segments):
                counts["flights_segment_count_mismatch"] += 1
                continue

            flight_rows = 0
            counts["flights_checked"] += 1

            for seg_i, (coord_seg, time_seg) in enumerate(
                zip(coord_segments, time_segments)
            ):
                if len(coord_seg) != len(time_seg):
                    counts["segments_rejected_count_mismatch"] += 1
                    continue

                previous_time = None

                for point_i, (coord, epoch) in enumerate(zip(coord_seg, time_seg)):
                    if not isinstance(coord, (list, tuple)) or len(coord) < 2:
                        counts["invalid_coordinates"] += 1
                        continue

                    try:
                        lon = float(coord[0])
                        lat = float(coord[1])
                        alt = float(coord[2]) if len(coord) > 2 and coord[2] is not None else ""
                        epoch = float(epoch)
                    except (TypeError, ValueError):
                        counts["invalid_values"] += 1
                        continue

                    if previous_time is not None and epoch < previous_time:
                        counts["segments_rejected_bad_time_order"] += 1
                        break
                    previous_time = epoch

                    counts["valid_points_all_regions"] += 1

                    if not (MIN_LON <= lon <= MAX_LON and MIN_LAT <= lat <= MAX_LAT):
                        continue

                    writer.writerow({
                        "flight_id": flight.get("flight_id", ""),
                        "icao24": flight.get("icao24", ""),
                        "callsign": flight.get("callsign", ""),
                        "icao_type": flight.get("icao_type", ""),
                        "timestamp_utc": utc_text(epoch),
                        "longitude": lon,
                        "latitude": lat,
                        "altitude_ft": alt,
                        "segment_index": seg_i,
                        "point_index": point_i,
                        "source_tile": flight.get("source_tile", ""),
                        "region_filter": "approximate_bbox_not_official_FIR"
                    })

                    flight_rows += 1
                    counts["candidate_points"] += 1
                    candidate_flights.add(flight.get("flight_id", ""))
                    dates.add(utc_text(epoch)[:10])

            if flight_rows:
                counts["flights_with_candidate_points"] += 1

    report = {
        "source_file": str(SOURCE),
        "output_file": str(OUTPUT),
        "date_range_requested": data.get("dates_utc", []),
        "source_flight_records": len(flights),
        "flights_checked": counts["flights_checked"],
        "candidate_unique_flights": len(candidate_flights),
        "candidate_points": counts["candidate_points"],
        "valid_points_all_regions": counts["valid_points_all_regions"],
        "candidate_dates_utc": sorted(dates),
        "approximate_bbox": {
            "longitude_min": MIN_LON,
            "longitude_max": MAX_LON,
            "latitude_min": MIN_LAT,
            "latitude_max": MAX_LAT
        },
        "boundary_warning": (
            "This bounding box is only a preliminary geographic filter. "
            "It is not an official Pakistan FIR boundary and does not prove "
            "that a point belongs to Pakistan airspace."
        ),
        "counts": dict(counts)
    }

    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nPAKISTAN REGION CANDIDATE DATASET COMPLETE")
    print("Source flights:", len(flights))
    print("Flights checked:", counts["flights_checked"])
    print("Candidate unique flights:", len(candidate_flights))
    print("Candidate points:", counts["candidate_points"])
    print("UTC dates:", sorted(dates))
    print("CSV:", OUTPUT)
    print("Report:", REPORT)


if __name__ == "__main__":
    main()

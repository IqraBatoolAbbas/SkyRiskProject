#!/usr/bin/env python3
"""
Audit ADSB.aero trajectory coordinate/timestamp alignment by individual path segment,
then export only segments whose coordinate and timestamp counts match.

Input:
  flight_data/reports/adsbaero_oct20_22_test.json

Outputs:
  flight_data/reports/adsbaero_segment_alignment_audit.json
  flight_data/processed/adsbaero_trajectories_oct20_22_segment_audited.csv

IMPORTANT:
- The Pakistan rectangle below is approximate only, NOT an official FIR boundary.
- A segment is exported only if its own coordinate/timestamp counts match and
  its timestamps are non-decreasing.
- Passing structural checks does not independently prove source-level point pairing.
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT_JSON = ROOT / "flight_data" / "reports" / "adsbaero_oct20_22_test.json"
AUDIT_JSON = ROOT / "flight_data" / "reports" / "adsbaero_segment_alignment_audit.json"
OUTPUT_CSV = ROOT / "flight_data" / "processed" / "adsbaero_trajectories_oct20_22_segment_audited.csv"

# Approximate geographic rectangle only; not Pakistan's official airspace/FIR.
PAKISTAN_BBOX = {
    "min_lon": 60.0,
    "max_lon": 78.0,
    "min_lat": 23.0,
    "max_lat": 38.0,
}


def flatten_numeric_timestamp_segment(value):
    """Return one segment's timestamps as floats, or [] for malformed values."""
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            out.append(float(item))
        else:
            # Do not silently flatten unexpected nested structures.
            return []
    return out


def epoch_to_iso(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def in_approx_bbox(lon, lat):
    return (
        PAKISTAN_BBOX["min_lon"] <= lon <= PAKISTAN_BBOX["max_lon"]
        and PAKISTAN_BBOX["min_lat"] <= lat <= PAKISTAN_BBOX["max_lat"]
    )


def get_segments(record):
    path = record.get("path") or {}
    geometry_type = path.get("type")
    coordinates = path.get("coordinates")

    if not isinstance(coordinates, list):
        return geometry_type, []

    if geometry_type == "MultiLineString":
        return geometry_type, coordinates
    if geometry_type == "LineString":
        return geometry_type, [coordinates]

    return geometry_type, []


def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(
            f"Input not found: {INPUT_JSON}\n"
            "Make sure adsbaero_oct20_22_test.json exists in flight_data/reports."
        )

    with INPUT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    flights = data.get("flights", [])
    if not isinstance(flights, list):
        raise ValueError("Input JSON field 'flights' is not a list.")

    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    audit = {
        "input_file": str(INPUT_JSON),
        "flight_records": len(flights),
        "bbox_used": PAKISTAN_BBOX,
        "bbox_warning": "Approximate rectangle only; not an official Pakistan FIR boundary.",
        "segments_total": 0,
        "segments_exported": 0,
        "segments_rejected": 0,
        "segments_count_mismatch": 0,
        "segments_bad_timestamp_order": 0,
        "unsupported_geometry_records": 0,
        "coordinate_points_total": 0,
        "coordinate_points_exported": 0,
        "points_inside_approx_bbox": 0,
        "points_outside_approx_bbox": 0,
        "flights_with_all_segments_valid": 0,
        "flights_with_some_invalid_segments": 0,
        "flight_checks": [],
    }

    csv_fields = [
        "flight_id", "icao24", "callsign", "icao_type",
        "flight_start_utc", "flight_end_utc",
        "segment_index", "point_index_in_segment",
        "timestamp_epoch_utc", "timestamp_utc",
        "longitude", "latitude", "altitude_ft",
        "inside_approx_pakistan_bbox",
        "segment_alignment_valid",
        "source_tile", "query_date_utc", "ingest_batch_date",
    ]

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writeheader()

        for record in flights:
            flight_id = record.get("flight_id", "")
            geometry_type, coordinate_segments = get_segments(record)
            timestamp_segments_raw = record.get("timestamps")
            if not isinstance(timestamp_segments_raw, list):
                timestamp_segments_raw = []

            # Expected source structure: one timestamp list per coordinate segment.
            flight_segment_count = len(coordinate_segments)
            timestamp_segment_count = len(timestamp_segments_raw)
            segment_results = []
            all_segments_valid = True

            if not coordinate_segments:
                audit["unsupported_geometry_records"] += 1

            for seg_idx, coords in enumerate(coordinate_segments):
                audit["segments_total"] += 1
                audit["coordinate_points_total"] += len(coords) if isinstance(coords, list) else 0

                raw_ts_segment = (
                    timestamp_segments_raw[seg_idx]
                    if seg_idx < len(timestamp_segments_raw)
                    else None
                )
                ts_values = flatten_numeric_timestamp_segment(raw_ts_segment)
                coords_ok = isinstance(coords, list)
                count_match = coords_ok and len(coords) == len(ts_values)

                ordered = all(
                    ts_values[i] <= ts_values[i + 1]
                    for i in range(len(ts_values) - 1)
                ) if ts_values else False

                segment_valid = bool(count_match and ordered)
                if not count_match:
                    audit["segments_count_mismatch"] += 1
                if count_match and not ordered:
                    audit["segments_bad_timestamp_order"] += 1
                if not segment_valid:
                    audit["segments_rejected"] += 1
                    all_segments_valid = False
                else:
                    audit["segments_exported"] += 1

                    for point_idx, (coord, epoch) in enumerate(zip(coords, ts_values)):
                        if not isinstance(coord, list) or len(coord) < 2:
                            continue
                        try:
                            lon = float(coord[0])
                            lat = float(coord[1])
                            alt = float(coord[2]) if len(coord) > 2 and coord[2] is not None else ""
                        except (TypeError, ValueError):
                            continue

                        inside = in_approx_bbox(lon, lat)
                        if inside:
                            audit["points_inside_approx_bbox"] += 1
                        else:
                            audit["points_outside_approx_bbox"] += 1
                        audit["coordinate_points_exported"] += 1

                        writer.writerow({
                            "flight_id": flight_id,
                            "icao24": record.get("icao24", ""),
                            "callsign": record.get("callsign", ""),
                            "icao_type": record.get("icao_type", ""),
                            "flight_start_utc": record.get("start_ts", ""),
                            "flight_end_utc": record.get("end_ts", ""),
                            "segment_index": seg_idx,
                            "point_index_in_segment": point_idx,
                            "timestamp_epoch_utc": f"{epoch:.3f}",
                            "timestamp_utc": epoch_to_iso(epoch),
                            "longitude": lon,
                            "latitude": lat,
                            "altitude_ft": alt,
                            "inside_approx_pakistan_bbox": inside,
                            "segment_alignment_valid": True,
                            "source_tile": record.get("source_tile", ""),
                            "query_date_utc": record.get("query_date_utc", ""),
                            "ingest_batch_date": record.get("ingest_batch_date", ""),
                        })

                segment_results.append({
                    "segment_index": seg_idx,
                    "coordinate_count": len(coords) if isinstance(coords, list) else None,
                    "timestamp_count": len(ts_values),
                    "count_match": bool(count_match),
                    "timestamps_non_decreasing": bool(ordered),
                    "exported": segment_valid,
                })

            if timestamp_segment_count != flight_segment_count:
                all_segments_valid = False

            if all_segments_valid and flight_segment_count > 0 and timestamp_segment_count == flight_segment_count:
                audit["flights_with_all_segments_valid"] += 1
            else:
                audit["flights_with_some_invalid_segments"] += 1

            audit["flight_checks"].append({
                "flight_id": flight_id,
                "geometry_type": geometry_type,
                "coordinate_segment_count": flight_segment_count,
                "timestamp_segment_count": timestamp_segment_count,
                "all_segments_valid": bool(
                    all_segments_valid and flight_segment_count > 0
                    and timestamp_segment_count == flight_segment_count
                ),
                "segments": segment_results,
            })

    with AUDIT_JSON.open("w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    print("SEGMENT-WISE ALIGNMENT AUDIT COMPLETE")
    print(f"Flight records: {audit['flight_records']}")
    print(f"Segments total: {audit['segments_total']}")
    print(f"Segments exported: {audit['segments_exported']}")
    print(f"Segments rejected: {audit['segments_rejected']}")
    print(f"Segments with coordinate/timestamp count mismatch: {audit['segments_count_mismatch']}")
    print(f"Segments with bad timestamp order: {audit['segments_bad_timestamp_order']}")
    print(f"Flights with all segments valid: {audit['flights_with_all_segments_valid']}")
    print(f"Flights with some invalid segments: {audit['flights_with_some_invalid_segments']}")
    print(f"Exported points: {audit['coordinate_points_exported']}")
    print(f"Points inside approximate bbox: {audit['points_inside_approx_bbox']}")
    print(f"Points outside approximate bbox: {audit['points_outside_approx_bbox']}")
    print(f"Audit JSON: {AUDIT_JSON}")
    print(f"Audited CSV: {OUTPUT_CSV}")
    print("WARNING: bbox is approximate, not an official FIR; alignment checks are structural.")


if __name__ == "__main__":
    main()

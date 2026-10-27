"""Build reproducible historical outputs from downloaded public sources."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import Point, shape
from shapely.prepared import prep

ROOT = Path(__file__).parent
RAW = ROOT / "raw"
PROCESSED = ROOT / "processed"
REPORTS = ROOT / "reports"
START = pd.Timestamp("2026-10-10T00:00:00Z")
END = pd.Timestamp("2026-10-16T00:00:00Z")
KEY = ["flight_id", "segment_index", "point_index"]


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    for i, current in enumerate(ring):
        previous = ring[i - 1]
        x1, y1 = previous[:2]
        x2, y2 = current[:2]
        crosses = ((y1 > lat) != (y2 > lat)) and (
            lon < (x2 - x1) * (lat - y1) / ((y2 - y1) or 1e-30) + x1
        )
        if crosses:
            inside = not inside
    return inside


def pakistan_geometry() -> dict:
    geojson = json.loads((RAW / "countries.geojson").read_text(encoding="utf-8"))
    for feature in geojson["features"]:
        props = feature.get("properties", {})
        names = [props.get(k) for k in ("name", "ADMIN", "name_en", "formal_en")]
        if any(str(value).strip().lower() == "pakistan" for value in names):
            return feature["geometry"]
    raise RuntimeError("Pakistan boundary was not found in countries.geojson")


def flatten_trajectories() -> pd.DataFrame:
    flights = json.loads(
        (RAW / "adsb_api_raw_2026-10-10_2026-10-15.json").read_text(
            encoding="utf-8"
        )
    )
    geometry = pakistan_geometry()
    pakistan = prep(shape(geometry))
    min_lon, min_lat, max_lon, max_lat = shape(geometry).bounds
    rows: list[dict] = []
    malformed: list[dict] = []
    for flight in flights:
        fid = flight.get("flight_id")
        path = flight.get("path") or {}
        segments = path.get("coordinates") or []
        timestamps = flight.get("timestamps") or []
        if len(segments) != len(timestamps):
            malformed.append({"flight_id": fid, "reason": "segment_count_mismatch"})
            continue
        for segment_index, (coordinates, times) in enumerate(
            zip(segments, timestamps)
        ):
            if len(coordinates) != len(times):
                malformed.append({
                    "flight_id": fid,
                    "segment_index": segment_index,
                    "reason": "point_timestamp_count_mismatch",
                })
                continue
            for point_index, (coordinate, timestamp) in enumerate(
                zip(coordinates, times)
            ):
                if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
                    continue
                try:
                    lon, lat, timestamp = (
                        float(coordinate[0]),
                        float(coordinate[1]),
                        float(timestamp),
                    )
                except (TypeError, ValueError):
                    continue
                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    continue
                if not (
                    min_lon <= lon <= max_lon and min_lat <= lat <= max_lat
                ):
                    continue
                if pakistan.covers(Point(lon, lat)):
                    rows.append({
                        "flight_id": fid,
                        "icao24": flight.get("icao24"),
                        "callsign": flight.get("callsign"),
                        "icao_type": flight.get("icao_type"),
                        "timestamp_utc": pd.Timestamp(
                            timestamp, unit="s", tz="UTC"
                        ).isoformat(),
                        "longitude": lon,
                        "latitude": lat,
                        "altitude_ft": (
                            float(coordinate[2])
                            if len(coordinate) > 2 and coordinate[2] is not None
                            else np.nan
                        ),
                        "segment_index": segment_index,
                        "point_index": point_index,
                        "trajectory_source": "adsb.aero API / adsb.lol archive",
                    })
    points = pd.DataFrame(rows)
    if points.empty:
        raise RuntimeError("No trajectory points were returned inside Pakistan")
    points["timestamp_utc"] = pd.to_datetime(
        points["timestamp_utc"], utc=True, errors="coerce"
    )
    points = points[
        points["timestamp_utc"].between(START, END, inclusive="left")
    ].sort_values(KEY).reset_index(drop=True)
    points.to_csv(PROCESSED / "trajectory_points_pakistan_2026-10-10_2026-10-15.csv", index=False)
    pd.DataFrame(malformed).to_csv(REPORTS / "malformed_trajectory_records.csv", index=False)
    return points


def add_trajectory_indicators(points: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame = points.copy()
    grouped = frame.groupby(["flight_id", "segment_index"], sort=False)
    frame["next_timestamp_utc"] = grouped["timestamp_utc"].shift(-1)
    frame["next_latitude"] = grouped["latitude"].shift(-1)
    frame["next_longitude"] = grouped["longitude"].shift(-1)
    lat1, lat2 = np.radians(frame["latitude"]), np.radians(frame["next_latitude"])
    dlat = lat2 - lat1
    dlon = np.radians(frame["next_longitude"] - frame["longitude"])
    haversine = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    frame["distance_km_to_next"] = 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(haversine, 0, 1)))
    frame["time_gap_seconds"] = (
        frame["next_timestamp_utc"] - frame["timestamp_utc"]
    ).dt.total_seconds()
    frame["derived_speed_kmh"] = frame["distance_km_to_next"] / (
        frame["time_gap_seconds"] / 3600
    )
    frame["trajectory_quality_warning"] = (
        frame["time_gap_seconds"].le(0)
        | frame["time_gap_seconds"].gt(900)
        | frame["derived_speed_kmh"].gt(1200)
        | frame[KEY].isna().any(axis=1)
    )
    frame.to_csv(PROCESSED / "trajectory_point_indicators.csv", index=False)
    segment = frame.groupby(["flight_id", "segment_index"], as_index=False).agg(
        point_count=("point_index", "size"),
        first_timestamp_utc=("timestamp_utc", "min"),
        last_timestamp_utc=("timestamp_utc", "max"),
        max_derived_speed_kmh=("derived_speed_kmh", "max"),
        max_time_gap_seconds=("time_gap_seconds", "max"),
        quality_warning_count=("trajectory_quality_warning", "sum"),
    )
    segment.to_csv(PROCESSED / "trajectory_segment_indicators.csv", index=False)
    flight = segment.groupby("flight_id", as_index=False).agg(
        segment_count=("segment_index", "nunique"),
        point_count=("point_count", "sum"),
        first_timestamp_utc=("first_timestamp_utc", "min"),
        last_timestamp_utc=("last_timestamp_utc", "max"),
        max_derived_speed_kmh=("max_derived_speed_kmh", "max"),
        max_time_gap_seconds=("max_time_gap_seconds", "max"),
        quality_warning_count=("quality_warning_count", "sum"),
    )
    flight.to_csv(PROCESSED / "trajectory_flight_indicators.csv", index=False)
    return frame, segment, flight


def integrate_kp(frame: pd.DataFrame) -> pd.DataFrame:
    raw = json.loads((RAW / "noaa_planetary_k_index.json").read_text(encoding="utf-8"))
    kp = pd.DataFrame(raw)
    kp["timestamp_utc"] = pd.to_datetime(kp["time_tag"], utc=True, errors="coerce")
    kp["timestamp_utc"] = kp["timestamp_utc"].dt.as_unit("ns")
    kp["Kp"] = pd.to_numeric(kp["Kp"], errors="coerce")
    kp = kp[["timestamp_utc", "Kp", "a_running", "station_count"]].dropna()
    kp = kp[kp["timestamp_utc"].between(START, END, inclusive="left")]
    kp.to_csv(PROCESSED / "noaa_kp_2026-10-10_2026-10-15.csv", index=False)
    result = pd.merge_asof(
        frame.assign(timestamp_utc=frame["timestamp_utc"].dt.as_unit("ns")).sort_values("timestamp_utc"),
        kp.sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
        tolerance=pd.Timedelta("3h"),
    )
    result["space_weather_warning"] = result["Kp"].isna()
    result.to_csv(PROCESSED / "historical_trajectory_kp_integrated.csv", index=False)
    return result


def export_weather_reference() -> pd.DataFrame:
    source = json.loads(
        (RAW / "open_meteo_pakistan_reference_2026-10-10_2026-10-15.json").read_text(
            encoding="utf-8"
        )
    )
    hourly = pd.DataFrame(source["hourly"])
    hourly["timestamp_utc"] = pd.to_datetime(hourly.pop("time"), utc=True)
    hourly["weather_source_latitude"] = source["latitude"]
    hourly["weather_source_longitude"] = source["longitude"]
    hourly["weather_spatial_match_status"] = "reference_grid_only_not_trajectory_join"
    hourly.to_csv(PROCESSED / "open_meteo_reference_hourly.csv", index=False)
    return hourly


def integrate_swips(frame: pd.DataFrame) -> pd.DataFrame:
    path = PROCESSED / "swips_qc_observations.csv"
    if not path.exists():
        return frame
    swips = pd.read_csv(path, parse_dates=["timestamp_utc"])
    swips["timestamp_utc"] = pd.to_datetime(swips["timestamp_utc"], utc=True).dt.as_unit("ns")
    swips = swips.sort_values("timestamp_utc")
    result = pd.merge_asof(
        frame.assign(timestamp_utc=frame["timestamp_utc"].dt.as_unit("ns")).sort_values("timestamp_utc"),
        swips[
            [
                "timestamp_utc",
                "flags_raw",
                "backfill_raw",
                "source_file",
            ]
        ],
        on="timestamp_utc",
        direction="nearest",
        tolerance=pd.Timedelta("5min"),
    )
    result["swips_match_status"] = np.where(
        result["flags_raw"].notna(),
        "matched_time_only_l1_spacecraft_indicator",
        "unmatched",
    )
    result["swips_velocity_used"] = False
    result.to_csv(PROCESSED / "historical_trajectory_quality_integrated.csv", index=False)
    return result


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    points = flatten_trajectories()
    frame, segment, flight = add_trajectory_indicators(points)
    integrated = integrate_kp(frame)
    weather = export_weather_reference()
    quality_integrated = integrate_swips(integrated)
    report = {
        "study_window_start_utc": START.isoformat(),
        "study_window_end_utc_exclusive": END.isoformat(),
        "trajectory_points_inside_pakistan": len(points),
        "trajectory_flights": int(points["flight_id"].nunique()),
        "trajectory_segments": int(points[["flight_id", "segment_index"]].drop_duplicates().shape[0]),
        "kp_rows": len(integrated),
        "kp_unmatched_rows": int(integrated["Kp"].isna().sum()),
        "weather_reference_rows": len(weather),
        "weather_trajectory_joined": False,
        "trajectory_quality_warning_rows": int(frame["trajectory_quality_warning"].sum()),
        "space_weather_warning_rows": int(integrated["space_weather_warning"].sum()),
        "swips_quality_time_matches": int(
            (quality_integrated["swips_match_status"] != "unmatched").sum()
        ) if "swips_match_status" in quality_integrated else 0,
        "notes": [
            "Weather is retained as a documented Pakistan reference grid, not joined to trajectory points because a single grid point is not a defensible spatial match for every flight point.",
            "Kp is a global geomagnetic indicator and is not presented as a direct aviation hazard limit.",
            "SWiPS quality fields were time-matched only where files existed; no SWiPS velocity-derived hazard indicator was created because the checked variable metadata do not establish units for the combined velocity vectors.",
        ],
    }
    (REPORTS / "historical_analysis_summary.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

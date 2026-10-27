
import json
import urllib.request
import urllib.error
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "flight_data" / "reports" / "adsbaero_pakistan_test.json"
BASE = "https://adsb.aero/api/v1"

# Pakistan ka approximate bounding area.
MIN_LON, MAX_LON = 60, 78
MIN_LAT, MAX_LAT = 23, 38

# Chhote tiles: har tile ki geometry alag query hogi.
GRID_COLS = 3
GRID_ROWS = 3

# Har tile par maximum flights to retrieve in this initial test.
PAGE_LIMIT = 20
MAX_PAGES_PER_TILE = 5


def request_json(url, method="GET", payload=None):
    headers = {"User-Agent": "SkyRisk-FYP-Research"}
    body = None

    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url, data=body, headers=headers, method=method
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"HTTP {exc.code}: {details}"
        ) from exc


def make_tiles():
    tiles = []
    lon_step = (MAX_LON - MIN_LON) / GRID_COLS
    lat_step = (MAX_LAT - MIN_LAT) / GRID_ROWS

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            west = MIN_LON + col * lon_step
            east = MIN_LON + (col + 1) * lon_step
            south = MIN_LAT + row * lat_step
            north = MIN_LAT + (row + 1) * lat_step

            polygon = {
                "type": "Polygon",
                "coordinates": [[
                    [west, south],
                    [east, south],
                    [east, north],
                    [west, north],
                    [west, south],
                ]],
            }

            tiles.append({
                "tile_id": f"R{row + 1}_C{col + 1}",
                "bounds": [west, south, east, north],
                "geometry": polygon,
            })

    return tiles


def main():
    report = {
        "source": BASE,
        "database_changed": False,
        "full_archive_downloaded": False,
        "region": "Approximate Pakistan bounding rectangle",
        "grid_rows": GRID_ROWS,
        "grid_cols": GRID_COLS,
        "tiles": [],
        "unique_flights": [],
        "warnings": [
            "A bounding rectangle includes areas outside Pakistan.",
            "Zero results do not prove that no flights operated.",
            "This is a limited test, not a complete archive export.",
        ],
    }

    try:
        data_range = request_json(f"{BASE}/data-range")
        report["data_range"] = data_range
        print("Available data range:", data_range)

        first_date = date.fromisoformat(data_range["first_date"])
        last_date = date.fromisoformat(data_range["last_date"])

        # Test the latest date listed by the API.
        query_date = last_date
        next_date = query_date + timedelta(days=1)

        if query_date < first_date:
            raise RuntimeError("API date range is invalid.")

        report["query_date_utc"] = query_date.isoformat()
        unique = {}

        for tile in make_tiles():
            tile_report = {
                "tile_id": tile["tile_id"],
                "bounds_lon_lat": tile["bounds"],
                "flights_returned": 0,
                "pages_read": 0,
                "error": None,
            }

            print(f"\nQuerying {tile['tile_id']}...")

            cursor = None

            for page_number in range(MAX_PAGES_PER_TILE):
                payload = {
                    "match": {
                        "trajectory_intersects": {
                            "geometry": tile["geometry"],
                            "time_from": query_date.isoformat()
                            + "T00:00:00Z",
                            "time_to": next_date.isoformat()
                            + "T00:00:00Z",
                        }
                    },
                    "start_from": query_date.isoformat()
                    + "T00:00:00Z",
                    "end_date": next_date.isoformat()
                    + "T00:00:00Z",
                    "window_days": 1,
                    "limit": PAGE_LIMIT,
                    "include_path": True,
                }

                if cursor:
                    payload["cursor"] = cursor

                try:
                    result = request_json(
                        f"{BASE}/query",
                        method="POST",
                        payload=payload,
                    )
                except Exception as exc:
                    tile_report["error"] = str(exc)
                    print("  Tile query error:", exc)
                    break

                flights = result.get("flights", [])
                tile_report["pages_read"] += 1
                tile_report["flights_returned"] += len(flights)

                for flight in flights:
                    flight_id = flight.get("flight_id")
                    if not flight_id:
                        continue

                    path = flight.get("path") or {}
                    coordinates = path.get("coordinates") or []
                    point_count = sum(
                        len(segment)
                        for segment in coordinates
                        if isinstance(segment, list)
                    )

                    # Deduplicate by stable flight ID across tiles/pages.
                    unique[flight_id] = {
                        "flight_id": flight_id,
                        "icao24": flight.get("icao24"),
                        "callsign": flight.get("callsign"),
                        "start_ts": flight.get("start_ts"),
                        "end_ts": flight.get("end_ts"),
                        "point_count": flight.get("point_count"),
                        "raw_point_count": flight.get("raw_point_count"),
                        "path_coordinate_count": point_count,
                        "start_airport_ident": flight.get(
                            "start_airport_ident"
                        ),
                        "end_airport_ident": flight.get(
                            "end_airport_ident"
                        ),
                        "path": path,
                        "timestamps": flight.get("timestamps"),
                        "path_gs": flight.get("path_gs"),
                        "source_tile": tile["tile_id"],
                    }

                cursor = result.get("cursor")
                print(
                    f"  Page {page_number + 1}: "
                    f"{len(flights)} flights"
                )

                if not cursor:
                    break

            report["tiles"].append(tile_report)

        report["unique_flights"] = list(unique.values())
        report["unique_flight_count"] = len(unique)
        report["total_tile_queries"] = len(report["tiles"])
        report["tiles_with_errors"] = sum(
            1 for tile in report["tiles"] if tile["error"]
        )
        report["tiles_with_results"] = sum(
            1 for tile in report["tiles"]
            if tile["flights_returned"] > 0
        )

        print("\nUnique flights after combining:", len(unique))
        print("Tiles with results:", report["tiles_with_results"])
        print("Tiles with errors:", report["tiles_with_errors"])

    except Exception as exc:
        report["error"] = str(exc)
        print("Test failed:", exc)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\nReport saved to:", REPORT)
    print("No database changes were made.")


if __name__ == "__main__":
    main()

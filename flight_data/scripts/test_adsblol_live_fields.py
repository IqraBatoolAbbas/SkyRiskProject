
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "flight_data" / "reports"
REPORT_FILE = REPORT_DIR / "adsblol_live_fields_test.json"

# Approximate city/airport-area reference points.
# Radius is in nautical miles.
TEST_LOCATIONS = {
    "Lahore": {"lat": 31.5216, "lon": 74.4036, "radius_nm": 100},
    "Karachi": {"lat": 24.9065, "lon": 67.1608, "radius_nm": 100},
    "Islamabad": {"lat": 33.6167, "lon": 73.0992, "radius_nm": 100},
}

API_BASE = "https://api.adsb.lol/v2/point"
TIMEOUT_SECONDS = 25

FIELD_MAP = {
    "timestamp": ["now", "seen_pos", "seen"],
    "latitude": ["lat"],
    "longitude": ["lon"],
    "altitude": ["alt_baro", "alt_geom"],
    "ground_speed": ["gs"],
    "track_or_heading": ["track"],
    "flight_or_aircraft_identifier": ["flight", "hex"],
}


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "SkyRisk-FYP-Data-Availability-Test/1.0"},
    )

    with urllib.request.urlopen(
        request, timeout=TIMEOUT_SECONDS
    ) as response:
        return json.loads(response.read().decode("utf-8"))


def field_available(aircraft, possible_keys):
    return any(
        aircraft.get(key) is not None
        and aircraft.get(key) != ""
        for key in possible_keys
    )


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "source": "ADSB.lol live API",
        "api_base": API_BASE,
        "test_time_utc": datetime.now(timezone.utc).isoformat(),
        "historical_data_tested": False,
        "locations": {},
        "limitations": [
            "This tests a live snapshot, not historical trajectories.",
            "A returned aircraft is not automatically a Pakistan flight.",
            "Position near an airport does not prove runway usage.",
            "No returned aircraft does not prove no flights occurred.",
            "API coverage may vary by location and time.",
        ],
    }

    for location_name, location in TEST_LOCATIONS.items():
        lat = location["lat"]
        lon = location["lon"]
        radius = location["radius_nm"]

        url = (
            f"{API_BASE}/{lat}/{lon}/{radius}"
        )

        print(f"\nChecking {location_name}...")

        result = {
            "query_url": url,
            "reference_coordinates": location,
            "request_success": False,
            "reported_total": None,
            "aircraft_returned": 0,
            "field_availability": {},
            "sample_aircraft": [],
            "error": None,
        }

        try:
            data = get_json(url)
            aircraft_list = data.get("aircraft", [])

            result["request_success"] = True
            result["reported_total"] = data.get("total")
            result["aircraft_returned"] = len(aircraft_list)

            for field, possible_keys in FIELD_MAP.items():
                count = sum(
                    field_available(aircraft, possible_keys)
                    for aircraft in aircraft_list
                )
                result["field_availability"][field] = {
                    "available_count": count,
                    "aircraft_count": len(aircraft_list),
                    "coverage_percent": (
                        round(100 * count / len(aircraft_list), 1)
                        if aircraft_list else None
                    ),
                    "source_keys": possible_keys,
                }

            # Save only a few examples in the report.
            for aircraft in aircraft_list[:5]:
                result["sample_aircraft"].append({
                    "hex": aircraft.get("hex"),
                    "flight": aircraft.get("flight"),
                    "lat": aircraft.get("lat"),
                    "lon": aircraft.get("lon"),
                    "alt_baro": aircraft.get("alt_baro"),
                    "alt_geom": aircraft.get("alt_geom"),
                    "gs": aircraft.get("gs"),
                    "track": aircraft.get("track"),
                    "seen": aircraft.get("seen"),
                    "seen_pos": aircraft.get("seen_pos"),
                })

            print(f"  Aircraft returned: {len(aircraft_list)}")
            for field, details in result["field_availability"].items():
                print(
                    f"  {field}: "
                    f"{details['available_count']}/"
                    f"{details['aircraft_count']}"
                )

        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            result["error"] = str(exc)
            print(f"  Request failed: {exc}")

        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  Unexpected error: {result['error']}")

        report["locations"][location_name] = result

        # Avoid sending requests too quickly.
        time.sleep(1)

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n===== ADSB.LOL LIVE FIELD TEST =====")
    for name, result in report["locations"].items():
        print(
            f"{name}: success={result['request_success']}, "
            f"aircraft={result['aircraft_returned']}"
        )

    print(f"\nReport saved to:\n{REPORT_FILE}")
    print("No database or existing backend files were changed.")
    print("Historical trajectory availability remains unverified.")


if __name__ == "__main__":
    main()


import json
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "weather_module" / "reports"
REPORT_FILE = REPORT_DIR / "weather_source_coverage.json"

# Current flight dataset ki target dates
START_DATE = date(2026, 10, 20)
END_DATE = date(2026, 10, 22)

# Open-Meteo historical archive availability check.
# This is only a source-availability test, not a flight-local weather join.
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

PARAMS = {
    "latitude": 30.474516,
    "longitude": 68.531136,
    "start_date": START_DATE.isoformat(),
    "end_date": END_DATE.isoformat(),
    "hourly": (
        "temperature_2m,relative_humidity_2m,precipitation,"
        "pressure_msl,cloud_cover,wind_speed_10m,"
        "wind_speed_100m,wind_direction_10m,"
        "wind_direction_100m,wind_gusts_10m"
    ),
    "timezone": "UTC",
}

def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "source": "Open-Meteo Historical Weather API",
        "url": BASE_URL,
        "requested_start_date": START_DATE.isoformat(),
        "requested_end_date": END_DATE.isoformat(),
        "reference_latitude": PARAMS["latitude"],
        "reference_longitude": PARAMS["longitude"],
        "status": "NOT_CHECKED",
        "hourly_rows": 0,
        "available_times": [],
        "limitations": [
            "This checks one reference coordinate only.",
            "It does not establish weather at each flight coordinate.",
            "It does not create a flight-local weather match.",
        ],
    }

    query = "&".join(
        f"{key}={urllib.parse.quote(str(value))}"
        for key, value in PARAMS.items()
    )
    request = urllib.request.Request(
        f"{BASE_URL}?{query}",
        headers={"User-Agent": "SkyRiskAuditor/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))

        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])

        report["status"] = "SUCCESS"
        report["hourly_rows"] = len(times)
        report["available_times"] = [
            times[0], times[-1]
        ] if times else []
        report["hourly_columns"] = list(hourly.keys())
        report["api_timezone"] = payload.get("timezone")
        report["api_response_elevation"] = payload.get("elevation")

        # Save downloaded reference data as a separate raw CSV.
        import csv

        data_path = ROOT / "weather_module" / "data"
        data_path.mkdir(parents=True, exist_ok=True)
        csv_path = data_path / "open_meteo_reference_2026-10-20_22.csv"

        columns = list(hourly.keys())
        with csv_path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            for index in range(len(times)):
                writer.writerow([
                    hourly[column][index]
                    for column in columns
                ])

        report["saved_csv"] = str(csv_path)

    except Exception as error:
        report["status"] = "FAILED"
        report["error"] = f"{type(error).__name__}: {error}"

    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nReport saved: {REPORT_FILE}")


if __name__ == "__main__":
    main()

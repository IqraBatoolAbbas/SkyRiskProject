
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "flight_data" / "reports"
REPORT_FILE = REPORT_DIR / "historical_flight_source_check.json"

# Public dataset metadata endpoint
HF_DATASET_API = (
    "https://huggingface.co/api/datasets/"
    "SANIKKI/tartanaviation-adsb-19k-clean"
)

# Approximate bounding box around Pakistan.
# This is a live snapshot query, NOT a historical-data query.
OPENSKY_LIVE_API = (
    "https://opensky-network.org/api/states/all"
    "?lamin=23&lomin=60&lamax=38&lomax=78"
)

TIMEOUT = 25


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "SkyRisk-FYP-Source-Check/1.0"},
    )

    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def check_huggingface():
    result = {
        "source": "Hugging Face published ADS-B dataset",
        "url": HF_DATASET_API,
        "success": False,
        "dataset_id": "SANIKKI/tartanaviation-adsb-19k-clean",
        "metadata": {},
        "error": None,
    }

    try:
        data = fetch_json(HF_DATASET_API)
        result["success"] = True
        result["metadata"] = {
            "id": data.get("id"),
            "downloads": data.get("downloads"),
            "likes": data.get("likes"),
            "last_modified": data.get("lastModified"),
            "siblings": [
                item.get("rfilename")
                for item in data.get("siblings", [])
            ],
        }
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


def check_opensky_live():
    result = {
        "source": "OpenSky live API",
        "url": OPENSKY_LIVE_API,
        "success": False,
        "aircraft_returned": 0,
        "fields": [],
        "sample_states": [],
        "historical_data_checked": False,
        "error": None,
    }

    try:
        data = fetch_json(OPENSKY_LIVE_API)
        states = data.get("states") or []

        result["success"] = True
        result["aircraft_returned"] = len(states)

        # OpenSky state-vector field indexes
        field_names = [
            "icao24",
            "callsign",
            "origin_country",
            "time_position",
            "last_contact",
            "longitude",
            "latitude",
            "barometric_altitude",
            "on_ground",
            "velocity",
            "true_track",
            "vertical_rate",
            "sensors",
            "geo_altitude",
            "squawk",
            "spi",
            "position_source",
        ]

        result["fields"] = field_names

        for state in states[:5]:
            result["sample_states"].append({
                field_names[i]: state[i]
                for i in range(min(len(state), len(field_names)))
            })

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Checking published dataset metadata...")
    hf = check_huggingface()
    print("Metadata request successful:", hf["success"])

    if hf["success"]:
        print("Dataset ID:", hf["metadata"].get("id"))
        print("Files listed:", len(hf["metadata"].get("siblings", [])))
        for filename in hf["metadata"].get("siblings", []):
            print("  -", filename)
    else:
        print("Metadata error:", hf["error"])

    print("\nChecking OpenSky live API...")
    opensky = check_opensky_live()
    print("Request successful:", opensky["success"])
    print("Aircraft returned:", opensky["aircraft_returned"])

    if opensky["error"]:
        print("OpenSky error:", opensky["error"])

    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Historical flight-source discovery",
        "huggingface_dataset": hf,
        "opensky_live": opensky,
        "notes": [
            "Dataset metadata does not prove Pakistan coverage.",
            "The published sample dataset is reported to cover Ohio, USA.",
            "OpenSky result is a live snapshot, not a historical track test.",
            "Historical OpenSky database access may require research approval.",
            "No dataset files were downloaded.",
            "No database changes were made.",
        ],
    }

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\nReport saved to:")
    print(REPORT_FILE)
    print("\nNo database changes were made.")


if __name__ == "__main__":
    main()

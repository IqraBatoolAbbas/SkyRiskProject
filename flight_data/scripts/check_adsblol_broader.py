
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

# Broader live coverage probe over a few separate locations.
LOCATIONS = [
    {"name": "Lahore", "lat": 31.5204, "lon": 74.3587},
    {"name": "Karachi", "lat": 24.8607, "lon": 67.0011},
    {"name": "Islamabad", "lat": 33.6844, "lon": 73.0479},
]

RADIUS_NM = 100
ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "flight_data" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

report = {
    "source": "ADSB.lol live API",
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "small multi-location live coverage probe",
    "results": [],
}

for place in LOCATIONS:
    url = (
        f"https://api.adsb.lol/v2/point/"
        f"{place['lat']}/{place['lon']}/{RADIUS_NM}"
    )

    item = {"location": place["name"], "url": url}

    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "SkyRisk-Auditor-Academic-Prototype",
            },
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        aircraft = data.get("ac", [])
        item["result"] = "success"
        item["total_reported"] = data.get("total", len(aircraft))
        item["aircraft_returned"] = len(aircraft)
        item["sample"] = [
            {
                "hex": ac.get("hex"),
                "callsign": ac.get("flight"),
                "latitude": ac.get("lat"),
                "longitude": ac.get("lon"),
                "altitude": ac.get("alt_baro"),
                "ground_speed": ac.get("gs"),
                "track": ac.get("track"),
                "position_age_seconds": ac.get("seen_pos"),
            }
            for ac in aircraft[:3]
        ]

    except urllib.error.HTTPError as exc:
        item["result"] = "http_error"
        item["http_status"] = exc.code
        item["details"] = exc.read().decode(
            "utf-8", errors="replace"
        )[:500]

    except Exception as exc:
        item["result"] = "request_failed"
        item["details"] = str(exc)

    report["results"].append(item)

out = REPORT_DIR / "adsblol_broader_probe.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")

print(json.dumps(report, indent=2))
print(f"\nReport saved to: {out}")

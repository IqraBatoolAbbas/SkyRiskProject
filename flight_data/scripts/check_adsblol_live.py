
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

# Approximate geographic centre of Pakistan.
# Radius is in nautical miles; this is a coverage probe,
# not a complete representation of Pakistan airspace.
LAT = 30.3753
LON = 69.3451
RADIUS_NM = 250

URL = (
    f"https://api.adsb.lol/v2/point/"
    f"{LAT}/{LON}/{RADIUS_NM}"
)

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "flight_data" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

report = {
    "source": "ADSB.lol live API",
    "url": URL,
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "small live coverage test",
}

try:
    req = urllib.request.Request(
        URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "SkyRisk-Auditor-Academic-Prototype",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    aircraft = data.get("ac", [])

    report["result"] = "success"
    report["total_reported"] = data.get("total", len(aircraft))
    report["aircraft_returned"] = len(aircraft)
    report["sample"] = []

    for ac in aircraft[:10]:
        report["sample"].append({
            "hex": ac.get("hex"),
            "callsign": ac.get("flight"),
            "latitude": ac.get("lat"),
            "longitude": ac.get("lon"),
            "altitude": ac.get("alt_baro"),
            "ground_speed": ac.get("gs"),
            "track": ac.get("track"),
            "position_age_seconds": ac.get("seen_pos"),
        })

except urllib.error.HTTPError as exc:
    report["result"] = "http_error"
    report["http_status"] = exc.code
    report["details"] = exc.read().decode(
        "utf-8", errors="replace"
    )[:1000]

except Exception as exc:
    report["result"] = "request_failed"
    report["details"] = str(exc)

out = REPORT_DIR / "adsblol_live_probe.json"
out.write_text(json.dumps(report, indent=2), encoding="utf-8")

print(json.dumps(report, indent=2))
print(f"\nReport saved to: {out}")

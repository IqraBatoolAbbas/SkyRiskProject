
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "flight_data" / "reports" / "adsbaero_general_test.json"
URL = "https://adsb.aero/api/v1/query"

payload = {
    "limit": 5,
    "include_path": False
}

req = urllib.request.Request(
    URL,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "User-Agent": "SkyRisk-FYP-Research",
    },
    method="POST",
)

report = {
    "source": URL,
    "database_changed": False,
    "archive_downloaded": False,
}

try:
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    flights = result.get("flights", [])
    report["returned_count"] = len(flights)
    report["cursor_present"] = result.get("cursor") is not None
    report["flights"] = [
        {
            "flight_id": f.get("flight_id"),
            "callsign": f.get("callsign"),
            "start_ts": f.get("start_ts"),
            "end_ts": f.get("end_ts"),
        }
        for f in flights
    ]

    print("Flights returned:", len(flights))
    for flight in report["flights"]:
        print(flight)

except Exception as exc:
    report["error"] = str(exc)
    print("Test failed:", exc)

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("Report saved to:", REPORT)
print("No database changes were made.")

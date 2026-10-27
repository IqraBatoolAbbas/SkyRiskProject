
import json
import urllib.error
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

BASE_URL = "https://adsb.aero/api/v1"
ENDPOINT = f"{BASE_URL}/data-range"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

report = {
    "source": "adsb.aero",
    "endpoint": ENDPOINT,
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "check_type": "metadata_only",
}

try:
    request = urllib.request.Request(
        ENDPOINT,
        headers={"Accept": "application/json"},
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        report["http_status"] = response.status
        report["response"] = json.loads(
            response.read().decode("utf-8")
        )

    report["result"] = "metadata_endpoint_reachable"

except urllib.error.HTTPError as exc:
    report["result"] = "http_error"
    report["http_status"] = exc.code
    report["details"] = exc.read().decode(
        "utf-8", errors="replace"
    )[:1000]

except Exception as exc:
    report["result"] = "request_failed"
    report["details"] = str(exc)

report_path = REPORT_DIR / "source_check_adsb_aero.json"
report_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8",
)

print(json.dumps(report, indent=2))
print(f"\nReport saved to: {report_path}")

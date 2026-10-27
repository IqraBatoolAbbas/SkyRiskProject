
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "flight_data" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

API_URL = (
    "https://api.github.com/repos/"
    "adsblol/globe_history/releases?per_page=5"
)

report = {
    "source": "ADSB.lol historical archive",
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "check_type": "release_metadata_only",
}

try:
    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SkyRisk-Auditor-Academic-Project",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        releases = json.loads(response.read().decode("utf-8"))

    report["result"] = "success"
    report["releases_found"] = len(releases)
    report["releases"] = []

    for release in releases:
        assets = []

        for asset in release.get("assets", []):
            assets.append({
                "name": asset.get("name"),
                "size_bytes": asset.get("size"),
                "download_url": asset.get("browser_download_url"),
            })

        report["releases"].append({
            "tag": release.get("tag_name"),
            "published_at": release.get("published_at"),
            "assets": assets,
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

report_path = REPORT_DIR / "adsblol_archive_check.json"
report_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8",
)

print(json.dumps(report, indent=2))
print(f"\nReport saved to: {report_path}")

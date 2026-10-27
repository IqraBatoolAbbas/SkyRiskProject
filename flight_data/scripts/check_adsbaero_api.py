
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "flight_data" / "reports" / "adsbaero_api_check.json"

URLS = [
    "https://adsb.aero/api/v1/health",
    "https://adsb.aero/api/openapi.json",
]

results = []

for url in URLS:
    item = {"url": url}

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "SkyRisk-FYP-Research"},
        )

        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read(500_000)
            item["http_status"] = response.status
            item["content_type"] = response.headers.get("Content-Type")

            try:
                data = json.loads(body.decode("utf-8"))
                if url.endswith("openapi.json"):
                    item["api_title"] = data.get("info", {}).get("title")
                    item["api_version"] = data.get("info", {}).get("version")
                    item["endpoints"] = list(data.get("paths", {}).keys())
                else:
                    item["response"] = data
            except (ValueError, UnicodeDecodeError):
                item["response_preview"] = body[:300].decode(
                    "utf-8", errors="replace"
                )

    except Exception as exc:
        item["error"] = str(exc)

    results.append(item)
    print(json.dumps(item, indent=2))

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")

print("\nReport saved to:", REPORT)
print("No flight archive downloaded.")
print("No database changes were made.")

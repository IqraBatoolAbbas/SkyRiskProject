
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "flight_data" / "reports" / "trace_sample_access.json"

URLS = [
    "https://samples.adsbexchange.com/traces/",
    "https://samples.adsbexchange.com/readsb-hist/2026/10/01/",
]

results = []

for url in URLS:
    item = {"url": url}

    try:
        request = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "SkyRisk-FYP-Research"},
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            item["status"] = response.status
            item["content_type"] = response.headers.get("Content-Type")
            item["content_length"] = response.headers.get("Content-Length")
            item["accept_ranges"] = response.headers.get("Accept-Ranges")

    except Exception as exc:
        item["error"] = str(exc)

    results.append(item)
    print(json.dumps(item, indent=2))

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")

print("\nReport saved to:", REPORT)
print("No data files downloaded.")
print("No database changes were made.")


from pathlib import Path
import json
from datetime import datetime, timezone

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

sources = [
    {
        "name": "Pakistan-specific public labelled NOTAM dataset",
        "url": "https://huggingface.co/datasets",
        "status": "NOT_VERIFIED",
        "notes": (
            "No suitable Pakistan-specific, openly downloadable, "
            "labelled training dataset has been confirmed yet."
        ),
    },
    {
        "name": "ICAO API data samples",
        "url": "https://www.icao.int/api-data-samples",
        "status": "ACCESS_AND_COVERAGE_NEED_CONFIRMATION",
        "notes": (
            "ICAO documents realtime and stored NOTAM services. "
            "Confirm API access, Pakistan coverage, historical data "
            "availability, and permitted use before relying on it."
        ),
    },
    {
        "name": "DEEL-AI NOTAM dataset",
        "url": "https://huggingface.co/datasets/DEEL-AI/NOTAM",
        "status": "PUBLIC_DATASET_FOUND",
        "notes": (
            "English text-classification dataset with 13 classes. "
            "The dataset card describes it as a toy NLP classification "
            "case based on real published data; it is not verified "
            "as Pakistan-specific."
        ),
    },
]

report = {
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "NOTAM source verification for academic research",
    "operational_use": False,
    "sources": sources,
}

output_file = REPORT_DIR / "notam_source_verification.json"
output_file.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8",
)

for source in sources:
    print(f"\n{source['name']}")
    print(f"Status: {source['status']}")
    print(f"URL: {source['url']}")
    print(source["notes"])

print(f"\nReport saved to: {output_file}")

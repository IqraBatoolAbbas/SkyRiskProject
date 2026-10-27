
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
API_URL = "https://notac.aero/api/v1/notam/"


def load_env_value(name):
    """Read a value from backend/.env without printing secrets."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")

    return os.getenv(name)


def fetch_page(api_key, page):
    params = urllib.parse.urlencode({
        "country_code": "PK",
        "status": "any",
        "page": page,
    })

    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={
            "Accept": "application/json",
            "User-Agent": "SkyRiskAuditor/0.1 academic-prototype",
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def validate_record(item):
    """Check essential fields without claiming operational validity."""
    start = item.get("effective_start")
    end = item.get("effective_end")

    issues = []

    if not item.get("id"):
        issues.append("missing_id")
    if not item.get("number"):
        issues.append("missing_notam_number")
    if not item.get("location_code"):
        issues.append("missing_location_code")
    if not item.get("text"):
        issues.append("missing_text")
    if not start:
        issues.append("missing_effective_start")
    if not end:
        issues.append("missing_effective_end")

    try:
        if start and end:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))

            if start_dt >= end_dt:
                issues.append("invalid_effective_period")
    except (ValueError, TypeError):
        issues.append("unparseable_effective_dates")

    text = (item.get("text") or "").strip().upper()
    is_checklist = "CHECKLIST" in text

    return {
        "source_id": item.get("id"),
        "number": item.get("number"),
        "location_code": item.get("location_code"),
        "category": item.get("category"),
        "notam_type": item.get("notam_type"),
        "effective_start": start,
        "effective_end": end,
        "status": item.get("status"),
        "text": item.get("text"),
        "is_checklist_candidate": is_checklist,
        "validation_issues": issues,
    }


def main():
    print("SkyRisk Auditor - NOTAM fetch and validation")
    print("-" * 48)

    api_key = load_env_value("NOTAC_API_KEY")
    if not api_key:
        raise SystemExit("NOTAC_API_KEY missing from backend/.env")

    all_records = []
    seen_ids = set()
    reported_total = None
    page = 1

    try:
        while True:
            data = fetch_page(api_key, page)
            results = data.get("results", [])

            if reported_total is None:
                reported_total = data.get("count")

            if not results:
                break

            for item in results:
                record_id = item.get("id")
                if record_id and record_id in seen_ids:
                    continue
                if record_id:
                    seen_ids.add(record_id)
                all_records.append(item)

            print(f"Page {page}: received {len(results)} records")

            if len(all_records) >= (reported_total or 0):
                break

            page += 1

    except urllib.error.HTTPError as error:
        print("API request failed with HTTP status:", error.code)
        print("Response body was not printed to protect request details.")
        return
    except Exception as error:
        print("Fetch failed:", type(error).__name__, str(error))
        return

    validated = [validate_record(item) for item in all_records]

    checklist_count = sum(
        record["is_checklist_candidate"] for record in validated
    )
    issue_count = sum(
        bool(record["validation_issues"]) for record in validated
    )

    output_path = BASE_DIR / "notam_validation_report.json"
    output_path.write_text(
        json.dumps(validated, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n--- SUMMARY ---")
    print("API reported total:", reported_total)
    print("Unique records fetched:", len(validated))
    print("Checklist candidates:", checklist_count)
    print("Records with validation issues:", issue_count)
    print("Report saved to:", output_path.name)
    print("No database records were changed.")
    print(
        "Reminder: source status and field checks do not prove "
        "official completeness or flight-specific applicability."
    )


if __name__ == "__main__":
    main()

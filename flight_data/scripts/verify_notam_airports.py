
import csv
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "flight_data" / "processed"
REPORTS = ROOT / "flight_data" / "reports"

NOTAM_CSV = PROCESSED / "notam_decisions_oct20_22.csv"
AIRPORT_URL = (
    "https://davidmegginson.github.io/"
    "ourairports-data/airports.csv"
)

REPORTS.mkdir(parents=True, exist_ok=True)

if not NOTAM_CSV.exists():
    raise FileNotFoundError(f"Missing input file: {NOTAM_CSV}")

# Existing NOTAM-decision output se actual location codes lo.
location_codes = set()
input_columns = set()

with NOTAM_CSV.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    input_columns = set(reader.fieldnames or [])

    location_column = next(
        (
            c for c in reader.fieldnames or []
            if c.lower() in {
                "location_code", "notam_location",
                "airport_code", "location"
            }
        ),
        None
    )

    if not location_column:
        raise ValueError(
            "NOTAM location column nahi mili. "
            f"Available columns: {sorted(input_columns)}"
        )

    for row in reader:
        code = (row.get(location_column) or "").strip().upper()
        if code:
            location_codes.add(code)

print("NOTAM location codes:", len(location_codes))
print("Downloading public airport reference data...")

request = urllib.request.Request(
    AIRPORT_URL,
    headers={"User-Agent": "SkyRiskAuditor-FYP/1.0"}
)

with urllib.request.urlopen(request, timeout=60) as response:
    airport_text = response.read().decode("utf-8-sig")

airports = {}

reader = csv.DictReader(airport_text.splitlines())

for row in reader:
    ident = (row.get("ident") or "").strip().upper()
    country = (row.get("iso_country") or "").strip().upper()

    if ident not in location_codes:
        continue

    try:
        lat = float(row["latitude_deg"])
        lon = float(row["longitude_deg"])
    except (TypeError, ValueError, KeyError):
        continue

    airports.setdefault(ident, []).append({
        "ident": ident,
        "name": row.get("name"),
        "country": country,
        "type": row.get("type"),
        "latitude": lat,
        "longitude": lon,
        "scheduled_service": row.get("scheduled_service"),
        "source": "OurAirports airports.csv"
    })

matched = []
ambiguous = []
unmatched = []

for code in sorted(location_codes):
    entries = airports.get(code, [])

    if not entries:
        unmatched.append(code)
    elif len(entries) > 1:
        ambiguous.append({
            "location_code": code,
            "records": entries
        })
    else:
        matched.append(entries[0])

output_csv = PROCESSED / "notam_airport_coordinate_candidates.csv"

with output_csv.open("w", encoding="utf-8", newline="") as f:
    fields = [
        "ident", "name", "country", "type",
        "latitude", "longitude", "scheduled_service", "source"
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(matched)

report = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "input_file": str(NOTAM_CSV),
    "input_columns": sorted(input_columns),
    "unique_notam_location_codes": len(location_codes),
    "unique_codes_with_one_coordinate_record": len(matched),
    "codes_with_multiple_records": ambiguous,
    "unmatched_location_codes": unmatched,
    "coordinate_source": AIRPORT_URL,
    "source_limitations": [
        "OurAirports is a public, volunteer-maintained dataset.",
        "Coordinates are reference points, not runway coordinates.",
        "Coordinate matches do not establish flight operational impact.",
        "This is not an official Pakistan FIR boundary.",
        "No flight decisions or database records were changed."
    ]
}

report_path = REPORTS / "notam_airport_coordinate_report.json"
report_path.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("\nAIRPORT COORDINATE VERIFICATION COMPLETE")
print("Unique NOTAM location codes:", len(location_codes))
print("Codes with one coordinate record:", len(matched))
print("Codes with multiple records:", len(ambiguous))
print("Unmatched codes:", unmatched)
print("CSV:", output_csv)
print("Report:", report_path)
print("No database writes performed.")

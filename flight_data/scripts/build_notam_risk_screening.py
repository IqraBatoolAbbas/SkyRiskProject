
import csv
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "flight_data"

CANDIDATES = DATA / "processed" / "notam_spatial_candidates_oct20_22.csv"
DECISIONS = DATA / "processed" / "notam_decisions_oct20_22.csv"
INSPECTION = DATA / "reports" / "notam_matching_inspection.json"

OUT_CSV = DATA / "processed" / "notam_flight_risk_screening.csv"
OUT_JSON = DATA / "reports" / "notam_flight_risk_screening_report.json"

PATTERNS = {
    "RUNWAY_RESTRICTION": (
        r"\b(RWY|RUNWAY|RUNWAYS)\b.{0,100}"
        r"\b(CLOSED|CLSD|UNAVAILABLE|U/S|WORK|WIP|"
        r"CLOSURE|RESTRICTED)\b|"
        r"\b(CLOSED|CLSD|UNAVAILABLE)\b.{0,100}"
        r"\b(RWY|RUNWAY)\b"
    ),
    "NAVIGATION_AID": (
        r"\b(DVOR|VOR|NDB|ILS|LOCALIZER|LOC|"
        r"GLIDE PATH|GP|DME)\b.{0,100}"
        r"\b(U/S|UNSERVICEABLE|UNAVAILABLE|"
        r"OUT OF SERVICE|NOT AVBL)\b|"
        r"\b(U/S|UNSERVICEABLE|UNAVAILABLE)\b.{0,60}"
        r"\b(DVOR|VOR|NDB|ILS|LOCALIZER|LOC|DME)\b"
    ),
    "OPERATING_HOURS": (
        r"\b(OPS HR|OPERATING HOURS|AD OPS HR|"
        r"NON-SKED|NON SCHEDULED|PRIOR CDN)\b"
    ),
    "AIRSPACE_RESTRICTION": (
        r"\b(AIRSPACE|PROHIBITED|RESTRICTED AREA|"
        r"NOT PERMITTED|AIRSPACE RESTRICTION)\b"
    ),
    "LIGHTING_RESTRICTION": (
        r"\b(LIGHTING|SALS|PAPI|APPROACH LIGHTS)\b.{0,100}"
        r"\b(U/S|UNAVAILABLE|UNSERVICEABLE|WORK|OUT OF SERVICE)\b"
    ),
    "WEATHER_SURFACE": (
        r"\b(SLIPPERY WHEN WET|WATERLOGGED|BRAKING ACTION)\b"
    ),
}


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def first(row, *names, default=""):
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def norm(value):
    return re.sub(r"\s+", "", str(value or "").upper())


def read_notam_records(path):
    """Read NOTAM records from a JSON list or nested JSON object."""
    if not path.exists():
        raise FileNotFoundError(f"NOTAM inspection report not found: {path}")

    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    records = []

    def walk(item):
        if isinstance(item, dict):
            number = first(item, "notam_number")
            location = first(item, "location_code", "notam_location")
            text = first(item, "notam_text", "text", "description")

            if number and location:
                records.append({
                    "notam_number": number,
                    "notam_location": location,
                    "notam_text": text,
                    "category": item.get("category", ""),
                    "status": first(item, "status"),
                    "effective_start": first(item, "effective_start"),
                    "effective_end": first(item, "effective_end"),
                    "source": first(item, "source"),
                })

            for value in item.values():
                if isinstance(value, (dict, list)):
                    walk(value)

        elif isinstance(item, list):
            for value in item:
                walk(value)

    walk(data)

    # Deduplicate repeated records while preserving their content.
    unique = {}
    for record in records:
        key = (
            norm(record["notam_number"]),
            norm(record["notam_location"]),
        )
        unique[key] = record

    return unique


def detect_indicators(text, category=""):
    searchable = str(text or "").upper()
    found = [
        name for name, pattern in PATTERNS.items()
        if re.search(pattern, searchable, flags=re.IGNORECASE)
    ]

    category_text = str(category or "").upper()

    # Category is supplementary metadata, not proof of impact.
    if "NAVAID" in category_text and "NAVIGATION_AID" not in found:
        found.append("NAVIGATION_AID_CATEGORY")

    return found


def main():
    candidates = read_csv(CANDIDATES)
    decisions = read_csv(DECISIONS)
    notams = read_notam_records(INSPECTION)

    source_rows = candidates if candidates else decisions
    if not source_rows:
        raise SystemExit(
            "No candidate or decision rows found. Check input CSV paths."
        )

    results = []
    counts = Counter()
    indicator_counts = Counter()
    unmatched_keys = set()
    flights = set()
    notam_numbers = set()

    for row in source_rows:
        flight = first(row, "flight_id")
        callsign = first(row, "callsign")
        number = first(row, "notam_number")
        location = first(row, "notam_location", "location_code")

        key = (norm(number), norm(location))
        record = notams.get(key)

        # If exact location-key match fails, don't silently guess.
        text = record["notam_text"] if record else first(
            row, "notam_text", "text", "description"
        )
        category = record["category"] if record else first(row, "category")
        decision = first(row, "decision", default="UNASSESSED")
        reason = first(row, "decision_reason")
        timestamp = first(
            row, "point_timestamp_utc", "timestamp_utc", "timestamp"
        )

        try:
            distance = float(first(row, "distance_to_airport_km"))
        except (ValueError, TypeError):
            distance = None

        indicators = detect_indicators(text, category)

        if not record and number and location:
            unmatched_keys.add(f"{number}@{location}")

        if decision == "VALIDATED_MATCH":
            screening = "REVIEW_VALIDATION_EVIDENCE"
        elif decision == "CANDIDATE_MATCH":
            screening = "POTENTIAL_RISK_REVIEW"
        elif decision == "UNCONFIRMED_APPLICABILITY":
            screening = "POTENTIAL_RISK_UNCONFIRMED"
        elif decision == "INSUFFICIENT_DATA":
            screening = "INSUFFICIENT_EVIDENCE"
        elif decision.startswith("REJECTED"):
            screening = "REJECTED_BY_EXISTING_RULE"
        else:
            screening = "NEEDS_REVIEW"

        results.append({
            "flight_id": flight,
            "callsign": callsign,
            "point_timestamp_utc": timestamp,
            "notam_number": number,
            "notam_location": location,
            "distance_to_airport_km": (
                round(distance, 3) if distance is not None else ""
            ),
            "existing_decision": decision,
            "screening_result": screening,
            "notam_text": text,
            "notam_category": category,
            "notam_status": record["status"] if record else "",
            "notam_effective_start": (
                record["effective_start"] if record else ""
            ),
            "notam_effective_end": (
                record["effective_end"] if record else ""
            ),
            "notam_source": record["source"] if record else "",
            "text_indicators": ";".join(indicators),
            "decision_reason": reason,
            "evidence_note": (
                "Text/category indicators are screening clues only. "
                "Proximity and time overlap do not establish operational impact."
            ),
        })

        counts[screening] += 1
        indicator_counts.update(indicators)

        if flight:
            flights.add(flight)
        if number:
            notam_numbers.add(number)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    report = {
        "input_used": str(CANDIDATES if candidates else DECISIONS),
        "notam_text_source": str(INSPECTION),
        "fallback_used": not bool(candidates),
        "rows_screened": len(results),
        "unique_flights": len(flights),
        "unique_notam_numbers": len(notam_numbers),
        "notam_records_loaded": len(notams),
        "rows_with_notam_text": sum(
            bool(row["notam_text"].strip()) for row in results
        ),
        "rows_without_notam_text": sum(
            not row["notam_text"].strip() for row in results
        ),
        "unmatched_notam_location_keys": sorted(unmatched_keys),
        "screening_counts": dict(counts),
        "text_indicator_counts": dict(indicator_counts),
        "validated_impacts_created": 0,
        "limitations": [
            "Text indicators use heuristic rules and may miss or misclassify NOTAMs.",
            "Category indicators are not proof of operational impact.",
            "Airport reference distance does not prove arrival or departure.",
            "Existing decisions are preserved and not upgraded to validated.",
            "Candidate input means the output covers candidate rows only.",
            "Inspection data is from the existing NOTAC-derived project report.",
        ],
        "output_csv": str(OUT_CSV),
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nCSV saved: {OUT_CSV}")
    print(f"Report saved: {OUT_JSON}")


if __name__ == "__main__":
    main()

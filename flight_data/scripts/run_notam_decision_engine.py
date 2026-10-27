
import csv
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]

POINTS_FILE = (
    ROOT / "flight_data" / "processed"
    / "pakistan_region_candidate_points_oct20_22.csv"
)
NOTAMS_FILE = (
    ROOT / "flight_data" / "reports"
    / "notam_matching_inspection.json"
)
OUTPUT_CSV = (
    ROOT / "flight_data" / "processed"
    / "notam_decisions_oct20_22.csv"
)
OUTPUT_REPORT = (
    ROOT / "flight_data" / "reports"
    / "notam_decision_engine_report.json"
)


def parse_datetime(value):
    if not value:
        return None
    try:
        result = datetime.fromisoformat(
            str(value).strip().replace("Z", "+00:00")
        )
        if result.tzinfo is None:
            return None
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def first_value(record, *keys):
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return value
    return ""


def get_notam_records(data):
    """Read common JSON list structures without inventing missing fields."""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if isinstance(data, dict):
        for key in ("notams", "records", "items", "results", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
            if isinstance(value, dict):
                found = get_notam_records(value)
                if found:
                    return found

    return []


def classify_notam(number, text, category, checklist):
    text = str(text).upper()
    category = str(category).upper()
    number = str(number).upper()

    if checklist or number in {"A0560/26", "C0060/26"}:
        return "CHECKLIST_OR_TRIGGER"

    if re.search(r"\bAIRSPACE\b|\bMSSR\b|\bSURVEILLANCE\b", text):
        return "AIRSPACE_OR_SURVEILLANCE"

    if re.search(r"\bTWY\b|\bTAXIWAY\b|\bBAY\b|\bPUSH BACK\b", text):
        return "TAXIWAY_OR_STAND"

    if re.search(
        r"\bLIGHT\b|\bPAPI\b|\bSALS\b|\bILS\b|"
        r"\bLOCALIZER\b|\bAPPROACH\b", text
    ):
        return "LIGHTING_OR_APPROACH_AID"

    if re.search(
        r"\bOPS HR\b|\bOPERATING HOURS\b|\bVFR FLT ONLY\b", text
    ):
        return "AERODROME_OPERATING_RULE"

    if re.search(
        r"\bRWY\b|\bRUNWAY\b|\bCLSD\b|\bCLOSED\b|"
        r"\bNOT AVBL\b|\bSLIPPERY\b", text
    ) or "RUNWAY" in category:
        return "RUNWAY_CONDITION_OR_CLOSURE"

    return "OTHER_OR_UNCLASSIFIED"


def main():
    for file_path in (POINTS_FILE, NOTAMS_FILE):
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required input file not found: {file_path}"
            )

    with POINTS_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        points = list(csv.DictReader(file))

    data = json.loads(NOTAMS_FILE.read_text(encoding="utf-8"))
    notam_records = get_notam_records(data)

    if not notam_records:
        raise ValueError(
            "NOTAM JSON structure not recognized. "
            "Check notam_matching_inspection.json before proceeding."
        )

    notams = []
    seen = set()

    for record in notam_records:
        number = str(first_value(
            record, "notam_number", "number", "notam_id", "source_id"
        )).strip()

        location = str(first_value(
            record, "location_code", "airport_code", "location"
        )).strip().upper()

        text = str(first_value(
            record, "notam_text", "text", "message", "description"
        )).strip()

        category = record.get("category", "")
        if isinstance(category, dict):
            category = category.get("label", category.get("code", ""))

        start = parse_datetime(first_value(
            record, "effective_start", "effective_from", "start"
        ))
        end = parse_datetime(first_value(
            record, "effective_end", "effective_to", "end"
        ))

        checklist = str(record.get(
            "is_checklist_candidate",
            record.get("checklist_candidate", False)
        )).strip().lower() in {"true", "1", "yes"}

        kind = classify_notam(number, text, category, checklist)

        key = (number, location, start, end, text)
        if key in seen:
            continue
        seen.add(key)

        notams.append({
            "number": number,
            "location": location,
            "text": text,
            "category": str(category),
            "start": start,
            "end": end,
            "kind": kind,
        })

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    point_time_missing = 0
    output_count = 0

    fields = [
        "flight_id", "icao24", "callsign", "icao_type",
        "point_timestamp_utc", "longitude", "latitude",
        "altitude_ft", "segment_index", "point_index",
        "notam_number", "notam_location",
        "notam_effective_start_utc", "notam_effective_end_utc",
        "notam_kind", "notam_text", "decision", "decision_reason",
        "spatial_applicability", "operational_impact",
    ]

    with OUTPUT_CSV.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for point in points:
            timestamp_text = point.get("timestamp_utc", "")
            timestamp = parse_datetime(timestamp_text)

            if not timestamp:
                point_time_missing += 1

            try:
                latitude = float(point["latitude"])
                longitude = float(point["longitude"])
                coordinates_valid = (
                    -90 <= latitude <= 90
                    and -180 <= longitude <= 180
                )
            except (ValueError, TypeError, KeyError):
                coordinates_valid = False

            for notam in notams:
                start = notam["start"]
                end = notam["end"]

                if not timestamp or not start or not end:
                    decision = "INSUFFICIENT_DATA"
                    reason = (
                        "Point timestamp or NOTAM validity time "
                        "is missing or invalid."
                    )

                elif timestamp < start or timestamp > end:
                    decision = "REJECTED_TIME"
                    reason = (
                        "Point timestamp is outside the NOTAM "
                        "effective interval."
                    )

                elif notam["kind"] == "CHECKLIST_OR_TRIGGER":
                    decision = "INSUFFICIENT_DATA"
                    reason = (
                        "Checklist/trigger material is not treated "
                        "as a confirmed operational restriction."
                    )

                elif not coordinates_valid:
                    decision = "INSUFFICIENT_DATA"
                    reason = "Valid point coordinates are unavailable."

                else:
                    decision = "UNCONFIRMED_APPLICABILITY"
                    reason = (
                        "Time overlaps, but airport/airspace "
                        "applicability and operational impact have "
                        "not been established."
                    )

                writer.writerow({
                    "flight_id": point.get("flight_id", ""),
                    "icao24": point.get("icao24", ""),
                    "callsign": point.get("callsign", ""),
                    "icao_type": point.get("icao_type", ""),
                    "point_timestamp_utc": timestamp_text,
                    "longitude": point.get("longitude", ""),
                    "latitude": point.get("latitude", ""),
                    "altitude_ft": point.get("altitude_ft", ""),
                    "segment_index": point.get("segment_index", ""),
                    "point_index": point.get("point_index", ""),
                    "notam_number": notam["number"],
                    "notam_location": notam["location"],
                    "notam_effective_start_utc": (
                        start.isoformat() if start else ""
                    ),
                    "notam_effective_end_utc": (
                        end.isoformat() if end else ""
                    ),
                    "notam_kind": notam["kind"],
                    "notam_text": notam["text"],
                    "decision": decision,
                    "decision_reason": reason,
                    "spatial_applicability": "NOT_ASSESSED",
                    "operational_impact": "NOT_ESTABLISHED",
                })

                counts[decision] += 1
                output_count += 1

    report = {
        "engine": "evidence_aware_notam_decision_engine_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "trajectory_points": len(points),
        "unique_flights": len({
            p.get("flight_id", "") for p in points
            if p.get("flight_id", "")
        }),
        "notam_records_after_deduplication": len(notams),
        "decision_rows": output_count,
        "decision_counts": dict(counts),
        "points_with_missing_timestamp": point_time_missing,
        "limitations": [
            "REJECTED_TIME means only that the point is outside "
            "the NOTAM effective interval.",
            "No verified airport coordinates or official FIR geometry "
            "are used by this version.",
            "Airport-specific NOTAM applicability is not established "
            "by time overlap alone.",
            "No VALIDATED_MATCH is produced without operational evidence.",
            "The approximate Pakistan bounding box is not an official FIR.",
            "Input files and PostgreSQL database are not modified.",
        ],
    }

    OUTPUT_REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\nNOTAM DECISION ENGINE COMPLETE")
    print(f"Trajectory points: {len(points):,}")
    print(f"Unique flights: {report['unique_flights']:,}")
    print(f"NOTAM records: {len(notams):,}")
    print(f"Decision rows: {output_count:,}")
    print("\nDecision counts:")
    for name in (
        "REJECTED_TIME",
        "REJECTED_SPATIAL",
        "UNCONFIRMED_APPLICABILITY",
        "INSUFFICIENT_DATA",
        "CANDIDATE_MATCH",
        "VALIDATED_MATCH",
    ):
        print(f"  {name}: {counts.get(name, 0):,}")

    print(f"\nCSV: {OUTPUT_CSV}")
    print(f"Report: {OUTPUT_REPORT}")
    print("No database writes performed.")


if __name__ == "__main__":
    main()

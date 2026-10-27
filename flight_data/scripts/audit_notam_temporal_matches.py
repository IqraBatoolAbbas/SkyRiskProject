
import csv
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "flight_data" / "processed"
    / "notam_temporal_candidate_matches_oct20_22.csv"
)
OUTPUT_CSV = (
    ROOT / "flight_data" / "reports"
    / "notam_temporal_match_summary.csv"
)
OUTPUT_JSON = (
    ROOT / "flight_data" / "reports"
    / "notam_temporal_match_audit.json"
)


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT}")

    stats = defaultdict(lambda: {
        "points": set(),
        "flights": set(),
        "locations": set(),
        "statuses": set(),
        "start": set(),
        "end": set(),
        "texts": set(),
    })

    total_rows = 0
    unique_point_notam_pairs = set()

    with INPUT.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            total_rows += 1
            notam = (
                row.get("notam_number", "").strip()
                or row.get("source_id", "").strip()
                or "UNKNOWN_NOTAM"
            )
            flight = row.get("flight_id", "").strip()
            timestamp = row.get("timestamp_utc", "").strip()
            segment = row.get("segment_index", "").strip()
            point = row.get("point_index", "").strip()

            point_key = (flight, timestamp, segment, point)
            pair_key = (notam, point_key)
            unique_point_notam_pairs.add(pair_key)

            item = stats[notam]
            item["points"].add(point_key)
            if flight:
                item["flights"].add(flight)

            location = row.get("location_code", "").strip()
            if location:
                item["locations"].add(location)

            status = row.get("notam_status", "").strip()
            if status:
                item["statuses"].add(status)

            start = row.get("effective_start_utc", "").strip()
            end = row.get("effective_end_utc", "").strip()
            if start:
                item["start"].add(start)
            if end:
                item["end"].add(end)

            text = row.get("notam_text", "").strip()
            if text:
                item["texts"].add(text)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary_rows = []

    for notam, item in sorted(stats.items()):
        summary_rows.append({
            "notam_number": notam,
            "location_codes": "; ".join(sorted(item["locations"])),
            "statuses": "; ".join(sorted(item["statuses"])),
            "unique_temporal_candidate_points": len(item["points"]),
            "unique_flights": len(item["flights"]),
            "effective_start_utc": "; ".join(sorted(item["start"])),
            "effective_end_utc": "; ".join(sorted(item["end"])),
            "notam_text": " | ".join(sorted(item["texts"])),
            "spatial_applicability": "UNKNOWN",
            "operational_impact": "UNKNOWN",
        })

    fields = [
        "notam_number",
        "location_codes",
        "statuses",
        "unique_temporal_candidate_points",
        "unique_flights",
        "effective_start_utc",
        "effective_end_utc",
        "notam_text",
        "spatial_applicability",
        "operational_impact",
    ]

    with OUTPUT_CSV.open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    report = {
        "input_csv": str(INPUT),
        "summary_csv": str(OUTPUT_CSV),
        "temporal_match_rows_read": total_rows,
        "unique_notam_ids_in_matches": len(stats),
        "unique_point_notam_pairs": len(unique_point_notam_pairs),
        "method": "Deduplicate and summarize existing temporal matches.",
        "spatial_applicability": "UNKNOWN",
        "operational_impact": "UNKNOWN",
        "warning": (
            "These counts measure timestamp overlap only. They do not "
            "prove that a flight used the affected airport, runway, "
            "facility, or airspace. NOTAM status and applicability "
            "require separate interpretation."
        ),
    }

    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print("\nNOTAM TEMPORAL MATCH AUDIT COMPLETE")
    print("Input match rows:", total_rows)
    print("Unique NOTAMs:", len(stats))
    print("Unique point-NOTAM pairs:", len(unique_point_notam_pairs))
    print("Summary CSV:", OUTPUT_CSV)
    print("Audit JSON:", OUTPUT_JSON)
    print("\nTOP NOTAM MATCH COUNTS")
    for row in sorted(
        summary_rows,
        key=lambda x: x["unique_temporal_candidate_points"],
        reverse=True
    )[:10]:
        print(
            row["notam_number"],
            "| location:", row["location_codes"],
            "| points:", row["unique_temporal_candidate_points"],
            "| flights:", row["unique_flights"],
        )


if __name__ == "__main__":
    main()

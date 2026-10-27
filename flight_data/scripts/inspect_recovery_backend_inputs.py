
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "recovery_candidates":
        ROOT / "flight_data" / "processed"
        / "recovery_route_candidates_oct20_22.csv",

    "hazard_reevaluation":
        ROOT / "flight_data" / "processed"
        / "recovery_hazard_reevaluation_oct20_22.csv",

    "flight_assessment":
        ROOT / "flight_data" / "processed"
        / "recovery_flight_assessment_oct20_22.csv",

    "evaluation_summary":
        ROOT / "flight_data" / "processed"
        / "recovery_evaluation_summary_oct20_22.csv",
}


def inspect_csv(name, path):
    print(f"\n{'=' * 70}")
    print(f"DATASET: {name}")
    print(f"FILE: {path.relative_to(ROOT)}")

    if not path.is_file():
        print("STATUS: FILE NOT FOUND")
        return

    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)
        print(f"COLUMNS ({len(reader.fieldnames or [])}):")
        for column in reader.fieldnames or []:
            print(f"  - {column}")

        print("\nFIRST DATA ROW:")
        first = next(reader, None)

        if first is None:
            print("  No data rows")
        else:
            for key, value in first.items():
                print(f"  {key}: {value}")


def main():
    print("SKYRISK RECOVERY INPUT INSPECTION")

    for name, path in FILES.items():
        inspect_csv(name, path)

    print("\nInspection complete. No files were modified.")


if __name__ == "__main__":
    main()

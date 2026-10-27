
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.recovery_service import (
    get_recovery_summary,
    get_flight_recovery,
)


def main():
    summary = get_recovery_summary()

    print("RECOVERY SUMMARY TEST")
    print("Status:", summary["status"])
    print("Flight assessments:", summary["flight_assessment_count"])
    print(
        "Candidate types:",
        len(summary["recovery_candidate_evaluation"]),
    )

    flight_id = "04022b:2026-10-22T21:24:08Z"
    flight = get_flight_recovery(flight_id)

    print("\nRECOVERY FLIGHT TEST")
    print("Flight ID:", flight_id)
    print("Found:", flight is not None)

    if flight:
        print("Candidate count:", flight["candidate_count"])
        print(
            "Proxy reevaluations:",
            len(flight["hazard_proxy_reevaluations"]),
        )
        print("Safety:", flight["safety_validation_status"])
        print("Clearance:", flight["operational_clearance"])

    assert summary["status"] == "success"
    assert len(summary["recovery_candidate_evaluation"]) == 4
    assert flight is not None
    assert flight["candidate_count"] > 0
    assert flight["safety_validation_status"] == "NOT_VALIDATED"
    assert flight["operational_clearance"] == "NOT_CHECKED"

    print("\nAll recovery service tests passed.")


if __name__ == "__main__":
    main()

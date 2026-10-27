
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent


def load_env_key(name):
    """Read a key from backend/.env without printing its value."""
    env_file = BASE_DIR / ".env"

    if not env_file.exists():
        return os.getenv(name)

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)

        if key.strip() == name:
            return value.strip().strip('"').strip("'")

    return os.getenv(name)


def request_json(url, headers=None):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "SkyRiskAuditor/0.1 academic-prototype",
            **(headers or {}),
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return error.code, {"error": body[:500]}

    except Exception as error:
        return None, {"error": str(error)}


def main():
    print("SkyRisk Auditor — Pakistan NOTAM source check")
    print("-" * 48)

    # First, check what the current NOTAC source returns for Pakistan.
    # This is a coverage test, not an official Pakistan NOTAM feed.
    notac_key = load_env_key("NOTAC_API_KEY")

    if notac_key:
        url = "https://notac.aero/api/v1/notam/?country_code=PK&status=any&page=2"
        status, data = request_json(
            url,
            headers={"Authorization": f"Bearer {notac_key}"},
        )

        print(f"\nNOTAC HTTP status: {status}")

        if status == 200:
            results = data.get("results", [])
            print("\n--- NOTAM DATA SAMPLE ---")
            for item in results[:3]:
                print({
                    "id": item.get("id"),
                    "number": item.get("number"),
                    "location_code": item.get("location_code"),
                    "category": item.get("category"),
                    "notam_type": item.get("notam_type"),
                    "effective_start": item.get("effective_start"),
                    "effective_end": item.get("effective_end"),
                    "status": item.get("status"),
                })
            if results:
                print("\nFields available in first record:")
                print(sorted(results[0].keys()))

                print("\nDate-related fields:")
                for key, value in results[0].items():
                    if any(word in key.lower() for word in
                           ["date", "time", "start", "end", "valid", "expire"]):
                        print(f"{key}: {value}")
            print("Pakistan records returned:", len(results))
            print("Total matching records:", data.get("count", 0))

            for item in results[:5]:
                print({
                    "number": item.get("number"),
                    "location": item.get("location_code"),
                    "status": item.get("status"),
                    "text": item.get("text"),
                })

            if not results:
                print(
                    "No Pakistan records returned by this query. "
                    "This does not prove that Pakistan has no NOTAMs."
                )
        else:
            print("NOTAC response:", data.get("error", data))

    else:
        print("\nNOTAC_API_KEY is not configured in backend/.env")

    # Optional: use an official/provider endpoint only after its access
    # credentials and exact endpoint are obtained.
    icao_key = load_env_key("ICAO_API_KEY")

    print("\nICAO access configured:", bool(icao_key))
    if not icao_key:
        print(
            "ICAO credentials are not configured. "
            "No live ICAO request was made."
        )

    print("\nSource check complete.")
    print(
        "Do not use empty or simulated results as proof that a flight "
        "has no operational NOTAMs."
    )


if __name__ == "__main__":
    main()

           
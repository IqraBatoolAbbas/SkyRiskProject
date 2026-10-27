
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
REPORT_FILE = (
    ROOT / "flight_data" / "reports"
    / "adsblol_archive_metadata.json"
)

URL = (
    "https://api.github.com/repos/"
    "adsblol/globe_history/releases?per_page=10"
)


def main():
    print("Checking ADSB.lol historical archive metadata...")

    request = urllib.request.Request(
        URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SkyRisk-FYP-Research",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            releases = json.loads(response.read().decode("utf-8"))

    except Exception as exc:
        print("Request failed:", str(exc))
        print("No database changes were made.")
        return

    results = []

    for release in releases:
        assets = []

        for asset in release.get("assets", []):
            assets.append({
                "name": asset.get("name"),
                "size_bytes": asset.get("size"),
                "size_gb": round(
                    (asset.get("size") or 0) / (1024 ** 3), 3
                ),
                "download_url": asset.get("browser_download_url"),
                "download_count": asset.get("download_count"),
            })

        results.append({
            "release_name": release.get("name"),
            "tag_name": release.get("tag_name"),
            "published_at": release.get("published_at"),
            "release_url": release.get("html_url"),
            "assets": assets,
        })

    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": URL,
        "releases_returned": len(results),
        "releases": results,
        "database_changed": False,
        "archive_downloaded": False,
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("Releases found:", len(results))

    for release in results:
        print("\nRelease:", release["release_name"])
        print("Tag:", release["tag_name"])

        if not release["assets"]:
            print("  No downloadable assets listed.")

        for asset in release["assets"]:
            print("  File:", asset["name"])
            print("  Size (GB):", asset["size_gb"])
            print("  Downloads:", asset["download_count"])

    print("\nReport saved to:", REPORT_FILE)
    print("No archive was downloaded.")
    print("No database changes were made.")


if __name__ == "__main__":
    main()


import json
import urllib.request
from pathlib import Path

# Read the private API key from .env
env_path = Path(__file__).parent / ".env"
api_key = None

for line in env_path.read_text(encoding="utf-8").splitlines():
    if line.startswith("NOTAC_API_KEY="):
        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

if not api_key or api_key == "paste_your_actual_key_here":
    raise SystemExit("API key missing. Check backend/.env")

url = "https://notac.aero/api/v1/notam/?location=KORD"

request = urllib.request.Request(
    url,
    headers={"Authorization": f"Bearer {api_key}"},
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    print("API connection successful!")
    print("Total matching NOTAMs:", data.get("count", 0))

    for item in data.get("results", [])[:3]:
        print("\nNOTAM:", item.get("number"))
        print("Location:", item.get("location_code"))
        print("Text:", item.get("text", "")[:200])


except Exception as error:
    print("API test failed:", error)

    if hasattr(error, "read"):
        print("Server response:", error.read().decode("utf-8"))



import importlib.util
import sys

PACKAGES = ["fastapi", "uvicorn", "torch", "transformers", "pydantic"]

def main():
    print("SKYRISK BACKEND DEPENDENCY CHECK")
    print("Python:", sys.executable)
    print("-" * 45)

    for package in PACKAGES:
        available = importlib.util.find_spec(package) is not None
        print(f"{package}: {'INSTALLED' if available else 'MISSING'}")

if __name__ == "__main__":
    main()

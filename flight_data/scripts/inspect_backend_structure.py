
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

EXCLUDED = {
    ".venv", "venv", "__pycache__", "node_modules",
    ".git", "site-packages"
}

IMPORTANT_NAMES = {
    "main.py", "app.py", "api.py", "routes.py",
    "requirements.txt", "pyproject.toml",
    "config.py", "database.py", "models.py"
}


def main():
    print("SKYRISK BACKEND STRUCTURE")
    print("=" * 60)

    if not BACKEND.exists():
        print(f"Backend folder not found: {BACKEND}")
        return

    for path in sorted(BACKEND.rglob("*")):
        if any(part in EXCLUDED for part in path.parts):
            continue
        if not path.is_file():
            continue

        relative = path.relative_to(ROOT)
        if (
            path.name in IMPORTANT_NAMES
            or path.suffix.lower() in {".py", ".toml"}
            or path.name == "requirements.txt"
        ):
            print(relative)

    print("=" * 60)
    print("Inspection complete. No files were modified.")


if __name__ == "__main__":
    main()

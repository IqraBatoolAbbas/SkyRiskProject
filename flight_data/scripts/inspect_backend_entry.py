
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILES_TO_INSPECT = [
    ROOT / "backend" / "main.py",
    ROOT / "backend" / "requirements.txt",
    ROOT / "requirements.txt",
    ROOT / "backend" / "pyproject.toml",
]


def main():
    print("SKYRISK BACKEND ENTRY-POINT INSPECTION")
    print("=" * 65)

    for path in FILES_TO_INSPECT:
        if not path.is_file():
            continue

        print(f"\nFILE: {path.relative_to(ROOT)}")
        print("-" * 65)

        try:
            lines = path.read_text(
                encoding="utf-8-sig"
            ).splitlines()

            # Show entry-point code without flooding the terminal.
            limit = 240 if path.name == "main.py" else 120

            for number, line in enumerate(lines[:limit], start=1):
                print(f"{number:04}: {line}")

            if len(lines) > limit:
                print(
                    f"... truncated; total lines: {len(lines)}"
                )

        except (OSError, UnicodeError) as error:
            print(f"Could not read file: {error}")

    print("\nInspection complete. No files were modified.")


if __name__ == "__main__":
    main()

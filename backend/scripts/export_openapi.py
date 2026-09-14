import json
import sys
from pathlib import Path

from app.main import create_app
from app.settings import Settings

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    spec = create_app(Settings()).openapi()
    OUTPUT_PATH.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"Wrote {OUTPUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()

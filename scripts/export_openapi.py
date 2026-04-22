from __future__ import annotations

from pathlib import Path

import yaml

from app.main import create_app


def main() -> None:
    app = create_app()
    spec = app.openapi()
    output_path = Path(__file__).resolve().parents[1] / "openapi" / "lis-internal-v1.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    print(f"Exported OpenAPI to {output_path}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "scripts/smoke_test.py",
    "scripts/smoke_test_fhir.py",
    "scripts/smoke_test_integration.py",
    "scripts/smoke_test_autoverification.py",
    "scripts/smoke_test_astm.py",
    "scripts/smoke_test_qc.py",
    "scripts/smoke_test_transport.py",
    "scripts/smoke_test_runtime.py",
]


def main() -> None:
    for script in SCRIPTS:
        print(f"=== Running {script} ===")
        subprocess.run(
            [sys.executable, str(ROOT / script)],
            check=True,
            cwd=ROOT,
        )
    print("Smoke test matrix OK")


if __name__ == "__main__":
    main()

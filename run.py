#!/usr/bin/env python3
"""Entry point for SmartPark AI CLI.

Run with:
    python run.py
"""

import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    cli_file = project_root / "smartpark-cli.py"

    if not cli_file.exists():
        raise SystemExit("smartpark-cli.py was not found in the project root.")

    subprocess.call([sys.executable, str(cli_file)])

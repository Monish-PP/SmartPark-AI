#!/usr/bin/env python3
"""SmartPark AI CLI Launcher.

Provides quick access to backend, frontend, edge AI service, and training commands.
"""

import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
EDGE_DIR = PROJECT_ROOT / "occupancy-service"


def get_python_executable():
    """Return the project venv Python when available, otherwise fall back to the current interpreter."""
    candidates = [
        PROJECT_ROOT / ".venv",
        PROJECT_ROOT.parent / ".venv",
        Path(r"D:\MONISH\New folder\.venv"),
    ]

    for base in candidates:
        if os.name == "nt":
            venv_python = base / "Scripts" / "python.exe"
        else:
            venv_python = base / "bin" / "python"

        if venv_python.exists():
            return str(venv_python)

    return sys.executable


PYTHON_EXECUTABLE = get_python_executable()
NPM_EXECUTABLE = shutil.which("npm") or shutil.which("npm.cmd") or "npm"


def find_available_port(start_port: int, max_tries: int = 10) -> int:
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port


def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False

BANNER = r"""
███████╗███╗   ███╗ █████╗ ██████╗ ████████╗██████╗  █████╗ ██████╗ ██╗  ██╗
██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝
███████╗██╔████╔██║███████║██████╔╝   ██║   ██████╔╝███████║██████╔╝█████╔╝
╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   ██╔═══╝ ██╔══██║██╔══██╗██╔═██╗
███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   ██║     ██║  ██║██║  ██║██║  ██╗
╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
                SmartPark AI - Your AI-Powered Smart Parking 
"""


def run_cmd(command, cwd=None, capture_output=False, wait=True):
    print(f"\n▶ Running: {' '.join(command)}")

    if not wait:
        kwargs = {"cwd": str(cwd) if cwd else None, "text": True}
        if os.name == "nt":
            # Create a separate process so the menu remains responsive.
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        else:
            kwargs["start_new_session"] = True
        return subprocess.Popen(command, **kwargs)

    return subprocess.run(command, cwd=str(cwd) if cwd else None, capture_output=capture_output, text=True)


def start_backend():
    backend_port = 8000
    if not is_port_available(backend_port):
        backend_port = find_available_port(backend_port)
        print(f"Port 8000 is busy. Starting Django backend on http://localhost:{backend_port}")
    else:
        print("Starting Django backend on http://localhost:8000")

    run_cmd([PYTHON_EXECUTABLE, "manage.py", "runserver", f"0.0.0.0:{backend_port}"], cwd=BACKEND_DIR, wait=False)


def start_frontend():
    frontend_port = 5173
    if not is_port_available(frontend_port):
        frontend_port = find_available_port(frontend_port)
        print(f"Port 5173 is busy. Starting React frontend on http://localhost:{frontend_port}")
    else:
        print("Starting React frontend on http://localhost:5173")

    run_cmd([NPM_EXECUTABLE, "run", "dev", "--", "--host", "0.0.0.0", "--port", str(frontend_port)], cwd=FRONTEND_DIR, wait=False)


def start_edge_service():
    edge_port = 8001
    if not is_port_available(edge_port):
        edge_port = find_available_port(edge_port)
        print(f"Port 8001 is busy. Starting FastAPI occupancy service on http://localhost:{edge_port}")
    else:
        print("Starting FastAPI occupancy service on http://localhost:8001")

    run_cmd([PYTHON_EXECUTABLE, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(edge_port)], cwd=EDGE_DIR, wait=False)


def train_occupancy_model():
    data_file = BACKEND_DIR / "data" / "pklot.yaml"
    if not data_file.exists():
        print("PKLot dataset config not found at backend/data/pklot.yaml")
        print("Download or convert the PKLot dataset first, then rerun this option.")
        return

    print("Training YOLOv8 occupancy model...")
    run_cmd([
        PYTHON_EXECUTABLE,
        "ai_engine/occupancy/train_yolo.py",
        "--epochs", "1",
        "--batch", "1",
        "--imgsz", "320",
    ], cwd=BACKEND_DIR)


def train_recommender():
    data_file = BACKEND_DIR / "data" / "historical_bookings.csv"
    if not data_file.exists():
        print("Training dataset not found at backend/data/historical_bookings.csv")
        print("Add the CSV file or generate sample data before running this option.")
        return

    print("Training recommendation engine...")
    run_cmd([PYTHON_EXECUTABLE, "-c", "from ai_engine.recommendation.engine import train_recommender; import pandas as pd; df = pd.read_csv('data/historical_bookings.csv'); train_recommender(df, save_dir='ml_models/')"], cwd=BACKEND_DIR)


def train_forecaster():
    data_file = BACKEND_DIR / "data" / "occupancy_logs.csv"
    if not data_file.exists():
        print("Training dataset not found at backend/data/occupancy_logs.csv")
        print("Add the CSV file or generate sample occupancy data before running this option.")
        return

    print("Training forecasting model...")
    run_cmd([
        PYTHON_EXECUTABLE,
        "-c",
        "from ai_engine.forecasting.forecaster import train_lstm, train_prophet, train_xgboost_forecaster; import pandas as pd; df = pd.read_csv('data/occupancy_logs.csv'); train_lstm(df); train_prophet(df); train_xgboost_forecaster(df); print('Forecasting pipeline ready.')",
    ], cwd=BACKEND_DIR)


def run_full_system():
    print("Starting SmartPark AI stack (backend + frontend + edge service).")
    print("Tip: each service is launched in its own process so the CLI stays interactive.")
    start_backend()
    start_frontend()
    start_edge_service()


def view_analytics():
    print("\nSmartPark AI Quick Analytics")
    print("- Backend: backend/manage.py")
    print("- Frontend: frontend/src")
    print("- Edge service: occupancy-service/app")
    print("- ML models: backend/ml_models")
    print("- Current runtime: Python", platform.python_version())


def main():
    print(BANNER)
    print("SmartPark AI\n")
    print("1. Start Backend")
    print("2. Start Frontend")
    print("3. Start Edge AI Service")
    print("4. Train Occupancy Model")
    print("5. Train Recommendation Engine")
    print("6. Train Forecasting Model")
    print("7. Run Full System")
    print("8. View Analytics")
    print("9. Exit")

    while True:
        try:
            choice = input("\nSelect an option [1-9]: ").strip()
        except KeyboardInterrupt:
            print("\nExiting SmartPark CLI.")
            return

        if choice == "1":
            start_backend()
        elif choice == "2":
            start_frontend()
        elif choice == "3":
            start_edge_service()
        elif choice == "4":
            train_occupancy_model()
        elif choice == "5":
            train_recommender()
        elif choice == "6":
            train_forecaster()
        elif choice == "7":
            run_full_system()
        elif choice == "8":
            view_analytics()
        elif choice == "9":
            print("Goodbye.")
            return
        else:
            print("Please choose a valid option.")


if __name__ == "__main__":
    main()

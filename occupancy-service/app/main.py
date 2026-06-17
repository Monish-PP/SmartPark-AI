"""
SmartPark AI — Edge Occupancy Service
=======================================
FastAPI application that:
  1. Opens a local camera (webcam or IP camera RTSP/HTTP).
  2. Runs YOLOv8 vehicle detection on each frame locally.
  3. Maps detections → parking slot occupancy states.
  4. POSTs only the occupancy summary to the Django backend.

Camera feed NEVER leaves this machine.
Only occupancy events are transmitted.

Endpoints:
  GET /health   — liveness probe
  GET /status   — current occupancy snapshot
  GET /config   — service configuration (non-secret fields)
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api_client import BackendClient
from app.config import settings
from app.detector import VehicleDetector
from app.slot_manager import SlotManager
from app.utils import setup_logging, utc_now_iso

# ── Logger ────────────────────────────────────────────────────────────────────
logger = setup_logging(settings.LOG_LEVEL)

# ── Shared state ──────────────────────────────────────────────────────────────
_detector: VehicleDetector | None = None
_slot_manager: SlotManager | None = None
_backend_client: BackendClient | None = None
_detection_task: asyncio.Task | None = None
_service_stats = {
    "started_at": None,
    "frames_processed": 0,
    "updates_sent": 0,
    "last_update_at": None,
    "errors": 0,
}


# ── Detection Loop ────────────────────────────────────────────────────────────

async def _run_detection_loop() -> None:
    """
    Core background task.
    Runs in a separate thread (via asyncio.to_thread) so OpenCV blocking I/O
    doesn't block the FastAPI event loop.
    """
    global _service_stats

    logger.info(
        f"Detection loop starting — interval: {settings.DETECTION_INTERVAL_SEC}s, "
        f"parking: {settings.PARKING_ID}, camera: {settings.CAMERA_SOURCE}"
    )

    min_change = settings.MIN_CHANGE_TO_REPORT
    interval = settings.DETECTION_INTERVAL_SEC
    last_sent_occupied = -1
    loop = asyncio.get_running_loop()

    def _blocking_stream():
        """Runs in a thread pool — contains blocking OpenCV calls."""
        nonlocal last_sent_occupied

        for frame, detections in _detector.stream():
            loop_start = time.monotonic()

            summary = _slot_manager.update(detections)
            _service_stats["frames_processed"] += 1

            # Determine whether to send an update
            occupied_now = summary["occupied_slots"]
            delta = abs(occupied_now - last_sent_occupied)
            should_send = last_sent_occupied == -1 or delta >= max(min_change, 1)

            if should_send:
                # Schedule coroutine on the event loop from this thread
                future = asyncio.run_coroutine_threadsafe(
                    _backend_client.send_occupancy_update(summary),
                    loop,
                )
                try:
                    success = future.result(timeout=15)
                    if success:
                        last_sent_occupied = occupied_now
                        _service_stats["updates_sent"] += 1
                        _service_stats["last_update_at"] = utc_now_iso()
                    else:
                        _service_stats["errors"] += 1
                except Exception as e:
                    logger.error(f"Error sending update from thread: {e}")
                    _service_stats["errors"] += 1

            # Throttle to detection interval
            elapsed = time.monotonic() - loop_start
            sleep_time = max(0.0, interval - elapsed)
            time.sleep(sleep_time)

    await asyncio.to_thread(_blocking_stream)


# ── FastAPI Lifecycle ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    global _detector, _slot_manager, _backend_client, _detection_task

    logger.info("=== SmartPark Edge Occupancy Service starting ===")

    # Initialise components
    _detector = VehicleDetector()
    _slot_manager = SlotManager()
    _backend_client = BackendClient()

    await _backend_client.start()
    await _backend_client.check_backend_health()

    # Launch detection loop as background task
    _detection_task = asyncio.create_task(_run_detection_loop())
    _service_stats["started_at"] = utc_now_iso()

    logger.info(
        f"Edge service ready — parking_id={settings.PARKING_ID}, "
        f"total_slots={settings.TOTAL_PARKING_SLOTS}"
    )

    yield   # ← app runs here

    # Shutdown
    logger.info("Shutting down edge service…")
    if _detection_task and not _detection_task.done():
        _detection_task.cancel()
        try:
            await _detection_task
        except asyncio.CancelledError:
            pass

    await _backend_client.stop()
    logger.info("=== SmartPark Edge Occupancy Service stopped ===")


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="SmartPark Edge Occupancy Service",
    description=(
        "Local AI service that detects parking occupancy from camera feeds "
        "and reports status to the SmartPark backend. "
        "Camera video is processed locally — never streamed to the cloud."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Liveness probe — returns 200 if the service is running."""
    task_alive = _detection_task is not None and not _detection_task.done()
    return {
        "status": "ok" if task_alive else "degraded",
        "detection_loop": "running" if task_alive else "stopped",
        "timestamp": utc_now_iso(),
    }


@app.get("/status", tags=["Occupancy"])
async def get_status():
    """Return the current occupancy snapshot from the slot manager."""
    if _slot_manager is None:
        return JSONResponse({"error": "Service not ready"}, status_code=503)

    summary = _slot_manager.current_summary()
    return {
        **summary,
        "service_stats": _service_stats,
        "timestamp": utc_now_iso(),
    }


@app.get("/config", tags=["Monitoring"])
async def get_config():
    """Return non-sensitive configuration for debugging."""
    return {
        "parking_id": settings.PARKING_ID,
        "camera_source": settings.CAMERA_SOURCE,
        "total_slots": settings.TOTAL_PARKING_SLOTS,
        "detection_interval_sec": settings.DETECTION_INTERVAL_SEC,
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
        "hysteresis_frames": settings.HYSTERESIS_FRAMES,
        "operating_mode": "region" if settings.SLOT_REGIONS else "count",
        "slot_region_count": len(settings.SLOT_REGIONS),
        "vehicle_class_ids": settings.VEHICLE_CLASS_IDS,
        "django_api_url": settings.DJANGO_API_URL,
    }

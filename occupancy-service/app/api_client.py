"""
SmartPark AI — Edge API Client
================================
Sends occupancy updates to the Django REST backend.
Uses async httpx with exponential backoff retry.
Authentication via X-Edge-Secret header.
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger("occupancy_service.api_client")


class BackendClient:
    """
    Async HTTP client that POSTs occupancy snapshots to the Django backend.

    Usage:
        client = BackendClient()
        await client.send_occupancy_update(summary)
    """

    def __init__(self):
        self._base_url = settings.DJANGO_API_URL.rstrip("/")
        self._secret = settings.API_SECRET_KEY
        self._max_retries = settings.MAX_RETRIES
        self._backoff = settings.RETRY_BACKOFF_SEC

        self._headers = {
            "Content-Type": "application/json",
            "X-Edge-Secret": self._secret,
        }

        # Persistent async client (connection pooling)
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Open the persistent HTTP connection pool."""
        self._client = httpx.AsyncClient(
            headers=self._headers,
            timeout=httpx.Timeout(10.0),
        )
        logger.info(f"BackendClient connected to {self._base_url}")

    async def stop(self) -> None:
        """Close the HTTP connection pool gracefully."""
        if self._client:
            await self._client.aclose()
            logger.info("BackendClient closed.")

    # ── Occupancy Update ──────────────────────────────────────────────────────

    async def send_occupancy_update(self, summary: dict) -> bool:
        """
        POST occupancy snapshot to Django.

        Payload shape:
        {
            "parking_id": "P001",
            "total_slots": 20,
            "occupied_slots": 12,
            "available_slots": 8,
            "occupancy_rate": 60.0,
            "slot_states": {"S1": true, "S2": false, ...},
            "timestamp": "2026-06-10T15:00:00+00:00"
        }

        Returns True on success, False after all retries exhausted.
        """
        payload = {
            "parking_id": summary["parking_id"],
            "total_slots": summary["total_slots"],
            "occupied_slots": summary["occupied_slots"],
            "available_slots": summary["available_slots"],
            "occupancy_rate": summary["occupancy_rate"],
            "slot_states": summary.get("slot_states", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        url = f"{self._base_url}/occupancy/update/"

        for attempt in range(1, self._max_retries + 1):
            try:
                resp = await self._client.post(url, json=payload)
                if resp.status_code in (200, 201):
                    logger.debug(
                        f"Occupancy update sent: {payload['occupied_slots']}"
                        f"/{payload['total_slots']} occupied "
                        f"({payload['occupancy_rate']}%)"
                    )
                    return True
                else:
                    logger.warning(
                        f"Backend returned {resp.status_code}: {resp.text[:200]}"
                    )
            except httpx.ConnectError:
                logger.warning(
                    f"Cannot reach backend at {url} "
                    f"(attempt {attempt}/{self._max_retries})"
                )
            except httpx.TimeoutException:
                logger.warning(
                    f"Backend request timed out "
                    f"(attempt {attempt}/{self._max_retries})"
                )
            except Exception as e:
                logger.error(f"Unexpected error sending update: {e}")

            if attempt < self._max_retries:
                wait = self._backoff * (2 ** (attempt - 1))   # exponential backoff
                logger.info(f"Retrying in {wait:.1f}s…")
                await asyncio.sleep(wait)

        logger.error("All retry attempts exhausted. Occupancy update dropped.")
        return False

    # ── Health Check ──────────────────────────────────────────────────────────

    async def check_backend_health(self) -> bool:
        """Ping the backend to verify connectivity at startup."""
        url = f"{self._base_url}/occupancy/all/"
        try:
            resp = await self._client.get(url, timeout=5.0)
            healthy = resp.status_code < 500
            logger.info(
                f"Backend health check: {'OK' if healthy else 'DEGRADED'} "
                f"({resp.status_code})"
            )
            return healthy
        except Exception as e:
            logger.warning(f"Backend health check failed: {e}")
            return False

# ─────────────────────────────────────────────────────────────────────────────
# SmartPark AI — Edge Occupancy Service
# Docker image: Python 3.11 slim, CPU-only (no GPU required)
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Dependency Builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System packages for OpenCV headless + httpx
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime Image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="SmartPark AI Team"
LABEL description="Edge AI occupancy detection service — local inference only"

WORKDIR /service

# Copy only installed packages from builder
COPY --from=builder /install /usr/local

# System libs required by OpenCV at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY app/ ./app/
COPY models/ ./models/

# YOLOv8 will auto-download yolov8n.pt on first run if not present.
# To use a custom model, bind-mount your .pt file to /service/models/yolov8n.pt

# Non-root user for security
RUN useradd -m -u 1001 edgeuser
USER edgeuser

# Expose FastAPI port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

# Run the service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "info"]

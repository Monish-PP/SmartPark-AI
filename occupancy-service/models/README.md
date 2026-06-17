# YOLOv8 Model Directory

Place your YOLOv8 model file here as `yolov8n.pt`.

## Auto-Download (Recommended)

The service will automatically download `yolov8n.pt` (6 MB, CPU-optimised)
from Ultralytics on first run if no model file is found here.
No manual action required for development.

## Custom / Fine-Tuned Model

For production with higher accuracy on parking-lot cameras:

1. Download the PKLot fine-tuned model from Roboflow Universe:
   https://universe.roboflow.com/brad-dwyer/pklot-1tros

2. Place the downloaded `.pt` file here as `yolov8n.pt`
   (or update `MODEL_PATH` in `app/detector.py`).

3. Rebuild the Docker image:
   ```bash
   docker build -t smartpark-edge .
   ```

## Model Size Comparison

| Model        | Size  | mAP50 | Latency (CPU) | Recommended For       |
|-------------|-------|-------|---------------|-----------------------|
| yolov8n.pt  | 6 MB  | 37.3  | ~50ms/frame   | Development, low-spec |
| yolov8s.pt  | 22 MB | 44.9  | ~90ms/frame   | Production, CPU       |
| yolov8m.pt  | 52 MB | 50.2  | ~200ms/frame  | High accuracy         |

All models run on CPU — no GPU required.

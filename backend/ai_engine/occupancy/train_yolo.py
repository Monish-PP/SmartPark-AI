"""
SmartPark AI — PKLot Dataset Trainer
======================================
Fine-tunes YOLOv8 on the PKLot dataset for parking slot
occupied/empty classification.

PKLot Dataset (choose one):
  - Roboflow: https://universe.roboflow.com/brad-dwyer/pklot-1tros
  - Original:  https://web.inf.ufpr.br/vri/databases/parking-lot-database/

Usage:
    python ai_engine/occupancy/train_yolo.py \
        --data data/pklot.yaml \
        --epochs 50 \
        --imgsz 640 \
        --batch 16 \
        --output ml_models/
"""

import argparse
import os
from pathlib import Path


def create_pklot_yaml(dataset_dir: str, output_path: str = "data/pklot.yaml"):
    """Create YOLO-format dataset YAML for PKLot."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    yaml_content = f"""
path: {os.path.abspath(dataset_dir)}
train: images/train
val:   images/val
test:  images/test

nc: 2
names:
  0: empty
  1: occupied
"""
    with open(output_path, "w") as f:
        f.write(yaml_content.strip())
    print(f"Dataset YAML written to {output_path}")
    return output_path


def train(data_yaml: str, epochs: int = 50, imgsz: int = 640,
          batch: int = 16, output_dir: str = "ml_models"):
    """
    Fine-tune YOLOv8n on PKLot dataset.
    Downloads YOLOv8n pretrained weights automatically.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        raise RuntimeError("Run: pip install ultralytics")

    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("SmartPark AI — YOLOv8 PKLot Training")
    print("=" * 60)
    print(f"  Dataset :  {data_yaml}")
    print(f"  Epochs  :  {epochs}")
    print(f"  Image   :  {imgsz}x{imgsz}")
    print(f"  Batch   :  {batch}")
    print("=" * 60)

    try:
        import torch
        device = "0" if torch.cuda.is_available() else "cpu"
    except Exception:
        device = "cpu"

    workers = 0 if device == "cpu" else 4

    # Load YOLOv8 nano (fastest, suitable for edge deployment)
    model = YOLO("yolov8n.pt")

    # Train
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name="pklot_smartpark",
        project=output_dir,
        patience=15,              # Early stopping
        save=True,
        plots=True,
        val=True,
        workers=workers,
        device=device,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        mosaic=1.0,
        augment=True,
        degrees=10,
        fliplr=0.5,
        scale=0.5,
    )

    # Copy best weights to ml_models/
    best_weights = Path(output_dir) / "pklot_smartpark" / "weights" / "best.pt"
    final_path = Path(output_dir) / "yolov8_parking.pt"

    if best_weights.exists():
        import shutil
        shutil.copy(best_weights, final_path)
        print(f"\n✅ Best model saved to: {final_path}")
    else:
        print("\n⚠️  Training complete but best.pt not found automatically.")

    # Validation
    print("\nRunning validation on test set...")
    metrics = model.val(data=data_yaml, split="test")
    print(f"  mAP50    : {metrics.box.map50:.3f}")
    print(f"  mAP50-95 : {metrics.box.map:.3f}")

    return results, metrics


def prepare_pklot_dataset(raw_dir: str, output_dir: str = "data/pklot_yolo"):
    """
    Convert raw PKLot dataset (XML annotations) to YOLO format.

    PKLot raw structure:
      PKLot/
        PUCPR/ UFPR04/ UFPR05/
          {weather}/
            {date}/
              {timestamp}.jpg
              {timestamp}.xml

    YOLO output structure:
      data/pklot_yolo/
        images/train/ images/val/ images/test/
        labels/train/ labels/val/ labels/test/
    """
    import xml.etree.ElementTree as ET
    import shutil
    import random

    for split in ["train", "val", "test"]:
        os.makedirs(f"{output_dir}/images/{split}", exist_ok=True)
        os.makedirs(f"{output_dir}/labels/{split}", exist_ok=True)

    all_pairs = []
    for root, dirs, files in os.walk(raw_dir):
        for fname in files:
            if fname.endswith(".xml"):
                xml_path = os.path.join(root, fname)
                img_path = xml_path.replace(".xml", ".jpg")
                if os.path.exists(img_path):
                    all_pairs.append((img_path, xml_path))

    random.shuffle(all_pairs)
    n = len(all_pairs)
    train_end = int(n * 0.7)
    val_end   = int(n * 0.85)

    splits = {
        "train": all_pairs[:train_end],
        "val":   all_pairs[train_end:val_end],
        "test":  all_pairs[val_end:],
    }

    for split, pairs in splits.items():
        for img_path, xml_path in pairs:
            # Parse XML
            tree = ET.parse(xml_path)
            root_el = tree.getroot()

            img_w = int(root_el.find("size/width").text)
            img_h = int(root_el.find("size/height").text)

            lines = []
            for space in root_el.findall("space"):
                occupied = int(space.get("occupied", 0))
                cls = 1 if occupied else 0

                # Get rotated rect or regular contour
                rotated = space.find("rotatedRect")
                if rotated is not None:
                    cx = float(rotated.find("center").get("x")) / img_w
                    cy = float(rotated.find("center").get("y")) / img_h
                    w  = float(rotated.find("size").get("w")) / img_w
                    h  = float(rotated.find("size").get("h")) / img_h
                    lines.append(f"{cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
                else:
                    # Use contour bounding box as fallback
                    contour = space.find("contour")
                    if contour is None:
                        continue
                    points = contour.findall("point")
                    xs = [int(p.get("x")) for p in points]
                    ys = [int(p.get("y")) for p in points]
                    xmin, xmax = min(xs), max(xs)
                    ymin, ymax = min(ys), max(ys)
                    cx = ((xmin + xmax) / 2) / img_w
                    cy = ((ymin + ymax) / 2) / img_h
                    bw = (xmax - xmin) / img_w
                    bh = (ymax - ymin) / img_h
                    lines.append(f"{cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

            # Write label file
            basename = os.path.splitext(os.path.basename(img_path))[0]
            label_dst = f"{output_dir}/labels/{split}/{basename}.txt"
            with open(label_dst, "w") as f:
                f.write("\n".join(lines))

            # Copy image
            img_dst = f"{output_dir}/images/{split}/{os.path.basename(img_path)}"
            shutil.copy(img_path, img_dst)

    print(f"\n✅ PKLot dataset converted to YOLO format at '{output_dir}'")
    print(f"   Train: {len(splits['train'])} | Val: {len(splits['val'])} | Test: {len(splits['test'])}")

    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 on PKLot dataset")
    parser.add_argument("--data",     default="data/pklot.yaml",   help="Path to dataset YAML")
    parser.add_argument("--raw_dir",  default="",                   help="Raw PKLot dir (for conversion)")
    parser.add_argument("--epochs",   type=int, default=50)
    parser.add_argument("--imgsz",    type=int, default=640)
    parser.add_argument("--batch",    type=int, default=16)
    parser.add_argument("--output",   default="ml_models/")
    args = parser.parse_args()

    # Step 1: Convert raw PKLot to YOLO format (if raw_dir provided)
    if args.raw_dir:
        out_dir = prepare_pklot_dataset(args.raw_dir, "data/pklot_yolo")
        yaml_path = create_pklot_yaml(out_dir, "data/pklot.yaml")
        args.data = yaml_path

    # Step 2: Train
    train(
        data_yaml=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        output_dir=args.output,
    )

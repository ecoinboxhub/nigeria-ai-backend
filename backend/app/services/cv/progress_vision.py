import base64
import os
from pathlib import Path
from typing import Any

import cv2
import mlflow
import numpy as np

MODEL_PATH = "yolov8n.pt"


class ProgressVisionService:
    def __init__(self) -> None:
        self._model = None

    def _load_model(self):
        if self._model is None:
            os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(".ultralytics").resolve()))
            from ultralytics import YOLO

            self._model = YOLO(MODEL_PATH)
        return self._model

    def _decode_image(self, image_base64: str) -> np.ndarray:
        raw = base64.b64decode(image_base64)
        np_arr = np.frombuffer(raw, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img

    def analyze(self, image_base64: str, planned_completion_pct: float) -> dict[str, Any]:
        img = self._decode_image(image_base64)
        if img is None:
            return {
                "detected_objects": [],
                "ppe_compliance_score": 0.0,
                "detected_completion_pct": 0.0,
                "deviation_pct": planned_completion_pct,
                "exceeds_threshold": planned_completion_pct > 15,
            }

        img = cv2.resize(img, (1280, 720))
        img = cv2.GaussianBlur(img, (3, 3), 0)

        model = self._load_model()
        results = model.predict(img, verbose=False)
        detected = []
        worker_count = 0
        ppe_hits = 0

        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for b in boxes:
                cls_id = int(b.cls[0])
                conf = float(b.conf[0])
                name = model.names.get(cls_id, str(cls_id))
                x1, y1, x2, y2 = [float(v) for v in b.xyxy[0].tolist()]
                detected.append(
                    {
                        "label": name,
                        "confidence": round(conf, 4),
                        "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                    }
                )
                if name == "person":
                    worker_count += 1
                if name in {"helmet", "sports ball", "backpack", "vest"}:
                    ppe_hits += 1

        detected_completion_pct = min(100.0, float(len(detected)) * 2.5)
        deviation_pct = abs(planned_completion_pct - detected_completion_pct)
        ppe_score = 1.0 if worker_count == 0 else min(1.0, ppe_hits / worker_count)

        Path("data/processed/site_images").mkdir(parents=True, exist_ok=True)
        out_file = Path("data/processed/site_images") / "last_inference.jpg"
        cv2.imwrite(str(out_file), img)

        mlflow.set_experiment("progress_visualizer")
        with mlflow.start_run(run_name="yolo_inference"):
            mlflow.log_metric("detections", len(detected))
            mlflow.log_metric("ppe_score", ppe_score)
            mlflow.log_metric("deviation_pct", deviation_pct)

        return {
            "detected_objects": detected,
            "ppe_compliance_score": round(ppe_score, 4),
            "detected_completion_pct": round(detected_completion_pct, 2),
            "deviation_pct": round(deviation_pct, 2),
            "exceeds_threshold": deviation_pct > 15,
        }


progress_vision_service = ProgressVisionService()

from ultralytics import YOLO
from typing import List
from domain.Models.frame import Frame
from domain.Models.plate import Plate
from domain.Interfaces.plate_detector import IPlateDetector

class YOLOPlateDetector(IPlateDetector):
    """
    Detector de placas usando YOLOv8.
    """
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = YOLO(model_path)

    def detect(self, frame: Frame) -> List[Plate]:
        results = self.model(frame.image)
        plates: List[Plate] = []

        for r in results[0].boxes:
            x1, y1, x2, y2 = map(int, r.xyxy[0])  # bounding box
            conf = float(r.conf[0])
            
            # Aquí text se llena luego por el OCR
            plates.append(Plate(
                text="",
                confidence=conf,
                bounding_box=(x1, y1, x2-x1, y2-y1)
            ))

        return plates

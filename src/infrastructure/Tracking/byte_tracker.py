# src/infrastructure/Tracking/byte_tracker_adapter.py

from typing import List, Tuple, Optional
import numpy as np

from src.domain.Interfaces.tracker import ITracker
from src.domain.Models.plate import Plate
from src.infrastructure.Tracking.byteTracker.byte_tracker import BYTETracker
from src.core.config import settings


def xywh_to_xyxy(x: int, y: int, w: int, h: int) -> Tuple[float, float, float, float]:
    """Convierte (x, y, w, h) -> (x_min, y_min, x_max, y_max)."""
    x_min = float(x)
    y_min = float(y)
    x_max = float(x + w)
    y_max = float(y + h)
    return x_min, y_min, x_max, y_max


def iou_xyxy(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Calcula matriz IoU entre arrays:
    a: [N,4] (x_min, y_min, x_max, y_max)
    b: [M,4]
    -> return [N, M]
    """
    N, M = a.shape[0], b.shape[0]
    ious = np.zeros((N, M), dtype=float)
    for i in range(N):
        ax1, ay1, ax2, ay2 = a[i]
        area_a = max(ax2 - ax1, 0) * max(ay2 - ay1, 0)
        for j in range(M):
            bx1, by1, bx2, by2 = b[j]
            inter_x1 = max(ax1, bx1)
            inter_y1 = max(ay1, by1)
            inter_x2 = min(ax2, bx2)
            inter_y2 = min(ay2, by2)
            inter_w = max(0.0, inter_x2 - inter_x1)
            inter_h = max(0.0, inter_y2 - inter_y1)
            inter_area = inter_w * inter_h
            area_b = max(bx2 - bx1, 0) * max(by2 - by1, 0)
            union = area_a + area_b - inter_area + 1e-6
            ious[i, j] = inter_area / union if union > 0 else 0.0
    return ious


class ByteTrackerAdapter(ITracker):
    """
    Adaptador de ByteTrack al contrato ITracker.
    - Transforma tus `Plate` a detecciones que ByteTrack espera.
    - Llama a BYTETracker.update y devuelve los mismos `Plate` con track_id.
    - Configuración tomada de variables de entorno (.env) vía settings.
    """

    def __init__(self):
        self._args_dict = {
            "track_thresh": settings.bytetrack_thresh,
            "match_thresh": settings.bytetrack_match_thresh,
            "track_buffer": settings.bytetrack_buffer_size,
            "frame_rate": settings.bytetrack_fps,
        }
        self._tracker = BYTETracker(self._args_dict)
        self._image_size: Optional[Tuple[int, int]] = None  # (height, width)

    def set_image_size(self, image_size: Tuple[int, int]) -> None:
        """Define el tamaño del frame (H, W). Debe llamarse una vez por frame."""
        self._image_size = image_size

    def update(self, plates: List[Plate]) -> List[Plate]:
        """
        Asigna un track_id a cada Plate. Requiere que `set_image_size` se haya llamado antes.
        Mantiene la firma ITracker.update(plates) para no romper el service.
        """
        if not plates:
            return plates

        if self._image_size is None:
            raise RuntimeError(
                "ByteTrackerAdapter.update llamado sin definir image_size. "
                "Invoca primero set_image_size((height, width)) por frame."
            )

        # 1) Construir detecciones para ByteTrack: [x_min, y_min, x_max, y_max, score]
        detections = []
        for plate in plates:
            x, y, w, h = plate.bounding_box
            x_min, y_min, x_max, y_max = xywh_to_xyxy(x, y, w, h)
            score = float(getattr(plate, "confidence", 1.0))
            detections.append([x_min, y_min, x_max, y_max, score])

        detections_np = np.array(detections, dtype=float) if detections else np.empty((0, 5), dtype=float)

        # 2) Ejecutar ByteTrack
        height, width = self._image_size
        online_tracks = self._tracker.update(detections_np, (height, width), (height, width))

        # 3) Asociar tracks a tus Plate por IoU máximo
        track_boxes = []
        track_ids = []
        for track in online_tracks:
            box_xyxy = track.tlbr  # (x_min, y_min, x_max, y_max)
            if box_xyxy is None or len(box_xyxy) != 4:
                continue
            track_boxes.append(box_xyxy.astype(float))
            track_ids.append(int(track.track_id))

        if not track_boxes:
            for plate in plates:
                plate.track_id = None
            return plates

        track_boxes_np = np.stack(track_boxes, axis=0)  # [T,4]
        plate_boxes_np = np.array(
            [xywh_to_xyxy(*p.bounding_box) for p in plates],
            dtype=float
        )  # [P,4]

        iou_matrix = iou_xyxy(plate_boxes_np, track_boxes_np)  # [P,T]
        best_track_index = np.argmax(iou_matrix, axis=1)
        best_iou = np.max(iou_matrix, axis=1)

        for i, plate in enumerate(plates):
            if best_iou[i] > 0.1:
                plate.track_id = track_ids[best_track_index[i]]
            else:
                plate.track_id = None

        return plates

# src/application/plate_recognition_service.py
# (mantén las demás importaciones y funciones que tenías; sólo muestro el archivo completo actualizado)

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="yolov5")

import time
import uuid
import cv2
import logging
from typing import Any, Iterable, Tuple

from src.domain.Models.detection_result import DetectionResult
from src.domain.Interfaces.camera_stream import ICameraStream
from src.domain.Interfaces.plate_detector import IPlateDetector
from src.domain.Interfaces.ocr_reader import IOCRReader
from src.domain.Interfaces.event_publisher import IEventPublisher
from src.domain.Interfaces.tracker import ITracker
from src.domain.Interfaces.deduplicator import IDeduplicator
from src.domain.Interfaces.text_normalizer import ITextNormalizer
from src.core.config import settings

logger = logging.getLogger(__name__)

class PlateRecognitionService:
    def __init__(
        self,
        camera_stream: ICameraStream,
        detector: IPlateDetector,
        ocr_reader: IOCRReader,
        publisher: IEventPublisher,
        tracker: ITracker,
        deduplicator: IDeduplicator,
        normalizer: ITextNormalizer,
        debug_show: bool = True,
        loop_delay: float = 0.0,
    ):
        self.camera_stream = camera_stream
        self.detector = detector
        self.ocr_reader = ocr_reader
        self.publisher = publisher
        self.tracker = tracker
        self.deduplicator = deduplicator
        self.normalizer = normalizer

        self.debug_show = debug_show
        self.loop_delay = loop_delay

        self.running = False
        self.frame_idx = 0
        self.camera_id = getattr(self.camera_stream, "camera_id", None) or "default"
        self.target_dt = getattr(settings, "target_frame_seconds", 0.0)

    def start(self):
        self.camera_stream.connect()
        self.running = True
        logger.info("Servicio de reconocimiento iniciado (camera_id=%s)", self.camera_id)

        try:
            while self.running:
                loop_start = time.perf_counter()

                frame = self.camera_stream.read_frame()
                if frame is None:
                    logger.warning("No se pudo leer frame, reintentando...")
                    time.sleep(0.5)
                    self._pace(loop_start)
                    continue

                # 1) Detectar bboxes
                plates_bboxes = self.detector.detect(frame)

                # 2) OCR gate por intervalo
                run_ocr = (self.frame_idx % max(1, settings.ocr_interval)) == 0
                raw_ocr_results = []
                if run_ocr and plates_bboxes:
                    for bbox in plates_bboxes:
                        try:
                            raw = self.ocr_reader.read_text(frame, bbox)
                            raw_ocr_results.append(raw)
                        except Exception as e:
                            logger.exception("OCR falló para bbox=%s: %s", getattr(bbox, "bbox", None), e)

                # 3) Filtrado operativo mínimo + normalización
                normalized_results = []
                for r in raw_ocr_results:
                    raw_text = getattr(r, "text", None)
                    if not raw_text:
                        continue
                    norm = self.normalizer.normalize(raw_text)
                    if not norm:
                        continue
                    conf = getattr(r, "confidence", 1.0)
                    if conf < settings.ocr_min_confidence:
                        continue
                    # evita mutaciones inesperadas: crea una copia ligera
                    new_plate = type(r)(**{k: getattr(r, k) for k in getattr(r, "__dict__", {})}) if hasattr(r, "__dict__") else r
                    # Algunos readers devuelven Plate ya; garantizamos .text actualizado
                    try:
                        new_plate.text = norm
                    except Exception:
                        # si no podemos mutar, crear un objeto simple con los atributos necesarios
                        class _P: pass
                        new_plate = _P()
                        new_plate.text = norm
                        new_plate.bounding_box = getattr(r, "bounding_box", None)
                        new_plate.confidence = getattr(r, "confidence", 1.0)
                    normalized_results.append(new_plate)

                # 4) Tracking -> pasar tamaño del frame (height, width)
                h, w = frame.data.shape[:2]
                try:
                    tracked_results = self.tracker.update(normalized_results, image_size=(h, w)) if normalized_results else []
                except TypeError:
                    # compatibilidad: si la implementación antigua no acepta image_size
                    logger.debug("Tracker.update() no acepta image_size, usando firma antigua.")
                    tracked_results = self.tracker.update(normalized_results) if normalized_results else []

                # 5) Deduplicación (por track_id + texto + camera_id)
                unique_results = []
                for plate in tracked_results:
                    text = getattr(plate, "text", None)
                    track_id = getattr(plate, "track_id", None)
                    if not text:
                        continue
                    try:
                        is_dup = self.deduplicator.is_duplicate(
                            track_id=track_id,
                            plate_text=text,
                            camera_id=self.camera_id
                        )
                    except TypeError:
                        is_dup = self.deduplicator.is_duplicate(track_id=track_id, plate_text=text)
                    except Exception:
                        logger.exception("Deduplicator error para track=%s text=%s", track_id, text)
                        is_dup = True

                    if not is_dup:
                        unique_results.append(plate)

                if not unique_results:
                    self.frame_idx += 1
                    self._pace(loop_start)
                    continue

                # 6) Construir DetectionResult
                captured_at = getattr(frame, "timestamp", None) or time.time()
                source = getattr(frame, "source", None) or getattr(self.camera_stream, "url", None) or settings.camera_url
                event_id = self._build_event_id(self.camera_id, unique_results, captured_at)

                result = DetectionResult(
                    event_id=event_id,
                    frame_id=str(uuid.uuid4()),
                    plates=unique_results,
                    processed_at=time.time(),
                    source=source,
                    captured_at=captured_at,
                    camera_id=self.camera_id
                )

                # 7) Publicar
                try:
                    self.publisher.publish(result)
                except Exception as e:
                    logger.exception("Publish failed: %s", e)

                # 8) Debug UI seguro
                if self.debug_show and hasattr(cv2, "imshow"):
                    try:
                        cv2.imshow("Stream", frame.data)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            logger.info("Se recibió señal de salida (q)")
                            break
                    except Exception:
                        logger.warning("imshow no disponible; desactivando debug_show")
                        self.debug_show = False

                self.frame_idx += 1
                self._pace(loop_start)

        except KeyboardInterrupt:
            logger.info("Servicio detenido manualmente (Ctrl+C)")
        finally:
            self.stop()

    def stop(self):
        try:
            self.camera_stream.disconnect()
        except Exception:
            logger.exception("Error al desconectar camera_stream")
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        self.running = False
        logger.info("Servicio detenido correctamente")

    # helpers (igual que antes)
    def _build_event_id(self, camera_id: str, plates: Iterable[Any], captured_at: float) -> str:
        first = next(iter(plates))
        track_id = getattr(first, "track_id", "na")
        text = getattr(first, "text", "NA")
        return f"{camera_id}:{track_id}:{text}:{int(captured_at)}"

    def _pace(self, loop_start: float) -> None:
        if getattr(self, "target_dt", 0.0):
            elapsed = time.perf_counter() - loop_start
            sleep = max(0.0, self.target_dt - elapsed)
            if sleep > 0:
                time.sleep(sleep)
        elif self.loop_delay > 0:
            time.sleep(self.loop_delay)

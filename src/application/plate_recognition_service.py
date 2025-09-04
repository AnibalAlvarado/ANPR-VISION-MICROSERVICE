import time
import uuid
import cv2
import logging
from src.domain.Models.detection_result import DetectionResult
from src.domain.Interfaces.camera_stream import ICameraStream
from src.domain.Interfaces.plate_detector import IPlateDetector
from src.domain.Interfaces.ocr_reader import IOCRReader
from src.domain.Interfaces.event_publisher import IEventPublisher
from src.utils.deduplicator import Deduplicator  # 👈 import deduplicador

logger = logging.getLogger(__name__)

class PlateRecognitionService:
    """
    Orquesta el flujo de reconocimiento de placas:
    - Captura frames desde la cámara
    - Detecta posibles placas
    - Lee texto de las placas con OCR
    - Filtra duplicados
    - Publica el resultado en un broker (o consola en dummy)
    """

    def __init__(
        self,
        camera_stream: ICameraStream,
        detector: IPlateDetector,
        ocr_reader: IOCRReader,
        publisher: IEventPublisher,
        debug_show: bool = True,
        loop_delay: float = 0.0,
        dedup_ttl: float = 3.0,
        similarity_threshold: float = 0.9   # 👈 nuevo parámetro
    ):
        self.camera_stream = camera_stream
        self.detector = detector
        self.ocr_reader = ocr_reader
        self.publisher = publisher
        self.running = False
        self.debug_show = True
        self.loop_delay = loop_delay
        self.deduplicator = Deduplicator(ttl=dedup_ttl, similarity_threshold=similarity_threshold)

    def start(self):
        """Inicia el proceso continuo de reconocimiento."""
        self.camera_stream.connect()
        self.running = True
        logger.info("✅ Servicio de reconocimiento iniciado")

        try:
            while self.running:
                frame = self.camera_stream.read_frame()
                if frame is None:
                    logger.warning("⚠️ No se pudo leer frame, reintentando...")
                    time.sleep(0.5)
                    continue

                # Detectar placas
                plates = self.detector.detect(frame)

                # Aplicar OCR si hay placas
                ocr_results = [self.ocr_reader.read_text(frame, p) for p in plates]

                # Filtrar duplicados
                unique_results = [
                    plate for plate in ocr_results
                    if plate.text and not self.deduplicator.is_duplicate(plate.text)
                ]

                if not unique_results:
                    continue  # nada nuevo, saltamos

                result = DetectionResult(
                    frame_id=str(uuid.uuid4()),
                    plates=unique_results,  # 👈 lista de Plate con text + confidence + bbox
                    processed_at=time.time(),
                    source=frame.source,
                    captured_at=frame.timestamp
                )

                self.publisher.publish(result)

                # Publicar resultado
                self.publisher.publish(result)

                # Mostrar frame (solo en modo debug local)
                if self.debug_show:
                    cv2.imshow("Stream", frame.data)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        logger.info(" Se recibió señal de salida (q)")
                        break

                if self.loop_delay > 0:
                    time.sleep(self.loop_delay)

        except KeyboardInterrupt:
            logger.info("🛑 Servicio detenido manualmente (Ctrl+C)")
        finally:
            self.stop()

    def stop(self):
        """Detiene el proceso."""

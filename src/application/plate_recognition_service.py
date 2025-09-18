import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="yolov5")
import time
import uuid
import cv2
import logging
from src.domain.Models.detection_result import DetectionResult
from src.domain.Interfaces.camera_stream import ICameraStream
from src.domain.Interfaces.plate_detector import IPlateDetector
from src.domain.Interfaces.ocr_reader import IOCRReader
from src.domain.Interfaces.event_publisher import IEventPublisher
from src.domain.Interfaces.tracker import ITracker  
from src.utils.deduplicator import Deduplicator

logger = logging.getLogger(__name__)

class PlateRecognitionService:
    """
    Orquesta el flujo de reconocimiento de placas:
    - Captura frames desde la cámara
    - Detecta posibles placas
    - Lee texto de las placas con OCR
    - Asigna track_id con el tracker
    - Filtra duplicados
    - Publica el resultado
    """

    def __init__(
        self,
        camera_stream: ICameraStream,
        detector: IPlateDetector,
        ocr_reader: IOCRReader,
        publisher: IEventPublisher,
        tracker: ITracker,            
        debug_show: bool = True,
        loop_delay: float = 0.0,
        dedup_ttl: float = 3.0,
        similarity_threshold: float = 0.9
    ):
        self.camera_stream = camera_stream
        self.detector = detector
        self.ocr_reader = ocr_reader
        self.publisher = publisher
        self.tracker = tracker           
        self.running = False
        self.debug_show = debug_show
        self.loop_delay = loop_delay
        self.deduplicator = Deduplicator(
            ttl=dedup_ttl,
            similarity_threshold=similarity_threshold
        )

    def start(self):
        """Inicia el proceso continuo de reconocimiento."""
        self.camera_stream.connect()
        self.running = True
        logger.info(" Servicio de reconocimiento iniciado")

        try:
            while self.running:
                frame = self.camera_stream.read_frame()
                if frame is None:
                    logger.warning(" No se pudo leer frame, reintentando...")
                    time.sleep(0.5)
                    continue

                # Detectar placas (solo bounding boxes)
                plates = self.detector.detect(frame)

                # Aplicar OCR a cada placa
                ocr_results = [self.ocr_reader.read_text(frame, p) for p in plates]

                # Asignar track_id a cada placa
                tracked_results = self.tracker.update(ocr_results)

                # Filtrar duplicados (basado en texto)
                unique_results = [
                    plate for plate in tracked_results
                    if plate.text and not self.deduplicator.is_duplicate(plate.text)
                ]

                if not unique_results:
                    continue  # nada nuevo, saltamos

                result = DetectionResult(
                    frame_id=str(uuid.uuid4()),
                    plates=unique_results,
                    processed_at=time.time(),
                    source=frame.source,
                    captured_at=frame.timestamp
                )

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
            logger.info(" Servicio detenido manualmente (Ctrl+C)")
        finally:
            self.stop()

    def stop(self):
        """Detiene el proceso."""
        self.camera_stream.disconnect()
        cv2.destroyAllWindows()
        self.running = False
        logger.info(" Servicio detenido correctamente")

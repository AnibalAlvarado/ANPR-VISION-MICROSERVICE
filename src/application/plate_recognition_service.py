import time
import uuid
import cv2
from domain.Models.detection_result import DetectionResult
from domain.Interfaces.camera_stream import ICameraStream
from domain.Interfaces.plate_detector import IPlateDetector
from domain.Interfaces.ocr_reader import IOCRReader
from domain.Interfaces.event_publisher import IEventPublisher

class PlateRecognitionService:
    """
    Orquesta el flujo de reconocimiento de placas:
    - Captura frames desde la cámara
    - Detecta posibles placas
    - Lee texto de las placas con OCR
    - Publica el resultado en un broker (o consola en dummy)
    """

    def __init__(
        self,
        camera_stream: ICameraStream,
        detector: IPlateDetector,
        ocr_reader: IOCRReader,
        publisher: IEventPublisher
    ):
        self.camera_stream = camera_stream
        self.detector = detector
        self.ocr_reader = ocr_reader
        self.publisher = publisher
        self.running = False

    def start(self):
        """Inicia el proceso continuo de reconocimiento."""
        self.camera_stream.connect()
        self.running = True
        print("🚀 Servicio de reconocimiento iniciado")

        while self.running:
            frame = self.camera_stream.read_frame()
            if frame is None:
                print("⚠️ No se pudo leer frame, reintentando...")
                time.sleep(1)
                continue

            # Detectar placas
            plates = self.detector.detect(frame)

            # Aplicar OCR si hay placas
            ocr_results = [self.ocr_reader.read_text(frame, p) for p in plates]

            # Crear resultado
            result = DetectionResult(
                frame_id=str(uuid.uuid4()),
                plates=ocr_results,
                processed_at=time.time()
            )

            # Publicar resultado
            self.publisher.publish(result)

            # Mostrar frame en ventana de prueba
            cv2.imshow("Stream", frame.data)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Evitar sobrecargar CPU
            time.sleep(0.1)

    def stop(self):
        """Detiene el proceso."""
        self.running = False
        self.camera_stream.disconnect()
        print("🛑 Servicio detenido")

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="yolov5")
from src.infrastructure.Camera.opencv_camera_stream import OpenCVCameraStream
from src.infrastructure.Detector.YOLOPlateDetector import YOLOPlateDetector
from src.infrastructure.OCR.EasyOCR_OCRReader import EasyOCR_OCRReader
from src.infrastructure.Messaging.console_publisher import ConsolePublisher
from src.application.plate_recognition_service import PlateRecognitionService
from src.infrastructure.Detector.factory import create_plate_detector
from src.infrastructure.Camera.camera_factory import create_camera_stream
from src.infrastructure.Tracking.byte_tracker import ByteTrackerAdapter
from src.core.config import settings  

def main():
    # URL de cámara o video de prueba
    url = settings.camera_url  
    # Inicializar dependencias
    camera = create_camera_stream()
    detector = create_plate_detector()
    ocr = EasyOCR_OCRReader()
    publisher = ConsolePublisher()
    tracker = ByteTrackerAdapter()


    # Crear servicio principal con todos los parámetros configurables
    service = PlateRecognitionService(
        camera_stream=camera,
        detector=detector,
        ocr_reader=ocr,
        publisher=publisher,
        tracker=tracker,
        debug_show=settings.debug_show,
        loop_delay=settings.loop_delay,
        dedup_ttl=settings.dedup_ttl,
        similarity_threshold=settings.similarity_threshold
    )

    # Ejecutar
    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()

if __name__ == "__main__":
    main()

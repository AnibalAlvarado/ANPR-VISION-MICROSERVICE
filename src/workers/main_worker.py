from src.infrastructure.Camera.opencv_camera_stream import OpenCVCameraStream
from src.infrastructure.Detector.YOLOPlateDetector import YOLOPlateDetector
from src.infrastructure.OCR.EasyOCR_OCRReader import EasyOCR_OCRReader
from src.infrastructure.Messaging.console_publisher import ConsolePublisher
from src.application.plate_recognition_service import PlateRecognitionService
from src.infrastructure.Detector.factory import create_plate_detector
from src.core.config import settings  

def main():
    # URL de cámara o video de prueba
    url = settings.camera_url  # 👈 cámbiala si es necesario

    # Inicializar dependencias
    camera = OpenCVCameraStream(url)
    detector = create_plate_detector()
    ocr = EasyOCR_OCRReader()
    publisher = ConsolePublisher()

    # Crear servicio principal con todos los parámetros configurables
    service = PlateRecognitionService(
        camera_stream=camera,
        detector=detector,
        ocr_reader=ocr,
        publisher=publisher,
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

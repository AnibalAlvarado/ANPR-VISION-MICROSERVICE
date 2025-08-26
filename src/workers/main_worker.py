from infrastructure.Camera.opencv_camera_stream import OpenCVCameraStream
from infrastructure.Detector.dummy_plate_detector import DummyPlateDetector
from infrastructure.OCR.dummy_ocr_reader import DummyOCRReader
from infrastructure.Messaging.console_publisher import ConsolePublisher
from application.plate_recognition_service import PlateRecognitionService

def main():
    # 📹 URL de cámara o video de prueba
    url = "http://192.168.1.2:8080/video"  # Ejemplo: "rtsp://usuario:pass@192.168.1.100:554/stream"

    # Inicializar dependencias
    camera = OpenCVCameraStream(url)
    detector = DummyPlateDetector()
    ocr = DummyOCRReader()
    publisher = ConsolePublisher()

    # Crear servicio principal
    service = PlateRecognitionService(
        camera_stream=camera,
        detector=detector,
        ocr_reader=ocr,
        publisher=publisher
    )

    # Ejecutar
    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()

if __name__ == "__main__":
    main()

# main.py (worker)
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="yolov5")

from src.core.config import settings
from src.domain.Models.camera import Camera
from src.infrastructure.Camera.camera_factory import create_camera_stream
from src.infrastructure.Detector.factory import create_plate_detector
from src.infrastructure.OCR.EasyOCR_OCRReader import EasyOCR_OCRReader
from src.infrastructure.Tracking.byte_tracker import ByteTrackerAdapter
from src.infrastructure.Messaging.retry_publisher import RetryPublisher
from src.infrastructure.Messaging.console_publisher import ConsolePublisher
from src.domain.Services.deduplicator_service import DeduplicatorService
from src.infrastructure.Normalizer.plate_normalizer import PlateNormalizer
from src.application.plate_recognition_service import PlateRecognitionService

def main():
    # crear el modelo Camera (camera_id estable)
    cam = Camera(camera_id="cam_entrance_01", url=settings.camera_url, name="ENTRADA")

    # crear stream (la factory ahora acepta Camera y anexa camera_id al stream)
    camera_stream = create_camera_stream(cam)

    detector = create_plate_detector()
    ocr = EasyOCR_OCRReader()
    tracker = ByteTrackerAdapter()

    raw_publisher = ConsolePublisher()
    publisher = RetryPublisher(raw_publisher, attempts=3, base_delay=0.2)

    normalizer = PlateNormalizer(min_len=settings.plate_min_length)
    deduplicator = DeduplicatorService(normalizer=normalizer, ttl=settings.dedup_ttl)

    service = PlateRecognitionService(
        camera_stream=camera_stream,
        detector=detector,
        ocr_reader=ocr,
        publisher=publisher,
        tracker=tracker,
        deduplicator=deduplicator,
        normalizer=normalizer,
        debug_show=settings.debug_show,
        loop_delay=settings.loop_delay,
    )

    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()

if __name__ == "__main__":
    main()

import cv2
import time
from domain.Models.frame import Frame
from domain.Interfaces.camera_stream import ICameraStream

class OpenCVCameraStream(ICameraStream):
    """
    Implementación concreta de ICameraStream usando OpenCV.
    Lee frames desde una URL (RTSP/HTTP).
    """

    def __init__(self, url: str):
        self.url = url
        self.cap = None

    def connect(self) -> None:
        self.cap = cv2.VideoCapture(self.url)
        if not self.cap.isOpened():
            raise ConnectionError(f"❌ No se pudo abrir el stream: {self.url}")
        print(f"✅ Conectado al stream: {self.url}")

    def read_frame(self) -> Frame | None:
        if self.cap is None:
            return None
        ret, data = self.cap.read()
        if not ret:
            return None
        return Frame(data=data, timestamp=time.time(), source=self.url)

    def disconnect(self) -> None:
        if self.cap:
            self.cap.release()
            print("🔌 Stream cerrado.")

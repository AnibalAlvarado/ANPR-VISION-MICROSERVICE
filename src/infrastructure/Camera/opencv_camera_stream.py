import cv2
import time
import logging
from domain.Models.frame import Frame
from domain.Interfaces.camera_stream import ICameraStream

logger = logging.getLogger(__name__)

class OpenCVCameraStream(ICameraStream):
    """
    Implementación de ICameraStream usando OpenCV.
    Lee frames desde una URL (RTSP/HTTP).
    """

    def __init__(self, url: str, reconnect_attempts: int = 3, fps_limit: float = 0.0):
        """
        :param url: URL del stream (RTSP/HTTP/archivo).
        :param reconnect_attempts: Número de intentos de reconexión antes de fallar.
        :param fps_limit: Máx FPS (0 = ilimitado).
        """
        self.url = url
        self.cap = None
        self.reconnect_attempts = reconnect_attempts
        self.fps_limit = fps_limit
        self._last_frame_time = 0.0

    def connect(self) -> None:
        self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        if not self.cap.isOpened():
            raise ConnectionError(f" No se pudo abrir el stream: {self.url}")
        logger.info(f" Conectado al stream: {self.url}")

    def read_frame(self) -> Frame | None:
        if self.cap is None or not self.cap.isOpened():
            logger.warning(" Stream no está conectado. Intentando reconectar...")
            if not self._try_reconnect():
                return None

        # Control de FPS
        if self.fps_limit > 0:
            elapsed = time.time() - self._last_frame_time
            min_interval = 1.0 / self.fps_limit
            if elapsed < min_interval:
                return None

        ret, data = self.cap.read()
        if not ret:
            logger.error(" Error al leer frame. Intentando reconectar...")
            if not self._try_reconnect():
                return None
            return None

        self._last_frame_time = time.time()
        return Frame(data=data, timestamp=self._last_frame_time, source=self.url)

    def _try_reconnect(self) -> bool:
        """ Intenta reconectar al stream """
        for attempt in range(1, self.reconnect_attempts + 1):
            logger.info(f" Reintentando conexión ({attempt}/{self.reconnect_attempts})...")
            cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
            if cap.isOpened():
                self.cap = cap
                logger.info(" Reconexión exitosa.")
                return True
            time.sleep(1)
        logger.error("🚨 No se pudo reconectar al stream.")
        return False

    def disconnect(self) -> None:
        if self.cap:
            self.cap.release()
            self.cap = None
            logger.info("🔌 Stream cerrado.")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

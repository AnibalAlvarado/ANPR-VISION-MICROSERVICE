from src.core.config import settings
from src.domain.Interfaces.camera_stream import ICameraStream

def create_camera_stream() -> ICameraStream:
    if settings.camera_native == True:
        from src.infrastructure.Camera.Picamera2CameraStream import Picamera2CameraStream
        return Picamera2CameraStream()
    else:
        # Implementación para la RaspBerry PI
        from src.infrastructure.Camera.OpenCVCameraStream import OpenCVCameraStream
        url = settings.camera_url  
        return OpenCVCameraStream(url)

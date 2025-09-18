from src.core.config import settings
from src.domain.Interfaces.camera_stream import ICameraStream

def create_camera_stream() -> ICameraStream:
    if settings.camera_native == True:
        from src.infrastructure.Camera.picamera2_camera_stream import Picamera2CameraStream
        return Picamera2CameraStream()
    else:
        from src.infrastructure.Camera.opencv_camera_stream import OpenCVCameraStream
        url = settings.camera_url  
        return OpenCVCameraStream(url)

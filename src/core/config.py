from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "anpr-microservice"
    app_env: str = "development"
    app_port: int = 8000

    kafka_broker: str
    kafka_topic: str

    db_url: str
    redis_url: str

    model_path: str
    conf_threshold: float = 0.3
    iou_threshold: float = 0.45

    debug_show: bool = False
    loop_delay: float = 0.0

    dedup_ttl: float = 3.0
    similarity_threshold: float = 0.9

     # OCR
    ocr_lang: str = "en"
    ocr_interval: int = 5
    ocr_min_length: int = 4
    ocr_min_confidence: float = 0.8

    # Camera
    camera_url: str

     # Switch de detector
    yolo_version: str = "v8"   # v5 | v8

    # YOLOv5 (local y/o HF)
    yolov5_model_path: str = "./models/yolov5n-license-plate.pt"
    yolov5_conf: float = 0.25
    yolov5_iou: float = 0.45
    yolov5_img_size: int = 640
    yolov5_agnostic: bool = False
    yolov5_multi_label: bool = False
    yolov5_max_det: int = 1000
    yolov5_device: str = "auto"  # auto | cpu | cuda:0

    # Hugging Face (opcional, solo si no existe el .pt local)
    yolov5_hf_repo: str = "keremberke/yolov5n-license-plate"
    yolov5_hf_filename: str = "yolov5n-license-plate.pt"


    class Config:
        env_file = ".env"

settings = Settings()

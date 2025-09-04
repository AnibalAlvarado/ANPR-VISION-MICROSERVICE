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


    class Config:
        env_file = ".env"

settings = Settings()

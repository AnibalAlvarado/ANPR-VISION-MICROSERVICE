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

    class Config:
        env_file = ".env"

settings = Settings()

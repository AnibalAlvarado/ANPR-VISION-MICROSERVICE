import json
import logging
from confluent_kafka import Producer
from src.domain.Models.detection_result import DetectionResult
from src.domain.Interfaces.event_publisher import IEventPublisher
from src.core.config import settings

logger = logging.getLogger(__name__)

class KafkaPublisher(IEventPublisher):
    """
    Implementación de IEventPublisher que publica mensajes en un tópico Kafka.
    """

    def __init__(self):
        conf = {
            "bootstrap.servers": settings.kafka_broker,
            "client.id": settings.app_name,
        }
        self.producer = Producer(conf)
        self.topic = settings.kafka_topic

    def publish(self, result: DetectionResult) -> None:
        try:
            payload = json.dumps(result.to_dict(), ensure_ascii=False)
            self.producer.produce(
                topic=self.topic,
                key=result.frame_id,  # clave opcional para particionamiento
                value=payload,
                callback=self.delivery_report
            )
            self.producer.poll(0)  # procesa callbacks
            logger.info(f"📤 Evento publicado en Kafka: {payload}")
        except Exception as e:
            logger.error(f"❌ Error al publicar en Kafka: {e}")

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"❌ Error en entrega Kafka: {err}")
        else:
            logger.debug(
                f"✅ Mensaje entregado a {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}"
            )

# src/infrastructure/Messaging/kafka_publisher.py
import json
import logging
import threading
import time
from typing import Optional
from datetime import datetime
from confluent_kafka import Producer, KafkaError
from src.domain.Models.detection_result import DetectionResult
from src.domain.Interfaces.event_publisher import IEventPublisher
from src.core.config import settings

logger = logging.getLogger(__name__)

class KafkaPublisher(IEventPublisher):
    """
    Publica PlateDetectedEventRecord en Kafka a partir de DetectionResult.
    El micro descarta info que no necesita el backend (bounding box, track, confidence).
    """

    def __init__(self, delivery_timeout: float = 10.0, producer_conf: Optional[dict] = None):
        base_conf = {
            "bootstrap.servers": settings.kafka_broker,
            "client.id": settings.app_name,
            "enable.idempotence": True,   # anti-duplicados
            "acks": "all",
            "message.send.max.retries": 3,
            "socket.timeout.ms": 30000,
            "request.timeout.ms": 30000,
        }
        if producer_conf:
            base_conf.update(producer_conf)

        self.producer = Producer(base_conf)
        self.topic = settings.kafka_topic
        self.delivery_timeout = delivery_timeout

        self._wait_for_metadata(timeout=15)

    def _wait_for_metadata(self, timeout: int = 15) -> None:
        """Intenta obtener metadata del cluster antes de permitir produces."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                md = self.producer.list_topics(timeout=5.0)
                if md and md.brokers:
                    logger.info("Kafka producer metadata OK: brokers=%s", list(md.brokers.keys()))
                    return
            except Exception as ex:
                logger.debug("Esperando metadata kafka: %s", ex)
            time.sleep(1.0)
        logger.warning("No se obtuvo metadata del broker en %ds; intentos futuros pueden fallar.", timeout)

    def publish(self, result: DetectionResult) -> None:
        logger.debug("Publish llamado para event_id=%s frame=%s", getattr(result, "event_id", None), getattr(result, "frame_id", None))
        payload = None
        try:
            # ⚡ Adaptar DetectionResult → PlateDetectedEventRecord
            plate_text = result.plates[0].text if result.plates else ""
            timestamp_iso = datetime.utcfromtimestamp(result.captured_at).isoformat()

            event = {
                "plate": plate_text,
                "cameraId": result.camera_id or result.source,
                "parkingId": None,   # backend puede completar luego
                "timestamp": timestamp_iso,
                "frameId": result.frame_id,
                "imageUrl": None     # opcional: snapshot si se guarda
            }

            payload = json.dumps(event, ensure_ascii=False)
            delivered = {"err": None, "called": False}
            ev = threading.Event()

            def _cb(err, msg):
                delivered["called"] = True
                delivered["err"] = err
                ev.set()
                if err is not None:
                    logger.error("Kafka delivery callback error: %s", err)
                else:
                    logger.debug("Kafka delivered %s [%s] @ %s", msg.topic(), msg.partition(), msg.offset())

            key = str(result.frame_id or "")
            self.producer.produce(
                topic=self.topic,
                key=key,
                value=payload.encode("utf-8"),
                callback=_cb,
            )
            self.producer.poll(0)

            if not ev.wait(timeout=self.delivery_timeout):
                logger.warning("Timeout esperando confirmación de Kafka (timeout=%.1fs). Intentando flush.", self.delivery_timeout)
                try:
                    self.producer.flush(timeout=5.0)
                except Exception:
                    logger.exception("Error durante flush tras timeout")
                raise Exception("Kafka delivery timeout")

            if delivered["err"] is not None:
                err = delivered["err"]
                msg_err = err.str() if isinstance(err, KafkaError) and hasattr(err, "str") else str(err)
                raise Exception(f"Kafka delivery failed: {msg_err}")

            logger.info("Evento publicado en Kafka topic=%s frame=%s payload=%s", self.topic, key, payload)

        except Exception:
            logger.exception("Error al publicar en Kafka. payload: %s", payload)
            raise

    def close(self, timeout: float = 5.0) -> None:
        try:
            self.producer.flush(timeout=timeout)
            logger.info("Kafka producer flushed/closed")
        except Exception:
            logger.exception("Error al flush/close del Kafka producer")

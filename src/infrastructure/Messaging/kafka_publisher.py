# src/infrastructure/Messaging/kafka_publisher.py
import json
import logging
import threading
import time
from typing import Optional
from confluent_kafka import Producer, KafkaError
from src.domain.Models.detection_result import DetectionResult
from src.domain.Interfaces.event_publisher import IEventPublisher
from src.core.config import settings

logger = logging.getLogger(__name__)

class KafkaPublisher(IEventPublisher):
    """
    Publica DetectionResult en Kafka.
    Mejoras:
    - espera metadata al crear productor para que idempotence pueda inicializarse.
    - configura timeouts más holgados.
    - delivery_timeout configurable (por defecto aumenté a 10s).
    """

    def __init__(self, delivery_timeout: float = 10.0, producer_conf: Optional[dict] = None):
        base_conf = {
            "bootstrap.servers": settings.kafka_broker,
            "client.id": settings.app_name,
            # intentamos usar idempotencia (mejora anti-duplicados) — requiere que broker permita pid allocation
            "enable.idempotence": True,
            "acks": "all",
            # timeouts más altos para entornos variables
            "message.send.max.retries": 3,
            "socket.timeout.ms": 30000,
            "request.timeout.ms": 30000,
        }
        if producer_conf:
            base_conf.update(producer_conf)

        self.producer = Producer(base_conf)
        self.topic = settings.kafka_topic
        self.delivery_timeout = delivery_timeout

        # Esperar metadata para que el producer pueda inicializar apropiadamente (reduce errores GETPID)
        self._wait_for_metadata(timeout=15)

    def _wait_for_metadata(self, timeout: int = 15) -> None:
        """Intenta obtener metadata del cluster antes de permitir produces; mejora la estabilidad inicial."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                md = self.producer.list_topics(timeout=5.0)
                # si obtenemos metadata con brokers -> estamos bien
                if md and md.brokers:
                    logger.info("Kafka producer metadata OK: brokers=%s", list(md.brokers.keys()))
                    return
            except Exception as ex:
                logger.debug("Esperando metadata kafka: %s", ex)
            time.sleep(1.0)
        logger.warning("No se obtuvo metadata del broker en %ds; intentos futuros pueden fallar.", timeout)

    def publish(self, result: DetectionResult) -> None:
        logger.warning("DEBUG publish called for event_id=%s frame=%s", getattr(result, "event_id", None), getattr(result, "frame_id", None))
        payload = None
        try:
            data = result.to_dict() if hasattr(result, "to_dict") else result.__dict__
            payload = json.dumps(data, ensure_ascii=False)
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

            # aseguramos que la key sea string (consistente para particionamiento)
            key = str(getattr(result, "frame_id", "") or "")
            self.producer.produce(
                topic=self.topic,
                key=key,
                value=payload.encode("utf-8"),
                callback=_cb,
            )
            # procesar callbacks
            self.producer.poll(0)

            # esperar confirmación
            if not ev.wait(timeout=self.delivery_timeout):
                # timeout: en este estado NO sabemos si broker recibió o no el mensaje.
                # Si idempotence está activo y se inicializó correctamente, reintentos no generarán duplicados en la mayoría de casos.
                logger.warning("Timeout esperando confirmación de Kafka (timeout=%.1fs). Intentando flush.", self.delivery_timeout)
                try:
                    # flush con timeout corto para procesar callbacks pendientes
                    self.producer.flush(timeout=5.0)
                except Exception:
                    logger.exception("Error durante flush tras timeout")
                # lanzamos excepción para que el orquestador (RetryPublisher) decida reintentar
                raise Exception("Kafka delivery timeout")

            if delivered["err"] is not None:
                err = delivered["err"]
                msg_err = err.str() if isinstance(err, KafkaError) and hasattr(err, "str") else str(err)
                raise Exception(f"Kafka delivery failed: {msg_err}")

            logger.info("Evento publicado en Kafka topic=%s frame=%s", self.topic, key)

        except Exception:
            logger.exception("Error al publicar en Kafka. payload: %s", payload)
            raise

    def close(self, timeout: float = 5.0) -> None:
        try:
            self.producer.flush(timeout=timeout)
            logger.info("Kafka producer flushed/closed")
        except Exception:
            logger.exception("Error al flush/close del Kafka producer")

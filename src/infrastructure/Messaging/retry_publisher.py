# src/infrastructure/publishers/retry_publisher.py
import time
import logging
from typing import Any
from src.domain.Interfaces.event_publisher import IEventPublisher

logger = logging.getLogger(__name__)

class RetryPublisher(IEventPublisher):
    """
    Wrapper simple que intenta publish hasta N veces con backoff.
    Envuelve un publisher concreto (p.ej. ConsolePublisher o KafkaPublisher).
    """
    def __init__(self, inner: IEventPublisher, attempts: int = 3, base_delay: float = 0.2):
        self.inner = inner
        self.attempts = max(1, attempts)
        self.base_delay = base_delay

    def publish(self, payload: Any) -> None:
        last_exc = None
        for i in range(1, self.attempts + 1):
            try:
                self.inner.publish(payload)
                return
            except Exception as e:
                last_exc = e
                wait = self.base_delay * (2 ** (i - 1))
                logger.warning("Publish attempt %d failed, retrying in %.2fs: %s", i, wait, e)
                time.sleep(wait)
        # si fallaron todas
        logger.exception("All publish attempts failed")
        # Re-lanzar para que quien orquesta pueda decidir (opcional)
        raise last_exc

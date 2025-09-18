from abc import ABC, abstractmethod
from typing import List

from src.domain.Models.plate import Plate


class ITracker(ABC):
    """
    Contrato para cualquier algoritmo de tracking de placas.

    Un tracker asigna un ID persistente (`track_id`) a cada placa detectada
    a través de múltiples frames, de forma que podamos reconocer que es
    el mismo objeto aunque aparezca varias veces consecutivas.
    """

    @abstractmethod
    def update(self, plates: List[Plate]) -> List[Plate]:
        """
        Actualiza el estado del tracker con las nuevas detecciones.

        Parameters
        ----------
        plates : List[Plate]
            Lista de placas detectadas en el frame actual. Cada placa
            contiene al menos el bounding box y el texto OCR (si ya fue
            reconocido).

        Returns
        -------
        List[Plate]
            Lista de placas con `track_id` asignado.
        """
        pass

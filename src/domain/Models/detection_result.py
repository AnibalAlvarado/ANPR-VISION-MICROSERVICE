from dataclasses import dataclass
from typing import List
from domain.Models.plate import Plate

@dataclass
class DetectionResult:
    """
    Resultado de procesar un frame.
    """
    frame_id: str              # ID único del frame procesado
    plates: List[Plate]        # Lista de placas detectadas
    processed_at: float        # Timestamp cuando se terminó el procesamiento

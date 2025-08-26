from dataclasses import dataclass, asdict
from typing import List
from domain.Models.plate import Plate

@dataclass
class DetectionResult:
    """
    Resultado de procesar un frame completo.
    """
    frame_id: str
    plates: List[Plate]
    processed_at: float   # timestamp cuando se terminó de procesar
    source: str           # identificador de la cámara o URL
    captured_at: float    # timestamp original del frame

    def to_dict(self) -> dict:
        """Convierte a dict serializable."""
        return {
            "frame_id": self.frame_id,
            "plates": [p.to_dict() if hasattr(p, "to_dict") else p.__dict__ for p in self.plates],
            "processed_at": self.processed_at,
            "source": self.source,
            "captured_at": self.captured_at
        }

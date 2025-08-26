from dataclasses import dataclass
from typing import Any
import numpy as np

@dataclass
class Frame:
    """
    Representa un frame capturado desde una cámara.
    """
    data: np.ndarray   # imagen en formato numpy array
    timestamp: float   # momento en que se capturó
    source: str        # identificador de la cámara o URL
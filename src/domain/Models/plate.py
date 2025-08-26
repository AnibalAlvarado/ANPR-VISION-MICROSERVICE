from dataclasses import dataclass

@dataclass
class Plate:
    """
    Representa una placa detectada en una imagen.
    """
    text: str                  # Texto de la placa reconocida
    confidence: float          # Nivel de confianza del OCR
    bounding_box: tuple[int]   # (x1, y1, x2, y2) en coordenadas de la imagen

import re
from src.domain.Interfaces.text_normalizer import ITextNormalizer
from src.core.config import settings

class PlateNormalizer(ITextNormalizer):
    """
    Normaliza texto de placas:
    - Mayúsculas
    - Quitar espacios, guiones, barras, puntos, etc.
    - Aceptar solo A-Z0-9
    - Rechazar si contiene caracteres prohibidos o es muy corta
    """
    _ALNUM = re.compile(r"[^A-Z0-9]")

    def __init__(self, min_len: int | None = None):
        self.min_len = min_len or settings.plate_min_length

    def normalize(self, text: str) -> str:
        if not text:
            return ""

        t = text.strip().upper()
        # quitar separadores comunes
        for ch in (" ", "-", "_", ".", "/","\\"):
            t = t.replace(ch, "")

        # eliminar caracteres no permitidos
        t = self._ALNUM.sub("", t)

        # validar longitud mínima
        if len(t) < self.min_len:
            return ""

        return t

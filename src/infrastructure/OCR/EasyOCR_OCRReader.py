import easyocr
import time
from src.domain.Models.frame import Frame
from src.domain.Models.plate import Plate
from src.domain.Interfaces.ocr_reader import IOCRReader
from src.core.config import settings

class EasyOCR_OCRReader(IOCRReader):
    """
    Implementación optimizada usando EasyOCR:
    - OCR cada N frames
    - Cache de resultados recientes
    - Filtro de resultados inválidos
    """
    def __init__(self):
        self.reader = easyocr.Reader([settings.ocr_lang], gpu=True)  # usa GPU si está disponible
        self.ocr_interval = settings.ocr_interval
        self.min_length = settings.ocr_min_length
        self.frame_counter = 0
        self.cache = {}  # {bbox: (text, confidence, timestamp)}

    def read_text(self, frame: Frame, plate: Plate) -> Plate:
        self.frame_counter += 1

        bbox_key = tuple(plate.bounding_box)

        # Si ya está cacheado y no toca renovar → usar cache
        if bbox_key in self.cache:
            cached_text, cached_conf, ts = self.cache[bbox_key]
            if self.frame_counter % self.ocr_interval != 0:
                plate.text = cached_text
                plate.confidence = cached_conf
                return plate

        # Recortar la región de la placa
        x, y, w, h = plate.bounding_box
        crop = frame.image[y:y+h, x:x+w]

        # Ejecutar OCR
        results = self.reader.readtext(crop)

        if results:
            text, confidence = results[0][1], results[0][2]
            # Filtro: longitud mínima
            if len(text) >= self.min_length:
                plate.text = text.strip().upper()
                plate.confidence = confidence
                self.cache[bbox_key] = (plate.text, confidence, time.time())
            else:
                plate.text = ""
                plate.confidence = 0.0
        else:
            plate.text = ""
            plate.confidence = 0.0

        return plate

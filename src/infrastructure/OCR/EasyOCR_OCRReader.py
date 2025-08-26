import easyocr
from domain.Models.frame import Frame
from domain.Models.plate import Plate
from domain.Interfaces.ocr_reader import IOCRReader

class EasyOCR_OCRReader(IOCRReader):
    """
    Implementación real usando EasyOCR.
    """
    def __init__(self, lang: str = "en"):
        self.reader = easyocr.Reader([lang], gpu=True)  # usa GPU si está disponible

    def read_text(self, frame: Frame, plate: Plate) -> Plate:
        # Recortar la región de la placa
        x, y, w, h = plate.bounding_box
        crop = frame.image[y:y+h, x:x+w]

        # Detectar texto
        results = self.reader.readtext(crop)

        if results:
            # Tomar el más confiable
            text, confidence = results[0][1], results[0][2]
            plate.text = text
            plate.confidence = confidence
        else:
            plate.text = ""
            plate.confidence = 0.0

        return plate

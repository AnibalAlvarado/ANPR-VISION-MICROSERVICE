from typing import List

from src.domain.Interfaces.tracker import ITracker
from src.domain.Models.plate import Plate


class ByteTrackerAdapter(ITracker):
    """
    Adaptador de ByteTrack al contrato ITracker.

    Encapsula la librería de ByteTrack para asignar IDs persistentes
    a las placas detectadas en múltiples frames.
    """

    def __init__(self, track_thresh: float = 0.5, match_thresh: float = 0.8, buffer_size: int = 30):
        """
        Inicializa el tracker.

        Parameters
        ----------
        track_thresh : float
            Confianza mínima para mantener un track activo.
        match_thresh : float
            Umbral de similitud para asociar detecciones.
        buffer_size : int
            Número de frames a mantener en memoria.
        """
        # Aquí más adelante se inicializara el objeto real de ByteTrack
        self.track_thresh = track_thresh
        self.match_thresh = match_thresh
        self.buffer_size = buffer_size

    def update(self, plates: List[Plate]) -> List[Plate]:
        """
        Asigna un `track_id` a cada placa usando ByteTrack.

        De momento devuelve las placas tal cual, con track_id = None,
        como stub inicial.
        """
        # TODO: integrar ByteTrack real
        return plates

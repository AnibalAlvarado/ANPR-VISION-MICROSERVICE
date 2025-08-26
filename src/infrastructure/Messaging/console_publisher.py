from domain.Interfaces.event_publisher import IEventPublisher
from domain.Models.detection_result import DetectionResult

class ConsolePublisher(IEventPublisher):
    """
    Implementación dummy que solo imprime los resultados en consola.
    """

    def publish(self, result: DetectionResult) -> None:
        print("📢 Publicando resultado:")
        print(result)

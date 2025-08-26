import json
from domain.Interfaces.event_publisher import IEventPublisher
from domain.Models.detection_result import DetectionResult

class ConsolePublisher(IEventPublisher):
    """
    Implementación dummy que solo imprime los resultados en consola.
    """

    def publish(self, result: DetectionResult) -> None:
        try:
            # Convertir el objeto DetectionResult a dict (asumiendo que tiene .__dict__ o método to_dict())
            if hasattr(result, "to_dict"):
                output = result.to_dict()
            else:
                output = result.__dict__

            print("📢 Publicando resultado:")
            print(json.dumps(output, indent=2, ensure_ascii=False))

        except Exception as e:
            print(f"❌ Error al imprimir resultado en consola: {e}")

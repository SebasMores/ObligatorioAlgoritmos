from __future__ import annotations

from collections import deque


class Repartidor:
    """
    Representa un repartidor de la app.

    - id: identificador interno (ej: R-AB12CD)
    - nombre: nombre del repartidor (para mostrar en logs)
    - wa_id: número de WhatsApp con el que va a chatear
    """

    def __init__(self, id: str, nombre: str, wa_id: str):
        self.id = id
        self.nombre = nombre
        self.wa_id = wa_id

        self.estado = "disponible"

        self.distancia_recorrida = 0.0
        self.pedidos_entregados = 0

        self.tandas_pendientes = deque()

    def __repr__(self) -> str:
        return f"<Repartidor {self.id} {self.nombre} estado={self.estado}>"

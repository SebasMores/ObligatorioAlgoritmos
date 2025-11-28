from collections import deque


class Repartidor:
    def __init__(self, id, nombre, wa_id):
        self.id = id
        self.nombre = nombre
        self.wa_id = wa_id  # número de WhatsApp formateado
        self.estado = "disponible"  # disponible / repartiendo
        self.distancia_recorrida = 0.0
        self.pedidos_entregados = 0

        self.tanda_actual = None  # TandaPedidos o None
        self.tandas_pendientes = deque()
        self.pedido_actual = None  # Pedido o None

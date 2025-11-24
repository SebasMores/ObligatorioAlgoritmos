class Repartidor:
    def __init__(self, id, nombre):
        self.id = id
        self.nombre = nombre
        self.estado = "disponible"  # o "ocupado"
        self.distancia_recorrida = 0.0
        self.pedidos_entregados = 0

# models/tanda_pedidos.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .pedidos import Pedido
from .arbol_pedidos import NodoPedido, construir_bst_desde_pedidos, recorrer_in_order


@dataclass
class TandaPedidos:
    id: str
    zona: str  # o Zona
    pedidos: List[Pedido]
    ts_creada: datetime = field(default_factory=datetime.utcnow)
    repartidor_id: str | None = None
    bst_root: Optional[NodoPedido] = None

    def __post_init__(self) -> None:
        """
        Al crear la tanda, construimos el BST con los pedidos.
        """
        self.bst_root = construir_bst_desde_pedidos(self.pedidos)

    # Método de ayuda para obtener pedidos ordenados por distancia
    def pedidos_ordenados_por_distancia(self) -> List[Pedido]:
        """
        Devuelve los pedidos de la tanda ordenados por distancia
        usando el recorrido in-order del BST.
        """
        return recorrer_in_order(self.bst_root)

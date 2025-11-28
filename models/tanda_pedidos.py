from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .pedidos import Pedido
from .arbol_pedidos import NodoPedido  # 👈 ESTE


@dataclass
class TandaPedidos:
    id: str
    zona: str  # o Zona
    pedidos: List[Pedido]
    ts_creada: datetime = field(default_factory=datetime.utcnow)
    repartidor_id: str | None = None
    bst_root: Optional[NodoPedido] = None

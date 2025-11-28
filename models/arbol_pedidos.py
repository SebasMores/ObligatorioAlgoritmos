# models/arbol_pedidos.py
from __future__ import annotations  # recomendado
from dataclasses import dataclass
from typing import Optional
from .pedidos import Pedido


@dataclass
class NodoPedido:
    pedido: Pedido
    distancia: float
    left: Optional[NodoPedido] = None
    right: Optional[NodoPedido] = None

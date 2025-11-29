from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from .pedidos import Pedido


@dataclass
class NodoPedido:
    """
    Nodo de un árbol binario de búsqueda para pedidos.
    Usamos 'distancia' como clave numérica de orden.
    """

    pedido: Pedido
    distancia: float
    left: Optional["NodoPedido"] = None
    right: Optional["NodoPedido"] = None


def insertar_nodo(
    raiz: Optional[NodoPedido],
    pedido: Pedido,
    distancia: float,
) -> NodoPedido:
    if raiz is None:
        return NodoPedido(pedido=pedido, distancia=distancia)

    if distancia < raiz.distancia:
        raiz.left = insertar_nodo(raiz.left, pedido, distancia)
    else:
        raiz.right = insertar_nodo(raiz.right, pedido, distancia)

    return raiz


def construir_bst_desde_pedidos(pedidos: List[Pedido]) -> Optional[NodoPedido]:
    """
    Construye un BST a partir de una lista de pedidos.
    Usamos pedido.total como clave numérica para ordenar.
    """
    raiz: Optional[NodoPedido] = None

    for pedido in pedidos:
        distancia = float(pedido.total)
        raiz = insertar_nodo(raiz, pedido, distancia)

    return raiz


def recorrer_in_order(raiz: Optional[NodoPedido]) -> List[Pedido]:
    """
    Devuelve los pedidos ordenados según la 'distancia' del nodo
    (en este caso, el total del pedido).
    """
    resultado: List[Pedido] = []

    def _in_order(nodo: Optional[NodoPedido]) -> None:
        if nodo is None:
            return
        _in_order(nodo.left)
        resultado.append(nodo.pedido)
        _in_order(nodo.right)

    _in_order(raiz)
    return resultado

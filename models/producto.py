from dataclasses import dataclass
from typing import List


@dataclass
class Producto:
    id: str
    nombre: str
    precio: float
    categoria: str


PRODUCTOS: List[Producto] = [
    # ===== PIZZAS =====
    Producto("p1", "Pizza Muzarella", 450, "Pizzas"),
    Producto("p2", "Pizza Napolitana", 520, "Pizzas"),
    Producto("p3", "Pizza Fugazzeta", 500, "Pizzas"),
    Producto("p4", "Pizza Jamón y Queso", 580, "Pizzas"),
    Producto("p5", "Pizza Calabresa", 600, "Pizzas"),
    # ===== MINUTAS =====
    Producto("m1", "Milanesa al Plato", 480, "Minutas"),
    Producto("m2", "Milanesa Napolitana", 550, "Minutas"),
    Producto("m3", "Hamburguesa Completa", 420, "Minutas"),
    Producto("m4", "Chivito Uruguayo", 620, "Minutas"),
    Producto("m5", "Papas Fritas", 270, "Minutas"),
    # ===== BEBIDAS =====
    Producto("b1", "Coca Cola 600ml", 150, "Bebidas"),
    Producto("b2", "Fanta 600ml", 150, "Bebidas"),
    Producto("b3", "Agua Mineral 500ml", 120, "Bebidas"),
    Producto("b4", "Cerveza Pilsen", 220, "Bebidas"),
    Producto("b5", "Jugo Natural", 180, "Bebidas"),
    # ===== POSTRES =====
    Producto("po1", "Flan Casero", 200, "Postres"),
    Producto("po2", "Tiramisú", 280, "Postres"),
    Producto("po3", "Helado 2 bochas", 230, "Postres"),
    Producto("po4", "Brownie con helado", 320, "Postres"),
    Producto("po5", "Panqueque de dulce de leche", 260, "Postres"),
    # ===== ENSALADAS =====
    Producto("e1", "Ensalada César", 390, "Ensaladas"),
    Producto("e2", "Ensalada Mixta", 300, "Ensaladas"),
    Producto("e3", "Ensalada Caprese", 350, "Ensaladas"),
    # ===== EXTRAS =====
    Producto("x1", "Empanada de carne", 90, "Extras"),
    Producto("x2", "Empanada de jamón y queso", 90, "Extras"),
]


def obtener_categorias() -> List[str]:
    """Devuelve lista única de categorías disponibles"""
    categorias = sorted({p.categoria for p in PRODUCTOS})
    return ["Todos"] + categorias


def get_producto_por_id(producto_id: str) -> Producto | None:
    for p in PRODUCTOS:
        if p.id == producto_id:
            return p
    return None

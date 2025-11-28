# models/pedidos.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict


@dataclass
class Pedido:
    id: str
    wa_id_cliente: str  # número de WhatsApp del cliente
    items: List[Dict]  # lo que hoy guardás en "carrito"
    total: float
    lat: float
    lon: float
    zona: str  # "NO", "NE", "SO", "SE"
    codigo_confirmacion: str
    estado: str = "pendiente"  # pendiente / en_reparto / entregado / cancelado
    ts_confirmado: datetime = field(default_factory=datetime.utcnow)

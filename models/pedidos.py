from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict


@dataclass
class Pedido:
    id: str
    wa_id_cliente: str
    items: List[Dict]
    total: float
    lat: float
    lon: float
    zona: str
    codigo_confirmacion: str
    estado: str = "pendiente"
    ts_confirmado: datetime = field(default_factory=datetime.utcnow)

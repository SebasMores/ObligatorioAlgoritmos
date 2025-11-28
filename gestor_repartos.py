# gestor_repartos.py

from __future__ import annotations

from collections import deque
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional

import uuid
import random
import string

from models.pedidos import Pedido
from models.zona import Zona
from models.tanda_pedidos import TandaPedidos

# Más adelante usaremos NodoPedido para el BST
# from models.arbol_pedidos import NodoPedido

# Coordenadas del restaurante (las podés ajustar si querés)
# Usamos algo similar al "centro" que ya tenés en chat.py
RESTAURANTE_LAT = -31.3833
RESTAURANTE_LON = -57.9667


class GestorRepartos:
    """
    Gestor central de la Opción 3:

    - Registra pedidos confirmados.
    - Los clasifica en zonas (NO / NE / SO / SE).
    - Mantiene una cola de pedidos por zona.

    Ahora además:
    - Forma tandas de pedidos por zona (7 pedidos o 45 minutos).
    - Guarda una cola de tandas sin repartidor asignado.
    """

    def __init__(self) -> None:
        # Todos los pedidos por id
        self.pedidos: Dict[str, Pedido] = {}

        # Una cola de pedidos por zona
        self.cola_por_zona: Dict[Zona, Deque[Pedido]] = {
            Zona.NO: deque(),
            Zona.NE: deque(),
            Zona.SO: deque(),
            Zona.SE: deque(),
        }

        # Tandas creadas por id
        self.tandas: Dict[str, TandaPedidos] = {}

        # Cola de tandas aún sin repartidor asignado
        self.cola_tandas_sin_repartidor: Deque[TandaPedidos] = deque()

    # ==========================================================
    #  CÁLCULO DE ZONA
    # ==========================================================
    def calcular_zona(self, lat: float, lon: float) -> Zona:
        """
        Clasifica un punto (lat, lon) en una de las 4 zonas:
        - Norte / Sur relativo al restaurante (lat).
        - Este / Oeste relativo al restaurante (lon).

        En Uruguay las latitudes son negativas:
        - Más "al norte" = valor de latitud más alto (menos negativo).
          Ej: -31.37 > -31.39  → -31.37 está más al norte.

        Longitud (también negativa):
        - Más "al este" = valor de longitud más alto (menos negativo).
          Ej: -57.95 > -57.99 → -57.95 está más al este.
        """

        # Norte vs Sur
        es_norte = lat > RESTAURANTE_LAT
        # Este vs Oeste
        es_este = lon > RESTAURANTE_LON

        if es_norte and not es_este:
            return Zona.NO  # Norte - Oeste
        elif es_norte and es_este:
            return Zona.NE  # Norte - Este
        elif not es_norte and not es_este:
            return Zona.SO  # Sur - Oeste
        else:
            return Zona.SE  # Sur - Este

    # ==========================================================
    #  REGISTRO DE PEDIDOS
    # ==========================================================
    def registrar_pedido(self, pedido: Pedido) -> None:
        """
        Recibe un Pedido ya armado, calcula (o corrige) la zona
        y lo encola en la cola correspondiente. Luego verifica
        si corresponde formar una tanda en esa zona.
        """
        zona = self.calcular_zona(pedido.lat, pedido.lon)
        pedido.zona = zona.value  # guardamos como string "NO", "NE", etc.

        # Guardar en diccionario general
        self.pedidos[pedido.id] = pedido

        # Encolar en la cola de su zona
        self.cola_por_zona[zona].append(pedido)

        print(
            f"[GESTOR] Pedido {pedido.id} registrado en zona {zona.value}. "
            f"Total cola zona {zona.value}: {len(self.cola_por_zona[zona])}"
        )

        # Después de encolar, revisamos si hay que formar una tanda
        self._chequear_formar_tanda(zona)

    # ==========================================================
    #  FORMACIÓN DE TANDAS POR ZONA
    # ==========================================================
    def _generar_id_pedido(self) -> str:
        """
        Genera un id corto tipo 'P-3FA9B2C1'
        """
        return "P-" + uuid.uuid4().hex[:8].upper()

    def _generar_id_tanda(self) -> str:
        """
        Genera un id corto tipo 'T-ABC123'
        """
        return "T-" + uuid.uuid4().hex[:6].upper()

    def _generar_codigo_confirmacion(self, length: int = 6) -> str:
        """
        Genera un código random alfanumérico de 6 caracteres,
        como pide la letra del obligatorio.
        """
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choices(chars, k=length))

    def _chequear_formar_tanda(self, zona: Zona) -> None:
        """
        Revisa la cola de la zona indicada y, si se cumple alguna condición,
        forma una TandaPedidos:

        - Si la cola tiene 7 o más pedidos → toma hasta 7 y arma una tanda.
        - Si el primer pedido lleva >= 45 minutos esperando → arma la tanda
          con los pedidos que haya (hasta 7).
        """
        cola = self.cola_por_zona[zona]
        if not cola:
            return

        ahora = datetime.utcnow()
        formar = False

        # Regla 1: hay 7 o más pedidos
        if len(cola) >= 7:
            formar = True
        else:
            # Regla 2: el primero lleva >= 45 minutos
            primero = cola[0]
            if ahora - primero.ts_confirmado >= timedelta(minutes=45):
                formar = True

        if not formar:
            return

        # Sacamos hasta 7 pedidos de la cola para formar la tanda
        pedidos_tanda: List[Pedido] = []
        while cola and len(pedidos_tanda) < 7:
            pedidos_tanda.append(cola.popleft())

        tanda_id = self._generar_id_tanda()
        tanda = TandaPedidos(
            id=tanda_id,
            zona=zona.value,
            pedidos=pedidos_tanda,
        )

        # Guardamos la tanda
        self.tandas[tanda_id] = tanda
        # Por ahora, todas las tandas van a la cola "sin repartidor"
        self.cola_tandas_sin_repartidor.append(tanda)

        print(
            f"[GESTOR] Tanda {tanda_id} creada en zona {zona.value} "
            f"con {len(pedidos_tanda)} pedidos. "
            f"Tandas en espera: {len(self.cola_tandas_sin_repartidor)}"
        )

    # ==========================================================
    #  HELPERS PARA CREAR PEDIDO DESDE EL CARRITO
    # ==========================================================
    def crear_y_registrar_pedido_desde_carrito(
        self,
        wa_id_cliente: str,
        carrito: List[Dict],
        lat: float,
        lon: float,
    ) -> Pedido:
        """
        Convierte el carrito actual de un cliente en un Pedido,
        lo registra en el sistema y lo encola por zona.

        Devuelve el Pedido para que el bot pueda:
        - mostrar el resumen
        - enviar el código de confirmación al cliente
        """
        total = sum(item["cantidad"] * item["precio_unitario"] for item in carrito)
        zona = self.calcular_zona(lat, lon)
        pedido_id = self._generar_id_pedido()
        codigo = self._generar_codigo_confirmacion()

        pedido = Pedido(
            id=pedido_id,
            wa_id_cliente=wa_id_cliente,
            items=carrito,
            total=total,
            lat=lat,
            lon=lon,
            zona=zona.value,
            codigo_confirmacion=codigo,
        )

        self.registrar_pedido(pedido)
        print(f"[GESTOR] Pedido creado: {asdict(pedido)}")

        return pedido


# Instancia global para usar desde chat.py / main.py
gestor_repartos = GestorRepartos()

# gestor_repartos.py

from __future__ import annotations

from collections import deque
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Deque, Dict, List

import uuid
import random
import string

from models.pedidos import Pedido
from models.zona import Zona
from models.tanda_pedidos import TandaPedidos
from models.repartidor import Repartidor

# Coordenadas del restaurante (las podés ajustar si querés)
RESTAURANTE_LAT = -31.3833
RESTAURANTE_LON = -57.9667


class GestorRepartos:
    """
    Gestor central de la Opción 3:

    - Registra pedidos confirmados.
    - Los clasifica en zonas (NO / NE / SO / SE).
    - Mantiene una cola de pedidos por zona.
    - Forma tandas (7 pedidos o 45 min).
    - Mantiene una cola de tandas sin repartidor.
    - Registra repartidores y les asigna tandas.
    """

    def __init__(self) -> None:
        # ----------------- PEDIDOS -----------------
        # Todos los pedidos por id
        self.pedidos: Dict[str, Pedido] = {}

        # Una cola de pedidos por zona
        self.cola_por_zona: Dict[Zona, Deque[Pedido]] = {
            Zona.NO: deque(),
            Zona.NE: deque(),
            Zona.SO: deque(),
            Zona.SE: deque(),
        }

        # ----------------- TANDAS ------------------
        # Tandas creadas por id
        self.tandas: Dict[str, TandaPedidos] = {}

        # Cola de tandas aún sin repartidor asignado
        self.cola_tandas_sin_repartidor: Deque[TandaPedidos] = deque()

        # ----------------- REPARTIDORES -----------
        # Repartidores por id interno
        self.repartidores_por_id: Dict[str, Repartidor] = {}
        # Repartidores por número de WhatsApp (wa_id)
        self.repartidores_por_wa: Dict[str, Repartidor] = {}

    # ==========================================================
    #  CÁLCULO DE ZONA
    # ==========================================================
    def calcular_zona(self, lat: float, lon: float) -> Zona:
        """
        Clasifica un punto (lat, lon) en una de las 4 zonas.
        Latitudes y longitudes negativas (Uruguay).
        """
        es_norte = lat > RESTAURANTE_LAT  # más al norte = menos negativo
        es_este = lon > RESTAURANTE_LON  # más al este  = menos negativo

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
        pedido.zona = zona.value  # "NO", "NE", etc.

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
        return "P-" + uuid.uuid4().hex[:8].upper()

    def _generar_id_tanda(self) -> str:
        return "T-" + uuid.uuid4().hex[:6].upper()

    def _generar_id_repartidor(self) -> str:
        return "R-" + uuid.uuid4().hex[:6].upper()

    def _generar_codigo_confirmacion(self, length: int = 6) -> str:
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
        if len(cola) >= 2:
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

        zona_str = zona.value
        tanda_id = self._generar_id_tanda()
        tanda = TandaPedidos(
            id=tanda_id,
            zona=zona_str,
            pedidos=pedidos_tanda,
        )

        # Guardamos la tanda
        self.tandas[tanda_id] = tanda
        # Por ahora, todas las tandas van a la cola "sin repartidor"
        self.cola_tandas_sin_repartidor.append(tanda)

        print(
            f"[GESTOR] Tanda {tanda_id} creada en zona {zona_str} "
            f"con {len(pedidos_tanda)} pedidos. "
            f"Tandas en espera: {len(self.cola_tandas_sin_repartidor)}"
        )

        # Por si ya hay repartidores disponibles, intentamos asignar
        self._asignar_tanda_a_repartidor_disponible()

    # ==========================================================
    #  REPARTIDORES
    # ==========================================================
    def registrar_repartidor(self, nombre: str, wa_id: str) -> Repartidor:
        """
        Crea un nuevo repartidor y lo deja en estado 'disponible'.
        Si hay tandas en espera, intenta asignarle una.
        """
        # Si ya existe por wa_id, lo devolvemos
        if wa_id in self.repartidores_por_wa:
            rep = self.repartidores_por_wa[wa_id]
            print(f"[GESTOR] Repartidor ya existente: {rep}")
            return rep

        rep_id = self._generar_id_repartidor()
        repartidor = Repartidor(id=rep_id, nombre=nombre, wa_id=wa_id)

        self.repartidores_por_id[rep_id] = repartidor
        self.repartidores_por_wa[wa_id] = repartidor

        print(f"[GESTOR] Repartidor registrado: {repartidor}")

        # Intentamos asignarle una tanda si hay en espera
        self._asignar_tanda_a_repartidor_disponible(repartidor_especifico=repartidor)

        return repartidor

    def obtener_repartidor_por_wa(self, wa_id: str) -> Repartidor | None:
        return self.repartidores_por_wa.get(wa_id)

    def _asignar_tanda_a_repartidor_disponible(
        self,
        repartidor_especifico: Repartidor | None = None,
    ) -> None:
        """
        Si hay tandas en espera y repartidores disponibles, les asigna
        la primera tanda de la cola.

        - Si 'repartidor_especifico' viene, intenta primero con ese.
        - Si no, recorre todos los repartidores buscando uno disponible.
        """
        if not self.cola_tandas_sin_repartidor:
            return

        candidatos: List[Repartidor] = []
        if repartidor_especifico is not None:
            candidatos.append(repartidor_especifico)
        else:
            candidatos = [
                r for r in self.repartidores_por_id.values() if r.estado == "disponible"
            ]

        if not candidatos:
            return

        for repartidor in candidatos:
            if not self.cola_tandas_sin_repartidor:
                break

            if repartidor.estado != "disponible":
                continue

            tanda = self.cola_tandas_sin_repartidor.popleft()
            repartidor.tanda_actual = tanda
            repartidor.estado = "repartiendo"
            tanda.repartidor_id = repartidor.id

            print(
                f"[GESTOR] Tanda {tanda.id} asignada a repartidor {repartidor.id} "
                f"({repartidor.nombre})."
            )

            # Más adelante, acá será el lugar para:
            # - construir el BST de la tanda
            # - enviar el primer pedido al repartidor por WhatsApp
            # - etc.

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

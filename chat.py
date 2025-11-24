from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# Estados de la conversación
STATE_IDLE = "IDLE"
STATE_MAIN_MENU = "MAIN_MENU"
STATE_RUTA = "RUTA"

WAITING_NONE = None
WAITING_RUTA_ORIGEN = "RUTA_ORIGEN"
WAITING_RUTA_DESTINO = "RUTA_DESTINO"
WAITING_RUTA_ALGORITMO = "RUTA_ALGORITMO"


@dataclass
class ChatSession:
    """
    Representa el estado de conversación de un usuario.
    """

    state: str = STATE_IDLE
    waiting_for: Optional[str] = WAITING_NONE
    data: Dict[str, Any] = field(default_factory=dict)


class ChatBot:
    """
    Núcleo de la lógica conversacional del bot.
    """

    def __init__(self) -> None:
        self.sessions: Dict[str, ChatSession] = {}

    # --------- Gestión de sesiones ---------

    def _get_session(self, user_id: str) -> ChatSession:
        if user_id not in self.sessions:
            self.sessions[user_id] = ChatSession()
        return self.sessions[user_id]

    # --------- API pública ---------

    def handle_message(self, user_id: str, text: str) -> List[str]:
        session = self._get_session(user_id)
        text = text or ""
        raw = text.strip()
        lower = raw.lower()

        if not raw:
            return ["No recibí ningún mensaje de texto. Probá de nuevo."]

        # Comandos globales
        if lower in (
            "/start",
            "hola",
            "buenas",
            "buenos dias",
            "buen día",
            "buenas tardes",
            "buenas noches",
        ):
            session.state = STATE_IDLE
            session.waiting_for = WAITING_NONE
            session.data.clear()
            return [
                "👋 ¡Hola! Soy el bot del obligatorio de Algoritmos y Estructuras de Datos.",
                "Usá el comando */ayuda* para ver las opciones disponibles.",
            ]

        if lower == "/reset":
            session.state = STATE_IDLE
            session.waiting_for = WAITING_NONE
            session.data.clear()
            return [
                "🔄 Conversación reiniciada.",
                "Mandá /ayuda para ver el menú de opciones.",
            ]

        if lower == "/ayuda":
            return self._handle_ayuda(session)

        # Si no está en ningún flujo, redirigimos a /ayuda
        if session.state == STATE_IDLE:
            return [
                "No entendí el mensaje 🤔",
                "Mandá */ayuda* para ver las opciones disponibles.",
            ]

        # Enrutado según estado actual
        if session.state == STATE_MAIN_MENU:
            return self._handle_main_menu(session, lower)

        if session.state == STATE_RUTA:
            return self._handle_opcion_ruta(session, raw, lower)

        # Fallback
        session.state = STATE_IDLE
        session.waiting_for = WAITING_NONE
        session.data.clear()
        return [
            "Se produjo un pequeño error en la conversación 😅",
            "Mandá /ayuda para empezar de nuevo.",
        ]

    # --------- Handlers internos ---------

    def _handle_ayuda(self, session: ChatSession) -> List[str]:
        """
        Muestra el menú principal y prepara el estado MAIN_MENU.
        """
        session.state = STATE_MAIN_MENU
        session.waiting_for = WAITING_NONE
        session.data.clear()

        return [
            "📋 *Menú de opciones*",
            "",
            "1️⃣ Calcular ruta de delivery (Dijkstra / A*).",
            "2️⃣ [Opción 2 del obligatorio].",
            "3️⃣ [Opción 3 del obligatorio].",
            "",
            "Respondé con el *número* de la opción (por ejemplo: 1).",
        ]

    def _handle_main_menu(self, session: ChatSession, lower: str) -> List[str]:
        """
        Maneja la selección de opciones del menú principal.
        """
        if lower == "1":
            session.state = STATE_RUTA
            session.waiting_for = WAITING_RUTA_ORIGEN
            session.data.clear()

            return [
                "🛵 Vamos a calcular la *ruta de delivery*.",
                "Escribí el *origen* (ejemplo: plaza artigas, terminal, hospital, centro, shopping).",
            ]

        if lower == "2":
            return [
                "La *Opción 2* todavía no está implementada.",
                "Por ahora, solo está funcionando la opción 1.",
            ]

        if lower == "3":
            return [
                "La *Opción 3* todavía no está implementada.",
                "Por ahora, solo está funcionando la opción 1.",
            ]

        return [
            "No entendí la opción seleccionada 😅",
            "Respondé *1, 2 o 3*, o mandá /ayuda para ver el menú de nuevo.",
        ]

    # ================= OPCIÓN 1: RUTA =================

    def _handle_opcion_ruta(
        self, session: ChatSession, raw: str, lower: str
    ) -> List[str]:
        """
        Flujo de la opción 1: cálculo de ruta con Dijkstra / A*.
        1) Pedir origen (como nombre)
        2) Pedir destino (como nombre)
        3) Preguntar algoritmo
        4) Convertir origen/destino a nodos del grafo y ejecutar
        """

        # Mapeo de nombres de lugares (texto) a coordenadas (lat, lon)
        lugares: Dict[str, tuple[float, float]] = {
            "centro": (-31.3833, -57.9667),
            "plaza artigas": (-31.3825, -57.9658),
            "hospital": (-31.3891, -57.9554),
            "hospital regional": (-31.3891, -57.9554),
            "terminal": (-31.3878, -57.9640),
            "terminal de omnibus": (-31.3878, -57.9640),
            "costanera sur": (-31.3795, -57.9525),
            "shopping": (-31.3715, -57.9580),
            "shopping salto": (-31.3715, -57.9580),
        }

        # ---------- Paso 1: ORIGEN ----------
        if session.waiting_for == WAITING_RUTA_ORIGEN:
            origen_nombre = lower.strip()

            if origen_nombre not in lugares:
                return [
                    "⚠️ No reconocí ese origen.",
                    "Probá con: plaza artigas, terminal, hospital, centro, shopping, costanera sur.",
                ]

            session.data["origen_nombre"] = origen_nombre
            session.waiting_for = WAITING_RUTA_DESTINO

            return [
                f"✅ Origen registrado: *{origen_nombre}*.",
                "Ahora escribí el *destino* (mismos lugares posibles).",
            ]

        # ---------- Paso 2: DESTINO ----------
        if session.waiting_for == WAITING_RUTA_DESTINO:
            destino_nombre = lower.strip()
            origen_nombre = session.data.get("origen_nombre")

            if destino_nombre not in lugares:
                return [
                    "⚠️ No reconocí ese destino.",
                    "Probá con: plaza artigas, terminal, hospital, centro, shopping, costanera sur.",
                ]

            if destino_nombre == origen_nombre:
                return [
                    "⚠️ El origen y el destino no pueden ser iguales.",
                    "Ingresá un destino distinto, por favor.",
                ]

            session.data["destino_nombre"] = destino_nombre
            session.waiting_for = WAITING_RUTA_ALGORITMO

            return [
                f"✅ Destino registrado: *{destino_nombre}*.",
                "",
                "¿Qué algoritmo querés usar para calcular la ruta?",
                "1️⃣ Dijkstra",
                "2️⃣ A* (A estrella)",
                "",
                "Respondé *1* o *2*.",
            ]

        # ---------- Paso 3: ELECCIÓN DE ALGORITMO ----------
        if session.waiting_for == WAITING_RUTA_ALGORITMO:
            origen_nombre = session.data.get("origen_nombre")
            destino_nombre = session.data.get("destino_nombre")

            if not origen_nombre or not destino_nombre:
                session.state = STATE_MAIN_MENU
                session.waiting_for = WAITING_NONE
                session.data.clear()
                return [
                    "Se perdió el origen o el destino en la conversación 😕.",
                    "Mandá /ayuda y volvé a elegir la opción 1.",
                ]

            # Elegir algoritmo
            if lower == "1":
                algoritmo = "Dijkstra"
                usar_dijkstra = True
            elif lower == "2":
                algoritmo = "A*"
                usar_dijkstra = False
            else:
                return [
                    "No entendí el algoritmo 😅.",
                    "Respondé *1* para Dijkstra o *2* para A*.",
                ]

            # --- Acá recién importamos cosas pesadas ---
            try:
                from coordenadas_gifs import (
                    dijkstra_gif,
                    a_star_gif,
                    reconstruct_path_gif,
                    create_gif,
                    G,
                )
                import osmnx as ox
            except Exception as e:
                session.state = STATE_MAIN_MENU
                session.waiting_for = WAITING_NONE
                session.data.clear()
                return [
                    "❌ Error interno al cargar el módulo de rutas.",
                    f"Detalle técnico: {e}",
                    "Avisale al profe que revise las dependencias (osmnx, networkx, etc.).",
                ]

            # Convertir nombres a coordenadas
            orig_coord = lugares[origen_nombre]  # (lat, lon)
            dest_coord = lugares[destino_nombre]  # (lat, lon)

            # Convertir coordenadas a nodos del grafo
            try:
                origen_nodo = ox.distance.nearest_nodes(
                    G, orig_coord[1], orig_coord[0]
                )  # (lon, lat)
                destino_nodo = ox.distance.nearest_nodes(
                    G, dest_coord[1], dest_coord[0]
                )
            except Exception as e:
                session.state = STATE_MAIN_MENU
                session.waiting_for = WAITING_NONE
                session.data.clear()
                return [
                    "❌ Error al buscar nodos en el mapa de Salto.",
                    f"Detalle técnico: {e}",
                ]

            # Ejecutar algoritmo correspondiente
            try:
                if usar_dijkstra:
                    dijkstra_gif(origen_nodo, destino_nodo)
                    ok = reconstruct_path_gif(origen_nodo, destino_nodo, "Dijkstra")
                    gif = create_gif("Dijkstra")
                else:
                    a_star_gif(origen_nodo, destino_nodo)
                    ok = reconstruct_path_gif(origen_nodo, destino_nodo, "A_Star")
                    gif = create_gif("A_Star")

                if not ok:
                    mensaje = [
                        f"⚠️ No se pudo reconstruir el camino con {algoritmo}.",
                        "Revisá si el grafo tiene conexión entre esos puntos.",
                    ]
                else:
                    mensaje = [
                        f"✅ Ruta calculada con *{algoritmo}* correctamente.",
                        f"📁 Se generó un GIF del recorrido: `{gif}` (en el servidor).",
                        "Representa el camino óptimo entre los puntos seleccionados.",
                    ]

            except Exception as e:
                mensaje = [
                    f"❌ Ocurrió un error al ejecutar {algoritmo}.",
                    f"Detalle técnico: {e}",
                ]

            # Reset de estado
            session.state = STATE_MAIN_MENU
            session.waiting_for = WAITING_NONE
            session.data.clear()

            mensaje.append("")
            mensaje.append("Si querés hacer otra consulta, mandá */ayuda*.")

            return mensaje

        # ---------- Fallback ----------
        session.state = STATE_MAIN_MENU
        session.waiting_for = WAITING_NONE
        session.data.clear()
        return [
            "Se perdió el flujo de la ruta 😅.",
            "Mandá /ayuda y elegí la opción 1 para reintentar.",
        ]


# Instancia global para que main.py pueda hacer: from chat import bot
bot = ChatBot()

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# ================= ESTADOS =================

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
    def __init__(self) -> None:
        self.sessions: Dict[str, ChatSession] = {}

    # -------- Sesiones --------

    def _get_session(self, user_id: str) -> ChatSession:
        if user_id not in self.sessions:
            self.sessions[user_id] = ChatSession()
        return self.sessions[user_id]

    # -------- API principal --------

    def handle_message(self, user_id: str, text: str) -> List[str]:
        session = self._get_session(user_id)
        raw = text.strip()
        lower = raw.lower()

        if not raw:
            return ["No recibí ningún mensaje."]

        if lower in ("/start", "hola", "buenas"):
            session.state = STATE_IDLE
            session.waiting_for = WAITING_NONE
            session.data.clear()
            return [
                "👋 Hola, soy el bot del obligatorio.",
                "Usá /ayuda para ver las opciones.",
            ]

        if lower == "/reset":
            session.state = STATE_IDLE
            session.waiting_for = WAITING_NONE
            session.data.clear()
            return ["🔄 Conversación reiniciada. Usá /ayuda."]

        if lower == "/ayuda":
            return self._handle_ayuda(session)

        if session.state == STATE_IDLE:
            return ["Mandá /ayuda para ver el menú."]

        if session.state == STATE_MAIN_MENU:
            return self._handle_main_menu(session, lower)

        if session.state == STATE_RUTA:
            return self._handle_opcion_ruta(session, raw, lower)

        session.state = STATE_IDLE
        session.waiting_for = WAITING_NONE
        session.data.clear()
        return ["Error inesperado 😅 Usá /ayuda."]

    # -------- MENÚ --------

    def _handle_ayuda(self, session: ChatSession) -> List[str]:
        session.state = STATE_MAIN_MENU
        session.waiting_for = WAITING_NONE
        session.data.clear()

        return [
            "📋 MENÚ",
            "1️⃣ Calcular ruta",
            "2️⃣ Otra opción",
            "3️⃣ Otra opción",
            "Respondé 1, 2 o 3",
        ]

    def _handle_main_menu(self, session: ChatSession, lower: str) -> List[str]:
        if lower == "1":
            session.state = STATE_RUTA
            session.waiting_for = WAITING_RUTA_ORIGEN
            session.data.clear()
            return ["🛵 Cálculo de ruta", "Ingresá el ORIGEN:"]

        return ["Opción inválida. Mandá /ayuda."]

    # ================= OPCIÓN 1 =================

    def _handle_opcion_ruta(
        self, session: ChatSession, raw: str, lower: str
    ) -> List[str]:
        from coordenadas_gifs import (
            dijkstra_gif,
            a_star_gif,
            reconstruct_path_gif,
            create_gif,
        )

        # ----- ORIGEN -----
        if session.waiting_for == WAITING_RUTA_ORIGEN:
            session.data["origen"] = lower
            session.waiting_for = WAITING_RUTA_DESTINO
            return [f"Origen: {lower} ✅", "Ahora ingresá el DESTINO:"]

        # ----- DESTINO -----
        if session.waiting_for == WAITING_RUTA_DESTINO:
            session.data["destino"] = lower
            session.waiting_for = WAITING_RUTA_ALGORITMO
            return [f"Destino: {lower} ✅", "Elegí algoritmo:", "1️⃣ Dijkstra", "2️⃣ A*"]

        # ----- ALGORITMO -----
        if session.waiting_for == WAITING_RUTA_ALGORITMO:
            origen = session.data["origen"]
            destino = session.data["destino"]

            if lower == "1":
                algoritmo = "Dijkstra"
                dijkstra_gif(origen, destino)
                reconstruct_path_gif(origen, destino, "Dijkstra")
                gif = create_gif("Dijkstra")

            elif lower == "2":
                algoritmo = "A*"
                a_star_gif(origen, destino)
                reconstruct_path_gif(origen, destino, "A*")
                gif = create_gif("A_Star")

            else:
                return ["Usá 1 o 2"]

            session.state = STATE_MAIN_MENU
            session.waiting_for = WAITING_NONE
            session.data.clear()

            return [
                f"✅ Ruta calculada con {algoritmo}",
                f"📁 GIF generado: {gif}",
                "Usá /ayuda para continuar",
            ]

        return ["Error de flujo. Usá /ayuda."]


# ===== INSTANCIA GLOBAL =====

bot = ChatBot()

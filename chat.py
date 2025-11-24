from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# --- Estados de la conversación ---

STATE_IDLE = "IDLE"
STATE_MAIN_MENU = "MAIN_MENU"
STATE_RUTA = "RUTA"  # Opción 1: calcular ruta

WAITING_NONE = None
WAITING_RUTA_ORIGEN = "RUTA_ORIGEN"
WAITING_RUTA_DESTINO = "RUTA_DESTINO"


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
    - Maneja sesiones por usuario (user_id).
    - Expone un método público handle_message(user_id, text)
      que devuelve una lista de strings (respuestas).
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
        """
        Procesa un mensaje de texto entrante y devuelve una lista de textos de respuesta.
        main.py debería:
          - Llamar a bot.handle_message(wa_id, text)
          - Enviar cada string usando whatsapp_client.send_text_message(...)
        """
        session = self._get_session(user_id)
        text = text or ""
        raw = text.strip()
        lower = raw.lower()

        # Normalización básica de espacios
        if not raw:
            return ["No recibí ningún mensaje de texto. Probá de nuevo."]

        # --- Comandos globales ---
        if lower in ("/start", "hola", "buenas", "buenos dias", "buen día", "buenas tardes", "buenas noches"):
            # Mensaje de bienvenida básico
            session.state = STATE_IDLE
            session.waiting_for = WAITING_NONE
            session.data.clear()
            return [
                "👋 ¡Hola! Soy el bot del obligatorio de Algoritmos y Estructuras de Datos.",
                "Usá el comando */ayuda* para ver las opciones disponibles."
            ]

        if lower == "/reset":
            session.state = STATE_IDLE
            session.waiting_for = WAITING_NONE
            session.data.clear()
            return [
                "🔄 Conversación reiniciada.",
                "Mandá /ayuda para ver el menú de opciones."
            ]

        if lower == "/ayuda":
            return self._handle_ayuda(session)

        # Si no está en ningún flujo todavía, redirigimos a /ayuda
        if session.state == STATE_IDLE:
            return [
                "No entendí el mensaje 🤔",
                "Mandá */ayuda* para ver las opciones disponibles."
            ]

        # --- Enrutado según estado actual ---
        if session.state == STATE_MAIN_MENU:
            return self._handle_main_menu(session, lower)

        if session.state == STATE_RUTA:
            return self._handle_opcion_ruta(session, raw, lower)

        # Fallback por si queda algún estado colgado
        session.state = STATE_IDLE
        session.waiting_for = WAITING_NONE
        session.data.clear()
        return [
            "Se produjo un pequeño error en la conversación 😅",
            "Mandá /ayuda para empezar de nuevo."
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
            "Respondé con el *número* de la opción (por ejemplo: 1)."
        ]

    def _handle_main_menu(self, session: ChatSession, lower: str) -> List[str]:
        """
        Maneja la selección de opciones del menú principal.
        """
        if lower == "1":
            # Entramos al flujo de la opción 1: calcular ruta
            session.state = STATE_RUTA
            session.waiting_for = WAITING_RUTA_ORIGEN
            session.data.clear()

            return [
                "🛵 Vamos a calcular la *ruta de delivery*.",
                "Decime el *origen* (por ejemplo: plaza_artigas, terminal, etc.)."
            ]

        if lower == "2":
            # Placeholder para opción 2
            return [
                "La *Opción 2* todavía no está implementada.",
                "Por ahora, solo está funcionando la opción 1.",
                "Si querés probarla, mandá */ayuda* y elegí 1."
            ]

        if lower == "3":
            # Placeholder para opción 3
            return [
                "La *Opción 3* todavía no está implementada.",
                "Por ahora, solo está funcionando la opción 1.",
                "Si querés probarla, mandá */ayuda* y elegí 1."
            ]

        return [
            "No entendí la opción seleccionada 😅",
            "Respondé *1, 2 o 3*, o mandá /ayuda para ver el menú de nuevo."
        ]

    def _handle_opcion_ruta(self, session: ChatSession, raw: str, lower: str) -> List[str]:
        """
        Flujo de la opción 1: cálculo de ruta con Dijkstra / A*.
        - Paso 1: pedir ORIGEN
        - Paso 2: pedir DESTINO
        - Paso 3: llamar a coordenadas_gifs y mostrar resultado
        """
        # Import lazy (por si corre en entorno donde no está todavía el módulo)
        try:
            from coordenadas_gifs import dijkstra  # Ajustá el nombre según tu implementación
        except Exception:
            dijkstra = None

        # Paso 1: esperando origen
        if session.waiting_for == WAITING_RUTA_ORIGEN:
            origen = lower  # podés usar raw si querés respetar mayúsculas
            session.data["origen"] = origen
            session.waiting_for = WAITING_RUTA_DESTINO

            return [
                f"Perfecto ✅ Origen: *{origen}*.",
                "Ahora decime el *destino*."
            ]

        # Paso 2: esperando destino
        if session.waiting_for == WAITING_RUTA_DESTINO:
            destino = lower
            origen = session.data.get("origen")

            if not origen:
                # Algo raro pasó, reseteamos el flujo de ruta
                session.state = STATE_MAIN_MENU
                session.waiting_for = WAITING_NONE
                session.data.clear()
                return [
                    "Ocurrió un error interno con el origen de la ruta 😕.",
                    "Volvamos a empezar. Mandá */ayuda* y elegí la opción 1 de nuevo."
                ]

            # Intentar calcular la ruta
            if dijkstra is None:
                mensaje_ruta = [
                    "⚠️ El cálculo de rutas todavía no está disponible (no se pudo importar coordenadas_gifs.dijkstra).",
                    "Verificá que el módulo *coordenadas_gifs.py* exista en el proyecto y tenga la función dijkstra(origen, destino)."
                ]
            else:
                try:
                    # Ejemplo: asumimos que dijkstra devuelve (ruta, costo)
                    ruta, costo = dijkstra(origen, destino)

                    if not ruta:
                        mensaje_ruta = [
                            "No se encontró una ruta entre esos puntos 😕.",
                            "Revisá que el origen y destino existan en el grafo."
                        ]
                    else:
                        ruta_str = " -> ".join(ruta)
                        mensaje_ruta = [
                            "📍 *Resultado de la ruta*",
                            f"• Origen: *{origen}*",
                            f"• Destino: *{destino}*",
                            f"• Ruta: {ruta_str}",
                            f"• Costo total: {costo}",
                        ]

                except Exception as e:
                    mensaje_ruta = [
                        "⚠️ Ocurrió un error al calcular la ruta.",
                        "Revisá que el origen y destino existan en el grafo y que la función dijkstra funcione correctamente.",
                        f"Detalle técnico (para debug): {e}"
                    ]

            # Al terminar, volvemos al menú principal
            session.state = STATE_MAIN_MENU
            session.waiting_for = WAITING_NONE
            session.data.clear()

            mensaje_ruta.append("")
            mensaje_ruta.append("Si querés hacer otra consulta, mandá */ayuda*.")

            return mensaje_ruta

        # Si por alguna razón el waiting_for no coincide con nada
        session.state = STATE_MAIN_MENU
        session.waiting_for = WAITING_NONE
        session.data.clear()
        return [
            "Se perdió el hilo de la conversación de la ruta 😅.",
            "Mandá /ayuda y elegí la opción 1 para intentarlo de nuevo."
        ]


# Instancia global para que main.py pueda hacer: from chat import bot
bot = ChatBot()

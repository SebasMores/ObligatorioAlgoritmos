from functools import wraps
from typing import Any, Optional, Dict, Callable
from services.whatsapp_client import send_text_message


class Chat:
    def __init__(self):
        self.function_graph: Dict[str, Dict] = {}
        self.user_phone: str = ""
        self.waiting_for: Optional[Callable] = None
        self.conversation_data: Dict[str, Any] = {}

    # =============== REGISTRO DE FUNCIONES (NODOS DEL GRAFO) ===============

    def register(self, command: str):
        """Decorador para registrar comandos del bot."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self.function_graph[command] = {
                "function": wrapper,
                "name": func.__name__,
                "doc": func.__doc__,
                "command": command,
            }
            return wrapper
        return decorator

    # ==================== MANEJO DE ESTADO DE LA CONVERSACIÓN ====================

    def set_waiting_for(self, func: Callable, **context_data):
        """Setea la función que debe manejar la próxima respuesta del usuario."""
        self.waiting_for = func

        if context_data:
            self.conversation_data.update(context_data)

        print(f"⏳ Esperando respuesta para: {func.__name__}")

    def set_conversation_data(self, key: str, value: Any):
        self.conversation_data[key] = value

    def get_conversation_data(self, key: str, default: Any = None) -> Any:
        return self.conversation_data.get(key, default)

    def clear_conversation_data(self):
        self.conversation_data = {}

    def reset_conversation(self):
        self.waiting_for = None
        self.conversation_data = {}
        print("✅ Conversación reseteada.")

    def is_waiting_response(self) -> bool:
        return self.waiting_for is not None

    def get_waiting_function(self) -> Optional[Callable]:
        return self.waiting_for

    def print_state(self):
        print(f"\n{'='*60}")
        print("ESTADO DE LA CONVERSACIÓN")
        print(f"{'='*60}")
        waiting = self.waiting_for
        print(f"Esperando respuesta: {waiting.__name__ if waiting else 'No'}")
        print(f"Datos de conversación: {self.conversation_data}")
        print(f"{'='*60}\n")

    # ==================== PROCESAR MENSAJES ====================

    def process_message(self, mensaje: str):
        """
        Procesa un mensaje del usuario.
        """
        mensaje = mensaje.strip()
        print(f"[Chat] Mensaje recibido para procesar: {mensaje}")

        # Si estamos esperando una respuesta, llamar a la función correspondiente
        if self.is_waiting_response():
            waiting_func = self.get_waiting_function()
            if waiting_func:
                waiting_func(mensaje)
            return

        # Si es un comando (empieza con '/')
        if mensaje.startswith("/"):
            comando = mensaje.split()[0]
            if comando in self.function_graph:
                func = self.function_graph[comando]["function"]
                func()
            else:
                send_text_message(
                    self.user_phone,
                    "❌ Comando no reconocido. Escribe /ayuda para ver las opciones disponibles."
                )
        else:
            send_text_message(
                self.user_phone,
                "❌ Por favor usa un comando. Escribe /ayuda para ver opciones."
            )


# ==================== INSTANCIA GLOBAL DEL BOT ====================

bot = Chat()


# ==================== FUNCIONES DEL BOT (NODOS DEL GRAFO) ====================

@bot.register("/ayuda")
def funcion_0_ayuda():
    """Muestra ayuda básica."""
    mensaje = (
        "🤖 ¡Hola! Aquí tienes las opciones disponibles:\n"
        "/iniciar - Iniciar una nueva conversación\n"
        "/ayuda - Mostrar este mensaje de ayuda\n"
    )
    send_text_message(bot.user_phone, mensaje)
    # Ejemplo: la próxima respuesta la maneja la función de bienvenida
    bot.set_waiting_for(funcion_1_bienvenida)


@bot.register("/iniciar")
def funcion_1_bienvenida():
    """Inicia la conversación con opciones básicas (ejemplo)."""
    bot.clear_conversation_data()

    mensaje = (
        "🤖 ¡Bienvenido! ¿Qué deseas hacer?\n\n"
        "1️⃣ Agregar producto\n"
        "2️⃣ Consultar stock\n"
        "3️⃣ Ver historial\n\n"
        "Por favor responde con el número de tu opción (1, 2 o 3)."
    )
    send_text_message(bot.user_phone, mensaje)

    # La próxima respuesta del usuario será manejada por funcion_2_elegir_opcion
    bot.set_waiting_for(funcion_2_elegir_opcion)


def funcion_2_elegir_opcion(mensaje: str):
    """Recibe la opción del usuario y valida."""
    opcion = mensaje.strip()

    if opcion in ["1", "2", "3"]:
        bot.set_conversation_data("opcion_elegida", opcion)
        funcion_3_responder(opcion)
    else:
        send_text_message(
            bot.user_phone,
            "❌ Opción inválida. Intenta de nuevo.\nEscribe /iniciar para comenzar de nuevo."
        )
        bot.set_waiting_for(funcion_2_elegir_opcion)


def funcion_3_responder(opcion: str):
    """Responde según la opción elegida (ejemplo simple)."""

    if opcion == "1":
        send_text_message(bot.user_phone, "🛒 Opción 1: aquí iría la lógica para agregar producto.")
    elif opcion == "2":
        send_text_message(bot.user_phone, "📦 Opción 2: aquí iría la lógica para consultar stock.")
    elif opcion == "3":
        send_text_message(bot.user_phone, "🧾 Opción 3: aquí iría la lógica para ver el historial.")

    # Después de responder, podríamos resetear o volver a /iniciar
    bot.reset_conversation()

from functools import wraps
from typing import Any, Optional, Dict, Callable
import inspect
from datetime import datetime

class Chat:
    def __init__(self):
        self.function_graph: Dict[str, Dict] = {}
        self.user_phone: str = ""
        self.waiting_for: Optional[Callable] = None
        self.conversation_data: Dict[str, Any] = {}
    
    def register_function(self, command: str):
        """Decorador para registrar comandos del bot."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            self.function_graph[command] = {
                'function': wrapper,
                'name': func.__name__,
                'doc': func.__doc__,
                'command': command
            }
            
            return wrapper
        return decorator
    
    def set_waiting_for(self, func: Callable, **context_data):
        """
        Setea la función que debe manejar la próxima respuesta del usuario.
        Permite guardar datos de contexto adicionales.
        """
        self.waiting_for = func
        
        # Guardar datos de contexto
        if context_data:
            self.conversation_data.update(context_data)
        
        print(f"⏳ Esperando respuesta para: {func.__name__}")
    
    def set_conversation_data(self, key: str, value: Any):
        """Guarda datos temporales de la conversación."""
        self.conversation_data[key] = value
    
    def get_conversation_data(self, key: str, default: Any = None) -> Any:
        """Obtiene datos temporales de la conversación."""
        return self.conversation_data.get(key, default)
    
    def clear_conversation_data(self):
        """Limpia los datos temporales de la conversación."""
        self.conversation_data = {}
    
    def reset_conversation(self):
        """Resetea la conversación."""
        self.waiting_for = None
        self.conversation_data = {}
        print("✅ Conversación reseteada.")
    
    def is_waiting_response(self) -> bool:
        """Verifica si el bot está esperando una respuesta."""
        return self.waiting_for is not None
    
    def get_waiting_function(self) -> Optional[Callable]:
        """Obtiene la función que está esperando respuesta."""
        return self.waiting_for
    
    def print_state(self):
        """Imprime el estado actual."""
        print(f"\n{'='*60}")
        print("ESTADO DE LA CONVERSACIÓN")
        print(f"{'='*60}")
        waiting = self.waiting_for
        print(f"Esperando respuesta: {waiting.__name__ if waiting else 'No'}")
        print(f"Datos de conversación: {self.conversation_data}")
        print(f"{'='*60}\n")

    # ==================== FUNCIONES DEL BOT PARA MANEJAR LA CONVERSACIÓN ====================
    
    @register_function('/ayuda')
    def funcion_0_ayuda(self):
        """Inicia la conversación con opciones."""
        # Aqui ofrecer ayuda al usuario
        mensaje = """
        🤖 ¡Hola! Aquí tienes las opciones disponibles:
        /iniciar - Iniciar una nueva conversación
        /ayuda - Mostrar este mensaje de ayuda
        """
        print(f"send_message_to_user: {mensaje}") # Aqui enviar el mensaje al usuario por whatsapp
        
        self.set_waiting_for(self.funcion_1_bienvenida)


    @register_function('/iniciar')
    def funcion_1_bienvenida(self):
        """Inicia la conversación con opciones."""
        bot.clear_conversation_data()
        
        mensaje = """
        🤖 ¡Bienvenido! ¿Qué deseas hacer?
        
        1️⃣ Agregar producto
        2️⃣ Consultar stock
        3️⃣ Ver historial
        
        Por favor responde con el número de tu opción (1, 2 o 3)
        """
        print(mensaje) # Aqui enviar el mensaje al usuario por whatsapp
        
        # Setear que la próxima respuesta debe ser manejada por funcion_2
        bot.set_waiting_for(self.funcion_2_elegir_opcion)


    def funcion_2_elegir_opcion(self, mensaje: str):
        """Recibe la opción del usuario y valida."""
        opcion = mensaje.strip()
        
        # Validar que sea una opción válida
        if opcion in ['1', '2', '3']:
            bot.set_conversation_data('opcion_elegida', opcion)
            
            # Ir a la función 3 con la opción elegida
            self.funcion_3_responder(opcion)
        else:
            # Opción inválida, volver a la función 1
            print("❌ Opción inválida. Intenta de nuevo.")
            self.funcion_1_bienvenida()


    def funcion_3_responder(opcion: str):
        """Responde según la opción elegida."""
        
        # Implementar logica según la opción
        if opcion == '1':
            pass
        
        elif opcion == '2':
            pass
        
        elif opcion == '3':
            pass
        
    def process_message(self, mensaje: str):
        """
        Procesa un mensaje del usuario.
        Esta función simula recibir mensajes de WhatsApp.
        """
        
        # Si estamos esperando una respuesta, ejecutar la función en espera
        if self.is_waiting_response():
            waiting_func = self.get_waiting_function()
            if waiting_func:
                # Aqui encontrar forma de procesar los parametros (pueden usar function_call de los LLMs para extraer parametros)
                waiting_func(mensaje)
                return
        
        # Si es un comando
        if mensaje.startswith('/'):
            comando = mensaje.split()[0]  # Tomar solo el comando sin argumentos
            if comando in self.function_graph:
                # Aqui encontrar forma de procesar los parametros (pueden usar function_call de los LLMs para extraer parametros)
                self.function_graph[comando]['function'](mensaje)
            else:
                print("❌ Comando no reconocido. Usa /ayuda para ver comandos disponibles.")
        else:
            print("❌ Por favor usa un comando. Escribe /ayuda para ver opciones.")
            
            
# Crear instancia del bot
bot = Chat()
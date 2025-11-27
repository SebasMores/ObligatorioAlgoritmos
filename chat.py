from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from models.productos import PRODUCTOS, obtener_categorias, get_producto_por_id
import math


# Estados de la conversación
STATE_IDLE = "IDLE"
STATE_MAIN_MENU = "MAIN_MENU"
STATE_RUTA = "RUTA"
STATE_PEDIDO = "PEDIDO"  # NUEVO

WAITING_NONE = None
WAITING_RUTA_ORIGEN = "RUTA_ORIGEN"
WAITING_RUTA_DESTINO = "RUTA_DESTINO"
WAITING_RUTA_ALGORITMO = "RUTA_ALGORITMO"

# Pedido
WAITING_PEDIDO_PRODUCTO = "PEDIDO_PRODUCTO"
WAITING_PEDIDO_FILTRO = "PEDIDO_FILTRO"


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

        if lower == "/lista_demo":
            # Ejemplo simple copiando la idea del JSON del profe
            return [
                {
                    "kind": "interactive_list",
                    "header": "Ejemplo de Título",
                    "body": "Cuerpo de la lista de prueba.",
                    "footer": "Pie de lista demo",
                    "button": "Menú",
                    "sections": [
                        {
                            "title": "Productos",
                            "rows": [
                                {
                                    "id": "prod_1",
                                    "title": "Hamburguesa",
                                    "description": "Con cheddar",
                                },
                                {
                                    "id": "prod_2",
                                    "title": "Pizza",
                                    "description": "Con piña",
                                },
                            ],
                        },
                        {
                            "title": "Opciones",
                            "rows": [
                                {
                                    "id": "ver_mas",
                                    "title": "Ver más productos",
                                    "description": "Muestra los siguientes 5",
                                },
                                {
                                    "id": "filtrar",
                                    "title": "Filtrar",
                                    "description": "Filtrar por categoría",
                                },
                            ],
                        },
                    ],
                }
            ]

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

        if session.state == STATE_PEDIDO:
            return self._handle_pedido(session, raw, lower)

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
            "2️⃣ Realizar pedido (listar productos).",
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
            # Iniciar flujo de pedido (versión simplificada)
            session.state = STATE_PEDIDO
            session.waiting_for = WAITING_PEDIDO_PRODUCTO
            session.data.clear()

            # Página inicial de productos (0)
            session.data["pedido_pagina"] = 0

            return self._mostrar_lista_productos(session)

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

            orig_coord = lugares[origen_nombre]
            dest_coord = lugares[destino_nombre]

            try:
                origen_nodo = ox.distance.nearest_nodes(G, orig_coord[1], orig_coord[0])
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

            try:
                if usar_dijkstra:
                    dijkstra_gif(origen_nodo, destino_nodo)
                    ok = reconstruct_path_gif(origen_nodo, destino_nodo, "Dijkstra")
                    algoritmo = "Dijkstra"
                else:
                    a_star_gif(origen_nodo, destino_nodo)
                    ok = reconstruct_path_gif(origen_nodo, destino_nodo, "A_Star")
                    algoritmo = "A*"

                if not ok:
                    mensaje = [
                        f"⚠️ No se pudo reconstruir el camino con {algoritmo}.",
                        "Revisá si el grafo tiene conexión entre esos puntos.",
                    ]
                else:
                    mensaje = [
                        f"✅ Ruta calculada con *{algoritmo}* correctamente.",
                        "📍 El recorrido óptimo fue procesado.",
                        "ℹ️ El GIF animado se genera localmente para visualización.",
                    ]

            except Exception as e:
                mensaje = [
                    f"❌ Ocurrió un error al ejecutar {algoritmo}.",
                    f"Detalle técnico: {e}",
                ]

            session.state = STATE_IDLE
            session.waiting_for = WAITING_NONE
            session.data.clear()

            mensaje.append("")
            mensaje.append("Si querés hacer otra consulta, mandá */ayuda*.")

            return mensaje

        session.state = STATE_IDLE
        session.waiting_for = WAITING_NONE
        session.data.clear()

        return [
            "Se perdió el flujo de la ruta 😅.",
            "Mandá /ayuda y elegí la opción 1 para reintentar.",
        ]

    def _get_productos_filtrados_ordenados(self, session: ChatSession):
        filtro = session.data.get("pedido_filtro", "Todos")
        orden = session.data.get("pedido_orden", "asc")

        productos = PRODUCTOS

        # Filtrar por categoría
        if filtro and filtro != "Todos":
            productos = [p for p in productos if p.categoria == filtro]

        # Ordenar por precio
        reverse = orden == "desc"
        productos = sorted(productos, key=lambda p: p.precio, reverse=reverse)
        return productos

        # ================= OPCIÓN 2: PEDIDO (VERSIÓN SIMPLE) =================

    def _mostrar_lista_productos(self, session: ChatSession):
        """
        Versión simplificada:
        - Solo muestra los primeros 5 productos
        - Una sección Productos
        - Una sección Opciones con 'Ver más' si corresponde
        """

        pagina = session.data.get("pedido_pagina", 0)
        PAGE_SIZE = 5

        # Productos en orden tal cual están definidos
        productos = PRODUCTOS
        total_items = len(productos)
        total_paginas = max(1, math.ceil(total_items / PAGE_SIZE))

        if pagina < 0:
            pagina = 0
        if pagina > total_paginas - 1:
            pagina = total_paginas - 1
        session.data["pedido_pagina"] = pagina

        start = pagina * PAGE_SIZE
        end = start + PAGE_SIZE
        productos_pagina = productos[start:end]

        rows_productos = []
        for p in productos_pagina:
            rows_productos.append(
                {
                    "id": p.id,
                    "title": f"{p.nombre} - ${p.precio:.0f}",
                    "description": p.categoria,
                }
            )

        rows_opciones = []
        if pagina < total_paginas - 1:
            rows_opciones.append(
                {
                    "id": "opt_ver_mas",
                    "title": "Siguientes productos",
                    "description": "Ver los próximos 5 productos",
                }
            )

        sections = []
        if rows_productos:
            sections.append({"title": "Productos", "rows": rows_productos})
        if rows_opciones:
            sections.append({"title": "Opciones", "rows": rows_opciones})

        body_text = f"Página {pagina + 1}/{total_paginas}."

        return [
            {
                "kind": "interactive_list",
                "header": "Menú de productos",
                "body": body_text,
                "footer": "Elegí un producto o 'Siguientes productos'.",
                "button": "Ver opciones",
                "sections": sections,
            }
        ]

    def _handle_pedido(self, session: ChatSession, raw: str, lower: str):
        """
        Versión simple:
        - Si elige 'opt_ver_mas' → avanza de página
        - Si elige un ID de producto → solo informa qué producto eligió
        """

        if session.waiting_for == WAITING_PEDIDO_PRODUCTO:
            # Ver más productos
            if lower == "opt_ver_mas":
                session.data["pedido_pagina"] = session.data.get("pedido_pagina", 0) + 1
                return self._mostrar_lista_productos(session)

            # Asumimos que cualquier otra cosa es ID de producto
            producto = get_producto_por_id(raw) or get_producto_por_id(lower)
            if producto is None:
                return [
                    "No reconocí esa opción 😅",
                    "Usá la lista interactiva para elegir un producto.",
                ] + self._mostrar_lista_productos(session)

            return [
                f"🛒 Elegiste: *{producto.nombre}* (${producto.precio:.0f}).",
                "Más adelante vamos a sumar cantidad y carrito.",
            ] + self._mostrar_lista_productos(session)

        # Si se pierde el flujo, volvemos al menú
        session.state = STATE_MAIN_MENU
        session.waiting_for = WAITING_NONE
        session.data.clear()
        return [
            "Se perdió el flujo de pedido 😅",
            "Mandá /ayuda y volvé a elegir la opción 2.",
        ]

    def _mostrar_lista_categorias(self, session: ChatSession):
        """
        Lista interactiva SOLO de categorías para elegir filtro.
        """
        categorias = obtener_categorias()  # incluye "Todos" al inicio

        rows = []
        for cat in categorias:
            rows.append(
                {
                    "id": f"cat_{cat.lower()}",
                    "title": cat,
                    "description": "Filtrar por esta categoría",
                }
            )

        return [
            {
                "kind": "interactive_list",
                "header": "Filtrar productos",
                "body": "Elegí una categoría para filtrar.",
                "footer": "La opción 'Todos' quita el filtro.",
                "button": "Categorías",
                "sections": [
                    {
                        "title": "Categorías",
                        "rows": rows,
                    }
                ],
            }
        ]

    def _handle_pedido(self, session: ChatSession, raw: str, lower: str):
        """
        Maneja el flujo de listado de productos y opciones (ver más, filtrar, ordenar).
        El 'lower' puede ser:
          - id de producto (p1, m1, etc.)
          - opción (opt_ver_mas, opt_filtrar, opt_ordenar, etc.)
          - categoría (cat_pizzas, cat_todos, ...)
        """

        # Esperando que el usuario interactúe con la lista de productos/opciones
        if session.waiting_for == WAITING_PEDIDO_PRODUCTO:
            # Opciones especiales
            if lower == "opt_ver_mas":
                session.data["pedido_pagina"] = session.data.get("pedido_pagina", 0) + 1
                return self._mostrar_lista_productos(session)

            if lower == "opt_volver":
                session.data["pedido_pagina"] = session.data.get("pedido_pagina", 0) - 1
                return self._mostrar_lista_productos(session)

            if lower == "opt_volver_inicio":
                session.data["pedido_pagina"] = 0
                return self._mostrar_lista_productos(session)

            if lower == "opt_filtrar":
                # Cambiamos el waiting_for para interpretar la elección de categoría
                session.waiting_for = WAITING_PEDIDO_FILTRO
                return self._mostrar_lista_categorias(session)

            if lower == "opt_ordenar":
                # Toggle asc/desc
                orden_actual = session.data.get("pedido_orden", "asc")
                session.data["pedido_orden"] = (
                    "desc" if orden_actual == "asc" else "asc"
                )
                return self._mostrar_lista_productos(session)

            # Si no es opción, asumimos que es un id de producto
            producto = get_producto_por_id(raw) or get_producto_por_id(lower)
            if producto is None:
                # Puede que el usuario haya escrito texto libre
                return [
                    "No reconocí esa opción 😅",
                    "Respondé desde la lista interactiva o mandá /ayuda para volver al menú.",
                ]

            # Por ahora solo confirmamos el producto elegido.
            # Más adelante acá vamos a pedir cantidad y detalles y guardarlo en el carrito.
            return [
                f"🛒 Elegiste: *{producto.nombre}* (${producto.precio:.0f}).",
                "En la próxima etapa vamos a pedir cantidad y detalles para el carrito.",
                "",
                "Por ahora podés seguir explorando productos:",
            ] + self._mostrar_lista_productos(session)

        # Esperando elección de categoría
        if session.waiting_for == WAITING_PEDIDO_FILTRO:
            if lower.startswith("cat_"):
                nombre_cat = raw[4:] if raw.lower().startswith("cat_") else lower[4:]
                # Reconstruimos el nombre original de categoría
                categorias = obtener_categorias()
                seleccion = None
                for cat in categorias:
                    if f"cat_{cat.lower()}" == lower:
                        seleccion = cat
                        break

                if seleccion is None:
                    # algo raro, volvemos sin cambiar nada
                    session.waiting_for = WAITING_PEDIDO_PRODUCTO
                    return self._mostrar_lista_productos(session)

                # Aplicar filtro
                session.data["pedido_filtro"] = seleccion
                session.data["pedido_pagina"] = 0
                session.waiting_for = WAITING_PEDIDO_PRODUCTO
                return self._mostrar_lista_productos(session)

            # Si no eligió una categoría válida
            session.waiting_for = WAITING_PEDIDO_PRODUCTO
            return [
                "No reconocí esa categoría 😅",
                "Volvemos al listado de productos.",
            ] + self._mostrar_lista_productos(session)

        # Cualquier otra cosa rara, volvemos al menú principal
        session.state = STATE_MAIN_MENU
        session.waiting_for = WAITING_NONE
        session.data.clear()
        return [
            "Se perdió el flujo de pedido 😅",
            "Mandá /ayuda y volvé a elegir la opción 2.",
        ]


# Instancia global para que main.py pueda hacer:
# from chat import bot
bot = ChatBot()

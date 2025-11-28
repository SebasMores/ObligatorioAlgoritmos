from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from models.productos import PRODUCTOS, get_producto_por_id, obtener_categorias
import math

# Estados de la conversación
STATE_IDLE = "IDLE"
STATE_MAIN_MENU = "MAIN_MENU"
STATE_RUTA = "RUTA"
STATE_PEDIDO = "PEDIDO"

WAITING_NONE = None
WAITING_RUTA_ORIGEN = "RUTA_ORIGEN"
WAITING_RUTA_DESTINO = "RUTA_DESTINO"
WAITING_RUTA_ALGORITMO = "RUTA_ALGORITMO"

# Pedido
WAITING_PEDIDO_PRODUCTO = "PEDIDO_PRODUCTO"
WAITING_PEDIDO_FILTRO = "PEDIDO_FILTRO"
WAITING_PEDIDO_CANTIDAD = "PEDIDO_CANTIDAD"
WAITING_PEDIDO_CONFIRMAR = "PEDIDO_CONFIRMAR"


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
    def handle_message(self, user_id: str, text: str) -> List[Any]:
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

        if lower == "/carrito":
            carrito = session.data.get("carrito", [])
            if not carrito:
                return [
                    "Tu carrito está vacío 🧺",
                    "Elegí la opción *2* en /ayuda para empezar un pedido.",
                ]
            return self._formatear_resumen_carrito(carrito)

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

    def _handle_main_menu(self, session: ChatSession, lower: str) -> List[Any]:
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
            session.data["pedido_filtro"] = "Todos"
            session.data["pedido_orden"] = "asc"

            return self._mostrar_lista_productos(session)

        if lower == "3":
            return [
                "La *Opción 3* todavía no está implementada.",
                "Por ahora, solo están funcionando las opciones 1 y 2.",
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

    # ================= OPCIÓN 2: PEDIDO (VERSIÓN SIMPLE) =================

    # ================= OPCIÓN 2: PEDIDO =================

    def _formatear_resumen_carrito(self, carrito):
        """
        Devuelve una lista de líneas de texto con el resumen del carrito.
        """
        if not carrito:
            return ["Tu carrito está vacío 🧺"]

        lineas = ["🧺 *Carrito actual:*", ""]
        total = 0

        for item in carrito:
            sub = item["cantidad"] * item["precio_unitario"]
            total += sub
            lineas.append(f"- {item['cantidad']} x {item['nombre']} = ${sub:.0f}")

        lineas.append("")
        lineas.append(f"💰 *Total:* ${total:.0f}")
        return lineas

    def _get_productos_filtrados(self, session: ChatSession):
        """
        Devuelve la lista de productos aplicando:
        - filtro por categoría (pedido_filtro)
        - orden por precio asc/desc (pedido_orden)
        """
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

    def _mostrar_lista_productos(self, session: ChatSession):
        """
        Muestra hasta 5 productos por página, con:
        - Filtro por categoría
        - Orden por precio asc/desc (toggle)
        - Opciones: ver más, filtrar, ordenar, finalizar, volver al menú
        """

        pagina = session.data.get("pedido_pagina", 0)
        PAGE_SIZE = 5

        # Productos con filtro + orden aplicados
        productos = self._get_productos_filtrados(session)
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
            # Título corto: solo el nombre, máx 24 caracteres
            title_text = p.nombre
            if len(title_text) > 24:
                title_text = title_text[:23] + "…"

            rows_productos.append(
                {
                    "id": p.id,
                    "title": title_text,
                    "description": f"${p.precio:.0f} · {p.categoria}",
                }
            )

        rows_opciones = []

        # Opción de ver más (si hay más páginas)
        if pagina < total_paginas - 1:
            rows_opciones.append(
                {
                    "id": "opt_ver_mas",
                    "title": "Siguientes productos",
                    "description": "Ver los próximos 5 productos",
                }
            )

        # Opción de filtrar por categoría
        rows_opciones.append(
            {
                "id": "opt_filtrar",
                "title": "Filtrar por categoría",
                "description": "Ver solo una categoría",
            }
        )

        # Opción de ordenar por precio (toggle asc/desc)
        orden_actual = session.data.get("pedido_orden", "asc")
        desc_opcion = "Descendente" if orden_actual == "asc" else "Ascendente"

        rows_opciones.append(
            {
                "id": "opt_ordenar",
                "title": "Ordenar por precio",
                "description": f"Cambiar a {desc_opcion}",
            }
        )

        # Finalizar pedido (ver resumen + confirmar)
        rows_opciones.append(
            {
                "id": "opt_finalizar",
                "title": "Finalizar pedido",
                "description": "Ver resumen y confirmar compra",
            }
        )

        # 🔙 NUEVO: Volver al menú principal
        rows_opciones.append(
            {
                "id": "opt_volver_menu",
                "title": "Volver al menú",
                "description": "Cancelar pedido y volver al menú principal",
            }
        )

        sections = []
        if rows_productos:
            sections.append({"title": "Productos", "rows": rows_productos})
        if rows_opciones:
            sections.append({"title": "Opciones", "rows": rows_opciones})

        filtro_actual = session.data.get("pedido_filtro", "Todos")
        orden_texto = "Ascendente" if orden_actual == "asc" else "Descendente"
        body_text = (
            f"Página {pagina + 1}/{total_paginas} · "
            f"Filtro: {filtro_actual} · Orden: {orden_texto}"
        )

        return [
            {
                "kind": "interactive_list",
                "header": "Menú de productos",
                "body": body_text,
                "footer": "Elegí un producto o una opción.",
                "button": "Ver opciones",
                "sections": sections,
            }
        ]

    def _mostrar_lista_categorias(self, session: ChatSession) -> List[Any]:
        """
        Lista interactiva SOLO de categorías para elegir filtro.
        Usa obtener_categorias() de models.productos.
        """
        categorias = obtener_categorias()  # p.ej: ["Todos", "Bebidas", "Minutas", ...]

        rows = []
        for cat in categorias:
            cat_id = "cat_" + cat.lower().replace(" ", "_")
            rows.append(
                {
                    "id": cat_id,
                    "title": cat,
                    "description": "Filtrar por esta categoría",
                }
            )

        return [
            {
                "kind": "interactive_list",
                "header": "Filtrar productos",
                "body": "Elegí una categoría para aplicar el filtro.",
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
           Flujo de pedido:
           - WAITING_PEDIDO_PRODUCTO: lista de productos y opciones
           - WAITING_PEDIDO_FILTRO: lista de categorías
           - WAITING_PEDIDO_CANTIDAD: pedir cantidad del producto elegido
        - WAITING_PEDIDO_CONFIRMAR: preguntar si sigue agregando o confirma
        """

        # ================== LISTA DE PRODUCTOS / OPCIONES ==================
        if session.waiting_for == WAITING_PEDIDO_PRODUCTO:
            # Ver más productos
            if lower == "opt_ver_mas":
                session.data["pedido_pagina"] = session.data.get("pedido_pagina", 0) + 1
                return self._mostrar_lista_productos(session)

            # Finalizar pedido → ver resumen
            if lower == "opt_finalizar":
                return self._mostrar_resumen_carrito(session)

            # Ir a elegir categoría (filtro)
            if lower == "opt_filtrar":
                session.waiting_for = WAITING_PEDIDO_FILTRO
                return self._mostrar_lista_categorias(session)

            # Ordenar por precio (toggle asc/desc)
            if lower == "opt_ordenar":
                orden_actual = session.data.get("pedido_orden", "asc")
                session.data["pedido_orden"] = (
                    "desc" if orden_actual == "asc" else "asc"
                )
                session.data["pedido_pagina"] = 0
                return self._mostrar_lista_productos(session)

            if lower == "opt_volver_menu":
                # Cancelamos el flujo de pedido y volvemos al menú
                session.state = STATE_MAIN_MENU
                session.waiting_for = WAITING_NONE
                session.data.clear()
                return [
                    "↩️ Volviste al *menú principal*.",
                ] + self._handle_ayuda(session)

            # Asumimos que cualquier otra cosa es ID de producto
            producto = get_producto_por_id(raw) or get_producto_por_id(lower)
            if producto is None:
                return [
                    "No reconocí esa opción 😅",
                    "Usá la lista interactiva para elegir un producto o una opción.",
                ] + self._mostrar_lista_productos(session)

            # Guardamos el producto elegido en la sesión y pedimos cantidad
            session.data["producto_actual_id"] = producto.id
            session.waiting_for = WAITING_PEDIDO_CANTIDAD

            return [
                f"🛒 Elegiste: *{producto.nombre}* (${producto.precio:.0f}).",
                "¿Cuántas unidades querés? (ingresá un número entero, por ejemplo: 1, 2, 3)",
            ]

            # ================== PEDIR CANTIDAD ==================
        if session.waiting_for == WAITING_PEDIDO_CANTIDAD:
            prod_id = session.data.get("producto_actual_id")
            producto = get_producto_por_id(prod_id) if prod_id else None

            if producto is None:
                # Algo raro: volvemos al listado de productos
                session.waiting_for = WAITING_PEDIDO_PRODUCTO
                return [
                    "Se perdió el producto seleccionado 😅",
                    "Volvemos al listado de productos.",
                ] + self._mostrar_lista_productos(session)

            # Intentar convertir la cantidad a entero
            try:
                cantidad = int(raw)
            except ValueError:
                return [
                    "Necesito que me indiques una cantidad en números 🙏",
                    "Por ejemplo: 1, 2, 3...",
                ]

            if cantidad <= 0:
                return [
                    "La cantidad debe ser un número entero positivo 🙂",
                    "Por ejemplo: 1, 2, 3...",
                ]

            # Agregar al carrito
            carrito = session.data.get("carrito", [])
            carrito.append(
                {
                    "producto_id": producto.id,
                    "nombre": producto.nombre,
                    "cantidad": cantidad,
                    "precio_unitario": producto.precio,
                }
            )
            session.data["carrito"] = carrito
            # Ya no necesitamos el producto_actual
            session.data.pop("producto_actual_id", None)

            subtotal = cantidad * producto.precio
            total = sum(item["cantidad"] * item["precio_unitario"] for item in carrito)

            session.waiting_for = WAITING_PEDIDO_CONFIRMAR

            return [
                f"✅ Se agregaron *{cantidad} x {producto.nombre}* al carrito (subtotal: ${subtotal:.0f}).",
                f"🧾 Total parcial del pedido: ${total:.0f}.",
                "",
                "¿Qué querés hacer ahora?️",
                "1️⃣ Agregar otro producto",
                "2️⃣ Confirmar pedido",
                "3️⃣ Ver carrito / editar",
            ]

            # ================== CONFIRMAR O SEGUIR AGREGANDO ==================
        if session.waiting_for == WAITING_PEDIDO_CONFIRMAR:
            carrito = session.data.get("carrito", [])

            # 1️⃣ Seguir agregando productos
            if lower == "1":
                session.waiting_for = WAITING_PEDIDO_PRODUCTO
                return [
                    "Perfecto, seguimos agregando productos 👍",
                ] + self._mostrar_lista_productos(session)

            # 2️⃣ Confirmar pedido
            if lower == "2":
                if not carrito:
                    # Por las dudas, si no hay nada en el carrito
                    session.waiting_for = WAITING_PEDIDO_PRODUCTO
                    return [
                        "Todavía no tenés productos en el carrito 😅",
                        "Elegí alguno de la lista.",
                    ] + self._mostrar_lista_productos(session)

                lineas = self._formatear_resumen_carrito(carrito)
                lineas.append("")
                lineas.append("✅ Pedido confirmado (a modo de simulación).")
                lineas.append("Si querés empezar de nuevo, mandá */ayuda*.")

                # Cerrar flujo de pedido
                session.state = STATE_IDLE
                session.waiting_for = WAITING_NONE
                session.data.clear()

                return lineas

            # 3️⃣ Ver carrito / editar
            if lower == "3" or lower in ("ver carrito", "carrito"):
                if not carrito:
                    return [
                        "Tu carrito todavía está vacío 🧺",
                        "Podés agregar productos desde el menú.",
                    ] + self._mostrar_lista_productos(session)

                lineas = self._formatear_resumen_carrito(carrito)
                lineas.append("")
                lineas.append(
                    "Si querés eliminar el último producto, escribí *eliminar*."
                )
                lineas.append("Si querés vaciar el carrito, escribí *vaciar*.")
                lineas.append(
                    "Si querés seguir, respondé *1* para agregar otro producto o *2* para confirmar."
                )
                return lineas

            # Eliminar último ítem del carrito
            if lower.startswith("eliminar"):
                if carrito:
                    carrito.pop()
                    session.data["carrito"] = carrito
                    resp = ["Se eliminó el último producto del carrito ✅"]

                    if carrito:
                        resp += self._formatear_resumen_carrito(carrito)
                    else:
                        resp.append("El carrito quedó vacío 🧺")

                    resp.append("")
                    resp.append(
                        "Respondé *1* para agregar otro producto o *2* para confirmar (si hay productos)."
                    )
                    return resp
                else:
                    return [
                        "El carrito ya está vacío 😅",
                        "Respondé *1* para agregar un producto.",
                    ]

            # Vaciar carrito
            if lower.startswith("vaciar"):
                if carrito:
                    session.data["carrito"] = []
                    return [
                        "Vacié el carrito ✅",
                        "Respondé *1* para agregar productos de nuevo.",
                    ]
                else:
                    return [
                        "El carrito ya estaba vacío 🙂",
                        "Respondé *1* para agregar productos.",
                    ]

            # Si no respondió nada de lo esperado
            return [
                "No entendí esa opción 😅",
                "Respondé *1* para agregar otro producto, *2* para confirmar el pedido o *3* para ver/editar el carrito.",
            ]

            # ================== LISTA DE CATEGORÍAS (FILTRO) ==================
        if session.waiting_for == WAITING_PEDIDO_FILTRO:
            # Esperamos ids tipo: cat_pizzas, cat_bebidas, cat_todos, etc.
            if lower.startswith("cat_"):
                categorias = obtener_categorias()
                seleccion = None
                for cat in categorias:
                    cat_id = "cat_" + cat.lower().replace(" ", "_")
                    if cat_id == lower:
                        seleccion = cat
                        break

                if seleccion is None:
                    # Algo raro: volvemos al listado sin cambiar nada
                    session.waiting_for = WAITING_PEDIDO_PRODUCTO
                    return [
                        "No reconocí esa categoría 😅",
                        "Volvemos al listado de productos.",
                    ] + self._mostrar_lista_productos(session)

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

            # ================== FALLBACK ==================
        session.state = STATE_MAIN_MENU
        session.waiting_for = WAITING_NONE
        session.data.clear()
        return [
            "Se perdió el flujo de pedido 😅",
            "Mandá /ayuda y volvé a elegir la opción 2.",
        ]

    def _mostrar_resumen_carrito(self, session: ChatSession):

        carrito = session.data.get("carrito", [])

        if not carrito:
            return [
                "🧺 Tu carrito está vacío.",
                "Agregá productos antes de finalizar.",
            ] + self._mostrar_lista_productos(session)

        mensaje = ["🧾 *Resumen del pedido:*", ""]

        total = 0
        for item in carrito:
            subtotal = item["cantidad"] * item["precio_unitario"]
            total += subtotal
            mensaje.append(f"{item['nombre']} x{item['cantidad']} → ${subtotal:.0f}")

        mensaje.append("")
        mensaje.append(f"💰 Total: ${total:.0f}")
        mensaje.append("")
        mensaje.append("¿Confirmás el pedido?")
        mensaje.append("1️⃣ Confirmar")
        mensaje.append("2️⃣ Cancelar")

        session.waiting_for = WAITING_PEDIDO_CONFIRMAR
        return mensaje


# Instancia global para que main.py pueda hacer:
# from chat import bot
bot = ChatBot()

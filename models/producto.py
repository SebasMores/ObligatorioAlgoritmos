class Producto:
    def __init__(self, id, nombre, descripcion, precio, categoria):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.categoria = categoria  # "Pizzas", "Minutas", "Bebidas", etc.
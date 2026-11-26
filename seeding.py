
import os
import hashlib
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP

from bson.decimal128 import Decimal128
from dotenv import load_dotenv
from faker import Faker
from pymongo import MongoClient

from cifrado import cifrar


# ==========================================
# CONFIGURACIÓN
# ==========================================

load_dotenv()

URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")

if not URI or not DB_NAME:
    raise RuntimeError("Faltan MONGODB_URI o DB_NAME en .env")

fake = Faker("es_MX")
Faker.seed(2026)
random.seed(2026)

FECHA_BASE = datetime(2026, 11, 1, tzinfo=timezone.utc)


def dinero(valor):
    numero = Decimal(str(valor)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
    return Decimal128(numero)


def hash_correo(correo):
    return hashlib.sha256(
        correo.strip().lower().encode("utf-8")
    ).hexdigest()


# ==========================================
# CATÁLOGO DE PRODUCTOS
# ==========================================

CATALOGO = [
    ("Laptop Lenovo IdeaPad", "Electronica", 12500),
    ("Mouse Logitech", "Electronica", 450),
    ("Teclado Mecanico", "Electronica", 1200),
    ("Monitor Samsung 24", "Electronica", 3200),
    ("Audifonos Bluetooth", "Electronica", 850),
    ("Memoria USB 64GB", "Electronica", 180),
    ("Disco SSD 1TB", "Electronica", 1450),
    ("Webcam Full HD", "Electronica", 680),
    ("Bocina Bluetooth", "Electronica", 950),
    ("Cargador USB-C", "Electronica", 350),
    ("Playera Deportiva", "Ropa", 299),
    ("Sudadera", "Ropa", 650),
    ("Pantalon Mezclilla", "Ropa", 799),
    ("Tenis Deportivos", "Ropa", 1350),
    ("Gorra", "Accesorios", 250),
    ("Mochila Escolar", "Accesorios", 780),
    ("Botella Termica", "Accesorios", 390),
    ("Reloj Digital", "Accesorios", 1100),
    ("Lampara de Escritorio", "Hogar", 550),
    ("Silla de Oficina", "Hogar", 2750),
    ("Organizador de Escritorio", "Hogar", 320),
    ("Juego de Sabanas", "Hogar", 890),
    ("Balon de Futbol", "Deportes", 480),
    ("Mancuernas 5KG", "Deportes", 720),
    ("Tapete de Yoga", "Deportes", 450),
]


# ==========================================
# CLIENTES
# ==========================================

def crear_clientes(db):
    insertados = 0

    for i in range(1, 21):
        correo = f"cliente{i:03d}@ejemplo.com"
        correo_hash = hash_correo(correo)

        if db.clientes.find_one({"correo_hash": correo_hash}):
            continue

        cliente = {
            "nombre": fake.first_name(),
            "apellidos": (
                f"{fake.last_name()} {fake.last_name()}"
            ),
            "correo_hash": correo_hash,
            "correo_cifrado": cifrar(correo),
            "telefono_cifrado": cifrar(
                fake.numerify("33########")
            ),
            "direcciones": [
                {
                    "calle": cifrar(fake.street_name()),
                    "ciudad": "Guadalajara",
                    "estado": "Jalisco",
                    "codigo_postal": fake.numerify("#####")
                }
            ],
            "fecha_registro": FECHA_BASE,
            "activo": True
        }

        db.clientes.insert_one(cliente)
        insertados += 1

    print(f"Clientes nuevos: {insertados}")


# ==========================================
# PRODUCTOS
# ==========================================

def crear_productos(db):
    insertados = 0

    for i, (nombre, categoria, precio) in enumerate(
        CATALOGO, start=1
    ):
        sku = f"PROD-{i:03d}"

        if db.productos.find_one({"sku": sku}):
            continue

        producto = {
            "sku": sku,
            "nombre": nombre,
            "descripcion": f"Producto de categoria {categoria}",
            "categoria": categoria,
            "precio": dinero(precio),
            "moneda": "MXN",
            "proveedor": {
                "nombre": "Distribuidora Comercial MX",
                "correo": "ventas@ejemplo.com"
            },
            "caracteristicas": {
                "modelo": f"MODELO-{i:03d}"
            },
            "activo": True
        }

        db.productos.insert_one(producto)
        insertados += 1

    print(f"Productos nuevos: {insertados}")


# ==========================================
# INVENTARIO
# ==========================================

def crear_inventario(db):
    insertados = 0

    skus = ["LAP-001"] + [
        f"PROD-{i:03d}" for i in range(1, 26)
    ]

    for sku in skus:
        producto = db.productos.find_one({"sku": sku})

        if producto is None:
            continue

        if db.inventario.find_one({
            "producto_id": producto["_id"]
        }):
            continue

        existencias = random.randint(15, 100)
        reservadas = random.randint(0, 5)

        inventario = {
            "producto_id": producto["_id"],
            "almacen": "Almacen Principal",
            "existencias": existencias,
            "reservadas": reservadas,
            "stock_minimo": 10,
            "ultima_actualizacion": FECHA_BASE
        }

        db.inventario.insert_one(inventario)
        insertados += 1

    print(f"Registros de inventario nuevos: {insertados}")


# ==========================================
# PEDIDOS
# ==========================================

def crear_pedidos(db):
    insertados = 0

    clientes = [
        db.clientes.find_one({
            "correo_hash": hash_correo(
                f"cliente{i:03d}@ejemplo.com"
            )
        })
        for i in range(1, 21)
    ]

    clientes = [c for c in clientes if c is not None]

    productos = [
        db.productos.find_one({"sku": f"PROD-{i:03d}"})
        for i in range(1, 26)
    ]

    productos = [p for p in productos if p is not None]

    if not clientes or not productos:
        raise RuntimeError(
            "Se necesitan clientes y productos antes de crear pedidos"
        )

    for i in range(1, 21):
        codigo = f"SEED-PED-{i:03d}"

        if db.pedidos.find_one({"seed_codigo": codigo}):
            continue

        cliente = clientes[(i - 1) % len(clientes)]

        seleccion = [
            productos[(i - 1) % len(productos)],
            productos[(i + 4) % len(productos)]
        ]

        items = []
        subtotal_pedido = Decimal("0.00")

        for producto in seleccion:
            cantidad = random.randint(1, 3)
            precio = producto["precio"].to_decimal()

            subtotal_item = precio * cantidad
            subtotal_pedido += subtotal_item

            items.append({
                "producto_id": producto["_id"],
                "sku": producto["sku"],
                "nombre": producto["nombre"],
                "cantidad": cantidad,
                "precio_unitario": producto["precio"],
                "subtotal": dinero(subtotal_item)
            })

        # Importes ficticios consistentes para las pruebas
        impuestos = (subtotal_pedido * Decimal("0.16"))
        costo_envio = Decimal("150.00")
        total = subtotal_pedido + impuestos + costo_envio

        direccion = cliente["direcciones"][0].copy()

        pedido = {
            "seed_codigo": codigo,
            "cliente_id": cliente["_id"],
            "fecha_pedido": FECHA_BASE + timedelta(days=i - 1),
            "productos": items,
            "subtotal": dinero(subtotal_pedido),
            "impuestos": dinero(impuestos),
            "costo_envio": dinero(costo_envio),
            "total": dinero(total),
            "estado": "Pendiente",
            "envio": {
                "paqueteria": "DHL",
                "estado": "Pendiente",
                "direccion": direccion
            }
        }

        db.pedidos.insert_one(pedido)
        insertados += 1

    print(f"Pedidos nuevos: {insertados}")


# ==========================================
# PAGOS
# ==========================================

def crear_pagos(db):
    insertados = 0

    for i in range(1, 21):
        referencia = f"SEED-PAGO-{i:03d}"
        codigo_pedido = f"SEED-PED-{i:03d}"

        if db.pagos.find_one({"referencia": referencia}):
            continue

        pedido = db.pedidos.find_one({
            "seed_codigo": codigo_pedido
        })

        if pedido is None:
            raise RuntimeError(
                f"No existe el pedido {codigo_pedido}"
            )

        pago = {
            "pedido_id": pedido["_id"],
            "referencia": referencia,
            "metodo": random.choice([
                "Tarjeta", "Transferencia", "Efectivo"
            ]),
            "monto": pedido["total"],
            "moneda": "MXN",
            "estado": "Pendiente",
            "fecha_pago": pedido["fecha_pedido"]
        }

        db.pagos.insert_one(pago)
        insertados += 1

    print(f"Pagos nuevos: {insertados}")


# ==========================================
# AUDITORÍA
# ==========================================

def crear_auditoria(db):
    insertados = 0

    # Eventos ficticios para probar la colección.
    # No son registros capturados automáticamente por triggers.

    for i in range(1, 16):
        codigo = f"SEED-AUD-{i:03d}"

        if db.auditoria.find_one({"seed_codigo": codigo}):
            continue

        pedido = db.pedidos.find_one({
            "seed_codigo": f"SEED-PED-{i:03d}"
        })

        if pedido is None:
            raise RuntimeError(
                f"No existe el pedido de auditoría {i}"
            )

        evento = {
            "seed_codigo": codigo,
            "usuario": "seed_script",
            "accion": "INSERT",
            "coleccion": "pedidos",
            "documento_id": pedido["_id"],
            "fecha": pedido["fecha_pedido"],
            "datos_anteriores": None,
            "datos_nuevos": {
                "estado": "Pendiente",
                "origen": "Datos ficticios de prueba"
            }
        }

        db.auditoria.insert_one(evento)
        insertados += 1

    print(f"Eventos de auditoría nuevos: {insertados}")


# ==========================================
# EJECUCIÓN
# ==========================================

def main():
    with MongoClient(
        URI,
        serverSelectionTimeoutMS=5000
    ) as client:

        client.admin.command("ping")
        db = client[DB_NAME]

        print("Conectado a MongoDB Atlas")
        print("Iniciando poblado de datos...\n")

        crear_clientes(db)
        crear_productos(db)
        crear_inventario(db)
        crear_pedidos(db)
        crear_pagos(db)
        crear_auditoria(db)

        print("\n--- CONTEO FINAL ---")

        colecciones = [
            "clientes",
            "productos",
            "pedidos",
            "pagos",
            "inventario",
            "auditoria"
        ]

        total = 0

        for nombre in colecciones:
            cantidad = db[nombre].count_documents({})
            total += cantidad
            print(f"{nombre}: {cantidad}")

        print(f"\nTOTAL DE DOCUMENTOS: {total}")
        print("Poblado finalizado")


if __name__ == "__main__":
    main()

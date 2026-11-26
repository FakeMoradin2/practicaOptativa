
import os
import hashlib

from bson.decimal128 import Decimal128
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")
db_name = os.getenv("DB_NAME")

if not uri or not db_name:
    raise RuntimeError("Faltan variables de conexión")

with MongoClient(uri, serverSelectionTimeoutMS=5000) as client:
    db = client[db_name]
    client.admin.command("ping")

    # Obtener el cliente que ya registramos
    correo = "cliente@ejemplo.com"
    correo_hash = hashlib.sha256(
        correo.lower().strip().encode("utf-8")
    ).hexdigest()

    cliente = db.clientes.find_one({
        "correo_hash": correo_hash
    })

    producto = db.productos.find_one({
        "sku": "LAP-001"
    })

    if not cliente or not producto:
        raise RuntimeError(
            "No se encontró el cliente o producto de prueba"
        )

    # Evitar insertar varias veces el mismo pedido de prueba
    pedido_existente = db.pedidos.find_one({
        "cliente_id": cliente["_id"],
        "productos.sku": "LAP-001"
    })

    if pedido_existente:
        pedido_id = pedido_existente["_id"]
        print("Pedido de prueba existente:", pedido_id)

    else:
        from datetime import datetime, timezone

        pedido = {
            "cliente_id": cliente["_id"],
            "fecha_pedido": datetime.now(timezone.utc),
            "productos": [
                {
                    "producto_id": producto["_id"],
                    "sku": producto["sku"],
                    "nombre": producto["nombre"],
                    "cantidad": 1,
                    "precio_unitario": Decimal128("12500.00"),
                    "subtotal": Decimal128("12500.00")
                }
            ],
            "subtotal": Decimal128("12500.00"),
            "impuestos": Decimal128("0.00"),
            "costo_envio": Decimal128("200.00"),
            "total": Decimal128("12700.00"),
            "estado": "Pendiente",
            "envio": {
                "paqueteria": "DHL",
                "estado": "Pendiente",
                "direccion": cliente["direcciones"][0].copy()
            }
        }

        resultado = db.pedidos.insert_one(pedido)
        pedido_id = resultado.inserted_id
        print("Pedido insertado:", pedido_id)

    # Recuperar el pedido almacenado en MongoDB
    guardado = db.pedidos.find_one({"_id": pedido_id})

    print("\n--- SUBDOCUMENTOS Y ARREGLOS ---")
    print("ID del pedido:", guardado["_id"])
    print("Cliente referenciado:", guardado["cliente_id"])
    print("Cantidad de productos:", len(guardado["productos"]))
    print("Primer producto:", guardado["productos"][0]["nombre"])
    print("Estado del envío:", guardado["envio"]["estado"])
    print("Total:", guardado["total"])

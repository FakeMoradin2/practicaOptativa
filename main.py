
import os
import hashlib
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient
from cifrado import cifrar, descifrar

# Cargar variables de entorno
load_dotenv()

uri = os.getenv("MONGODB_URI")
db_name = os.getenv("DB_NAME")

if not uri or not db_name:
    raise RuntimeError("Faltan variables en el archivo .env")

# Datos ficticios para las pruebas
correo = "cliente@ejemplo.com"
telefono = "3312345678"
calle = "Av. Vallarta"

correo_hash = hashlib.sha256(
    correo.strip().lower().encode("utf-8")
).hexdigest()

# Conexión a MongoDB Atlas
with MongoClient(uri, serverSelectionTimeoutMS=5000) as client:
    client.admin.command("ping")
    db = client[db_name]

    print("Conexión exitosa con MongoDB Atlas")
    print("Base de datos:", db.name)
    print("Colecciones:", db.list_collection_names())

    # Buscar si el cliente ya existe
    cliente_guardado = db.clientes.find_one({
        "correo_hash": correo_hash
    })

    # Insertar solamente si no existe
    if cliente_guardado is None:
        cliente = {
            "nombre": "Juan",
            "apellidos": "Perez Lopez",
            "correo_hash": correo_hash,
            "correo_cifrado": cifrar(correo),
            "telefono_cifrado": cifrar(telefono),
            "direcciones": [
                {
                    "calle": cifrar(calle),
                    "ciudad": "Guadalajara",
                    "estado": "Jalisco",
                    "codigo_postal": "44160"
                }
            ],
            "fecha_registro": datetime.now(timezone.utc),
            "activo": True
        }

        resultado = db.clientes.insert_one(cliente)
        print("Cliente insertado:", resultado.inserted_id)

        cliente_guardado = db.clientes.find_one({
            "_id": resultado.inserted_id
        })

    else:
        print("El cliente de prueba ya existe.")
        print("ID:", cliente_guardado["_id"])

    # Proteger la dirección existente si aún está en texto plano
    direccion = cliente_guardado["direcciones"][0]
    calle_guardada = direccion["calle"]

    try:
        calle_descifrada = descifrar(calle_guardada)

    except Exception:
        # El cliente de prueba anterior guardaba la calle sin cifrar
        if calle_guardada != calle:
            raise RuntimeError(
                "La dirección tiene un valor inesperado; "
                "no se modificará automáticamente."
            )

        db.clientes.update_one(
            {"_id": cliente_guardado["_id"]},
            {"$set": {"direcciones.0.calle": cifrar(calle)}}
        )

        print("Dirección cifrada correctamente")
        calle_descifrada = calle

    # Recuperar el documento actualizado
    cliente_guardado = db.clientes.find_one({
        "correo_hash": correo_hash
    })

    # Demostrar el descifrado
    print("\n--- VERIFICACIÓN DE CIFRADO ---")

    print(
        "Correo descifrado:",
        descifrar(cliente_guardado["correo_cifrado"])
    )

    print(
        "Teléfono descifrado:",
        descifrar(cliente_guardado["telefono_cifrado"])
    )

    print("Calle descifrada:", calle_descifrada)

    print("\nDatos cifrados en MongoDB:")
    print("Correo:", cliente_guardado["correo_cifrado"])
    print("Teléfono:", cliente_guardado["telefono_cifrado"])
    print("Calle:", cliente_guardado["direcciones"][0]["calle"])

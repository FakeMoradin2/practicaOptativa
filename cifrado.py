from pathlib import Path
from cryptography.fernet import Fernet

RUTA_CLAVE = Path.home() / ".ecommerce-fernet.key"

clave = RUTA_CLAVE.read_bytes()
fernet = Fernet(clave)


def cifrar(texto: str) -> str:
    return fernet.encrypt(texto.encode("utf-8")).decode("utf-8")


def descifrar(texto_cifrado: str) -> str:
    return fernet.decrypt(
        texto_cifrado.encode("utf-8")
    ).decode("utf-8")
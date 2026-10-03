"""Configuración de la aplicación.

Lee las variables de entorno definidas en ``backend/.env`` (copia de
``.env.example``). Los valores por defecto están pensados para desarrollo
local con SQLite; en producción (Render) todo llega por variables de entorno.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# backend/  (el archivo config.py vive en backend/app/)
BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"

# Carga backend/.env si existe. En producción no hay archivo: las variables
# las inyecta la plataforma.
load_dotenv(BASE_DIR / ".env")


def _normalizar_url(url: str) -> str:
    """Render entrega la URL como ``postgres://``; SQLAlchemy 2 exige
    ``postgresql://``. Sin esta corrección el despliegue falla al conectar."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _url_base_datos() -> str:
    """SQLite en desarrollo, PostgreSQL en producción."""
    url = os.getenv("DATABASE_URL")
    if url:
        return _normalizar_url(url)
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{INSTANCE_DIR / 'muebleria.db'}"


class Config:
    """Configuración base, compartida por desarrollo y producción."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-cambiar-en-produccion")

    # --- JWT ---
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "dev-jwt-secret-key-for-local-development-only"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_HORAS", "12")))
    # El rol viaja dentro del token; identificamos al usuario con su id.
    JWT_IDENTITY_CLAIM = "sub"

    # --- Base de datos ---
    SQLALCHEMY_DATABASE_URI = _url_base_datos()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Evita que una conexión muerta de PostgreSQL tumbe la API en Render.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- CORS ---
    # Lista separada por comas: "http://localhost:5173,https://miapp.onrender.com"
    CORS_ORIGINS = [
        origen.strip()
        for origen in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origen.strip()
    ]

    # --- API ---
    JSON_SORT_KEYS = False
    # Zona horaria de operación de la mueblería (para "el día de hoy").
    ZONA_HORARIA = os.getenv("ZONA_HORARIA", "America/Mexico_City")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-secret-key-with-at-least-32-characters"


CONFIGURACIONES = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def obtener_config(nombre: str | None = None):
    """Devuelve la clase de configuración según el entorno."""
    if nombre is None:
        nombre = os.getenv("FLASK_ENV", "development")
    configuracion = CONFIGURACIONES.get(nombre, DevelopmentConfig)
    if configuracion is ProductionConfig:
        faltantes = [
            clave
            for clave in ("SECRET_KEY", "JWT_SECRET_KEY")
            if not os.getenv(clave)
        ]
        if faltantes:
            raise RuntimeError(
                "Faltan variables obligatorias de producción: "
                + ", ".join(faltantes)
            )
    return configuracion

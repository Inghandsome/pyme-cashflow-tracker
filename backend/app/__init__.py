"""Fábrica de la aplicación Flask.

Se usa el patrón *application factory* para que las pruebas puedan crear una
app con configuración distinta (base de datos en memoria) sin tocar el código.
"""

import click
from flask import Flask

from app.config import obtener_config
from app.extensions import cors, db, jwt, migrate
from app.utils.respuestas import error

VERSION_API = "0.1.0"


def crear_app(nombre_config: str | None = None) -> Flask:
    """Construye y configura la aplicación."""
    app = Flask(__name__)
    app.config.from_object(obtener_config(nombre_config))

    _inicializar_extensiones(app)
    _registrar_manejadores_jwt()
    _registrar_blueprints(app)
    _registrar_comandos(app)
    _registrar_manejadores_error(app)

    @app.get("/api/salud")
    def salud():
        """Endpoint de salud: lo usa Render para saber si el servicio vive."""
        return {"ok": True, "datos": {"estado": "activo", "version": VERSION_API}}

    return app


def _inicializar_extensiones(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=False,
    )


def _registrar_manejadores_jwt() -> None:
    """Convierte los errores de JWT en respuestas JSON traducidas.

    Sin esto, un token vencido devolvería el HTML de error de Flask en vez del
    formato que el frontend sabe leer.
    """
    from app.models import Usuario

    @jwt.user_lookup_loader
    def cargar_usuario(_cabecera, datos):
        identidad = datos.get("sub")
        return db.session.get(Usuario, int(identidad)) if identidad else None

    @jwt.unauthorized_loader
    def sin_token(_motivo):
        return error("no_autorizado", 401)

    @jwt.invalid_token_loader
    def token_invalido(_motivo):
        return error("token_invalido", 401)

    @jwt.expired_token_loader
    def token_expirado(_cabecera, _datos):
        return error("token_invalido", 401)


def _registrar_blueprints(app: Flask) -> None:
    from app.routes.auth import bp_auth
    from app.routes.categorias import bp_categorias
    from app.routes.dashboard import bp_dashboard
    from app.routes.transacciones import bp_transacciones
    from app.routes.usuarios import bp_usuarios

    app.register_blueprint(bp_auth, url_prefix="/api/auth")
    app.register_blueprint(bp_usuarios, url_prefix="/api/usuarios")
    app.register_blueprint(bp_categorias, url_prefix="/api/categorias")
    app.register_blueprint(bp_transacciones, url_prefix="/api/transacciones")
    app.register_blueprint(bp_dashboard, url_prefix="/api/dashboard")


def _registrar_comandos(app: Flask) -> None:
    """Comandos de consola: ``flask init-db`` y ``flask seed``."""

    @app.cli.command("init-db")
    def init_db():
        """Crea todas las tablas (alternativa rápida a las migraciones)."""
        from app import models  # noqa: F401  (registra los modelos)

        db.create_all()
        click.echo("Base de datos creada.")

    @app.cli.command("seed")
    @click.option(
        "--email",
        default=None,
        help="Correo del dueño. Si se omite, usa el de .env o el de ejemplo.",
    )
    @click.option("--password", default=None, help="Contraseña del dueño.")
    def seed(email, password):
        """Carga la empresa, el dueño y las categorías de la mueblería."""
        from seed_data import sembrar

        resultado = sembrar(email=email, password=password)
        for linea in resultado:
            click.echo(linea)


def _registrar_manejadores_error(app: Flask) -> None:
    """Errores HTTP y excepciones → JSON, nunca HTML."""

    @app.errorhandler(404)
    def no_encontrado(_e):
        return error("no_encontrado", 404)

    @app.errorhandler(405)
    def metodo_no_permitido(_e):
        return error(
            "datos_invalidos", 405, mensaje="El método HTTP no está permitido aquí."
        )

    @app.errorhandler(500)
    def error_interno(_e):
        db.session.rollback()
        return error(
            "datos_invalidos",
            500,
            mensaje="Ocurrió un error inesperado en el servidor.",
        )

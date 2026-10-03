"""Endpoints de autenticación: login, perfil y cambio de contraseña.

Decisión de seguridad: **no hay registro público**. El dueño lo crea el script
de datos semilla (``seed_data.py``) y los cajeros los da de alta el propio
dueño desde ``/api/usuarios``. Así nadie puede crearse una cuenta solo.
"""

from flask import Blueprint, request
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models import ROL_CAJERO, ROL_DUENO, Usuario
from app.utils.decorators import jwt_requerido, usuario_actual
from app.utils.respuestas import error, ok
from app.utils.validacion import DatoInvalido, limpiar_texto, validar_idioma

bp_auth = Blueprint("auth", __name__)


def _serializar_sesion(usuario: Usuario) -> dict:
    """Token + datos del usuario. El rol viaja dentro del token."""
    token = create_access_token(
        identity=str(usuario.id),
        additional_claims={"rol": usuario.rol, "nombre": usuario.nombre},
    )
    return {"token": token, "usuario": usuario.to_dict()}


@bp_auth.post("/login")
def login():
    """Inicia sesión con correo y contraseña."""
    datos = request.get_json(silent=True) or {}
    email = (limpiar_texto(datos.get("email"), 180) or "").lower()
    password = datos.get("password") or ""

    if not email or not password:
        return error("datos_invalidos", 400, detalle={"campos": ["email", "password"]})

    usuario = Usuario.query.filter_by(email=email).first()

    # Un mismo mensaje para "no existe" y "contraseña mal": no le decimos a un
    # atacante qué correos están registrados.
    if not usuario or not usuario.verificar_password(password):
        return error("credenciales_invalidas", 401)

    if not usuario.activo:
        return error("usuario_inactivo", 403)

    return ok(_serializar_sesion(usuario))


@bp_auth.get("/perfil")
@jwt_requerido
def perfil():
    """Datos del usuario con sesión activa (el frontend los usa al recargar)."""
    return ok(usuario_actual().to_dict())


@bp_auth.patch("/perfil")
@jwt_requerido
def actualizar_perfil():
    """Actualiza el nombre o el idioma preferido del propio usuario."""
    usuario = usuario_actual()
    datos = request.get_json(silent=True) or {}

    if "nombre" in datos:
        nombre = limpiar_texto(datos.get("nombre"), 120)
        if not nombre:
            return error("datos_invalidos", 400, detalle={"campo": "nombre"})
        usuario.nombre = nombre

    if "idioma" in datos:
        try:
            usuario.idioma = validar_idioma(datos.get("idioma"))
        except DatoInvalido as exc:
            return error("datos_invalidos", 400, mensaje=str(exc))

    db.session.commit()
    return ok(usuario.to_dict())


@bp_auth.post("/cambiar-password")
@jwt_requerido
def cambiar_password():
    """Cambia la contraseña exigiendo la actual."""
    usuario = usuario_actual()
    datos = request.get_json(silent=True) or {}
    actual = datos.get("password_actual") or ""
    nueva = datos.get("password_nueva") or ""

    if not usuario.verificar_password(actual):
        return error(
            "datos_invalidos",
            400,
            mensaje="La contraseña actual no es correcta."
            if usuario.idioma == "es"
            else "The current password is not correct.",
        )

    if len(nueva) < 8:
        return error(
            "datos_invalidos",
            400,
            mensaje="La contraseña nueva debe tener al menos 8 caracteres."
            if usuario.idioma == "es"
            else "The new password must be at least 8 characters long.",
        )

    usuario.establecer_password(nueva)
    db.session.commit()
    return ok({"actualizado": True})


@bp_auth.get("/roles")
def roles():
    """Catálogo de roles y qué puede hacer cada uno.

    Lo consume el frontend para no duplicar la matriz de permisos en el código
    de React; el backend sigue siendo la autoridad final.
    """
    return ok(
        [
            {
                "clave": ROL_DUENO,
                "nombre": {"es": "Dueño", "en": "Owner"},
                "descripcion": {
                    "es": "Acceso completo: presupuestos, flujo, reportes y usuarios.",
                    "en": "Full access: budgets, cash flow, reports and users.",
                },
            },
            {
                "clave": ROL_CAJERO,
                "nombre": {"es": "Cajero", "en": "Cashier"},
                "descripcion": {
                    "es": "Registra los movimientos del día y ve el resumen diario.",
                    "en": "Records today's transactions and sees the daily summary.",
                },
            },
        ]
    )

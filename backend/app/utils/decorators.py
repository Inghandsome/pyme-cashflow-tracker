"""Decoradores de autorización.

Regla de oro del proyecto: **ninguna restricción de rol vive solo en el
frontend**. Cada endpoint protegido se declara aquí, y si el rol no alcanza la
API responde ``403`` con un mensaje ya traducido.
"""

from functools import wraps

from flask_jwt_extended import current_user, get_jwt, verify_jwt_in_request

from app.models import ROL_DUENO, Usuario
from app.utils.respuestas import error


def jwt_requerido(fn):
    """Exige una sesión válida (cualquier rol activo)."""

    @wraps(fn)
    def envoltura(*args, **kwargs):
        verify_jwt_in_request()
        if not current_user or not current_user.activo:
            return error("usuario_inactivo", 403)
        return fn(*args, **kwargs)

    return envoltura


def rol_requerido(*roles: str):
    """Exige una sesión válida **y** que el rol esté en ``roles``.

    Se verifica el rol contra la base de datos (no solo contra el *claim* del
    token) para que desactivar o cambiar el rol de un usuario surta efecto de
    inmediato, sin esperar a que expire su token.
    """

    def decorador(fn):
        @wraps(fn)
        def envoltura(*args, **kwargs):
            verify_jwt_in_request()
            if not current_user or not current_user.activo:
                return error("usuario_inactivo", 403)

            rol_token = get_jwt().get("rol")
            if current_user.rol not in roles or rol_token not in roles:
                return error("sin_permiso", 403)

            return fn(*args, **kwargs)

        return envoltura

    return decorador


# Atajos legibles para las rutas.
solo_dueno = rol_requerido(ROL_DUENO)


def usuario_actual() -> Usuario:
    """Usuario autenticado de la petición en curso."""
    return current_user

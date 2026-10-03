"""Respuestas JSON estandarizadas para toda la API.

Formato de éxito::

    {"ok": true, "datos": ...}

Formato de error::

    {"ok": false, "error": {"codigo": "no_autorizado",
                            "mensaje": "No tienes permiso...",
                            "detalle": {...}}}

El campo ``mensaje`` se devuelve ya traducido según el idioma solicitado
(cabecera ``Accept-Language`` o parámetro ``?lang=``), de modo que el
frontend pueda mostrarlo tal cual.
"""

from flask import jsonify, request

# Idioma por defecto del sistema.
IDIOMA_POR_DEFECTO = "es"
IDIOMAS_SOPORTADOS = ("es", "en")

# Mensajes de error de la API en ambos idiomas.
MENSAJES = {
    "credenciales_invalidas": {
        "es": "Correo o contraseña incorrectos.",
        "en": "Wrong email or password.",
    },
    "usuario_inactivo": {
        "es": "Tu usuario está desactivado. Pide al dueño que lo reactive.",
        "en": "Your account is disabled. Ask the owner to re-enable it.",
    },
    "no_autorizado": {
        "es": "Necesitas iniciar sesión.",
        "en": "You need to sign in.",
    },
    "sin_permiso": {
        "es": "Tu rol no tiene permiso para esta acción.",
        "en": "Your role is not allowed to perform this action.",
    },
    "token_invalido": {
        "es": "Tu sesión expiró. Vuelve a iniciar sesión.",
        "en": "Your session expired. Please sign in again.",
    },
    "no_encontrado": {
        "es": "No se encontró el recurso solicitado.",
        "en": "The requested resource was not found.",
    },
    "datos_invalidos": {
        "es": "Revisa los datos enviados.",
        "en": "Please check the submitted data.",
    },
    "conflicto": {
        "es": "Ese registro ya existe.",
        "en": "That record already exists.",
    },
    "cajero_solo_hoy": {
        "es": "Como cajero solo puedes registrar movimientos del día de hoy.",
        "en": "As a cashier you can only record today's transactions.",
    },
    "cajero_solo_propias": {
        "es": "Como cajero solo puedes modificar los movimientos que tú registraste hoy.",
        "en": "As a cashier you can only edit the transactions you recorded today.",
    },
}


def idioma_solicitado() -> str:
    """Detecta el idioma pedido en ``?lang=`` o ``Accept-Language``."""
    parametro = (request.args.get("lang") or "").lower()[:2]
    if parametro in IDIOMAS_SOPORTADOS:
        return parametro

    cabecera = (request.headers.get("Accept-Language") or "").lower()
    if cabecera.startswith("en"):
        return "en"

    # Si hay sesión, respetamos la preferencia guardada del usuario.
    try:
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

        from app.models import Usuario

        verify_jwt_in_request(optional=True)
        identidad = get_jwt_identity()
        if identidad:
            usuario = Usuario.query.get(int(identidad))
            if usuario and usuario.idioma in IDIOMAS_SOPORTADOS:
                return usuario.idioma
    except Exception:
        pass

    return IDIOMA_POR_DEFECTO


def traducir(clave: str, idioma: str | None = None) -> str:
    """Devuelve el mensaje ``clave`` en el idioma indicado."""
    idioma = idioma or idioma_solicitado()
    return MENSAJES.get(clave, {}).get(idioma, clave)


def ok(datos=None, codigo_http: int = 200, **extra):
    """Respuesta de éxito."""
    cuerpo = {"ok": True, "datos": datos}
    cuerpo.update(extra)
    return jsonify(cuerpo), codigo_http


def error(clave: str, codigo_http: int = 400, detalle=None, mensaje: str | None = None):
    """Respuesta de error con mensaje traducido."""
    return (
        jsonify(
            {
                "ok": False,
                "error": {
                    "codigo": clave,
                    "mensaje": mensaje or traducir(clave),
                    "detalle": detalle,
                },
            }
        ),
        codigo_http,
    )

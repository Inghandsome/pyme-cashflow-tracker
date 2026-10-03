"""Endpoints de gestión de usuarios. **Exclusivos del dueño.**

El dueño solo puede dar de alta **cajeros**: el sistema está pensado para una
mueblería con un único propietario responsable. Si más adelante se necesitara
un segundo dueño, basta con relajar la validación de ``rol`` aquí.
"""

from flask import Blueprint, request

from app.extensions import db
from app.models import ROL_CAJERO, Usuario
from app.utils.decorators import solo_dueno, usuario_actual
from app.utils.respuestas import error, ok
from app.utils.validacion import DatoInvalido, limpiar_texto, validar_idioma

bp_usuarios = Blueprint("usuarios", __name__)


def _buscar_de_la_empresa(usuario_id: int, empresa_id: int) -> Usuario | None:
    """Busca un usuario asegurando que sea de la misma empresa.

    Evita que alguien con un id manipulado toque datos de otro negocio.
    """
    return Usuario.query.filter_by(id=usuario_id, empresa_id=empresa_id).first()


@bp_usuarios.get("")
@solo_dueno
def listar_usuarios():
    """Lista los cajeros (y el propio dueño) de la empresa."""
    dueno = usuario_actual()
    usuarios = (
        Usuario.query.filter_by(empresa_id=dueno.empresa_id)
        .order_by(Usuario.rol.desc(), Usuario.nombre)
        .all()
    )
    return ok([usuario.to_dict() for usuario in usuarios])


@bp_usuarios.post("")
@solo_dueno
def crear_usuario():
    """Da de alta un cajero."""
    dueno = usuario_actual()
    datos = request.get_json(silent=True) or {}

    nombre = limpiar_texto(datos.get("nombre"), 120)
    email = (limpiar_texto(datos.get("email"), 180) or "").lower()
    password = datos.get("password") or ""

    if not nombre or not email or len(password) < 8:
        return error(
            "datos_invalidos",
            400,
            detalle={
                "requisitos": "nombre, email y password (mínimo 8 caracteres)"
            },
        )

    rol = (limpiar_texto(datos.get("rol"), 20) or ROL_CAJERO).lower()
    if rol != ROL_CAJERO:
        return error(
            "datos_invalidos",
            400,
            mensaje="Solo se pueden crear usuarios con rol de cajero.",
        )

    if Usuario.query.filter_by(email=email).first():
        return error("conflicto", 409, detalle={"campo": "email"})

    try:
        idioma = validar_idioma(datos.get("idioma", "es"))
    except DatoInvalido as exc:
        return error("datos_invalidos", 400, mensaje=str(exc))

    usuario = Usuario(
        nombre=nombre,
        email=email,
        rol=ROL_CAJERO,
        idioma=idioma,
        empresa_id=dueno.empresa_id,
    )
    usuario.establecer_password(password)

    db.session.add(usuario)
    db.session.commit()

    return ok(usuario.to_dict(), 201)


@bp_usuarios.patch("/<int:usuario_id>")
@solo_dueno
def actualizar_usuario(usuario_id: int):
    """Edita un cajero: nombre, idioma, reactivar/desactivar o resetear clave."""
    dueno = usuario_actual()
    usuario = _buscar_de_la_empresa(usuario_id, dueno.empresa_id)

    if not usuario:
        return error("no_encontrado", 404)

    if usuario.es_dueno:
        return error(
            "datos_invalidos",
            400,
            mensaje="El usuario dueño no se edita desde este endpoint.",
        )

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

    if "activo" in datos:
        usuario.activo = bool(datos.get("activo"))

    # El dueño puede resetear la contraseña de un cajero que la olvidó.
    if datos.get("password"):
        nueva = datos["password"]
        if len(nueva) < 8:
            return error(
                "datos_invalidos",
                400,
                mensaje="La contraseña debe tener al menos 8 caracteres.",
            )
        usuario.establecer_password(nueva)

    db.session.commit()
    return ok(usuario.to_dict())


@bp_usuarios.delete("/<int:usuario_id>")
@solo_dueno
def desactivar_usuario(usuario_id: int):
    """Desactiva un cajero.

    No se borra la fila a propósito: sus transacciones guardan ``usuario_id`` y
    borrarlo dejaría movimientos huérfanos, perdiendo la auditoría de quién
    capturó qué.
    """
    dueno = usuario_actual()
    usuario = _buscar_de_la_empresa(usuario_id, dueno.empresa_id)

    if not usuario:
        return error("no_encontrado", 404)

    if usuario.es_dueno or usuario.id == dueno.id:
        return error(
            "datos_invalidos",
            400,
            mensaje="No puedes desactivar tu propio usuario de dueño.",
        )

    usuario.activo = False
    db.session.commit()

    return ok({"id": usuario.id, "activo": False, "accion": "desactivado"})

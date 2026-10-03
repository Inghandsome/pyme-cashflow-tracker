"""Endpoints de categorías.

Leer categorías lo puede hacer **cualquier rol** (el cajero las necesita para
registrar un movimiento). Crear, editar y borrar es **solo del dueño**.
"""

from flask import Blueprint, request

from app.extensions import db
from app.models import Categoria, Transaccion
from app.models.categoria import TIPOS_CATEGORIA
from app.utils.decorators import jwt_requerido, solo_dueno, usuario_actual
from app.utils.respuestas import error, idioma_solicitado, ok
from app.utils.validacion import DatoInvalido, limpiar_texto

bp_categorias = Blueprint("categorias", __name__)


def _categoria_de_la_empresa(categoria_id: int, empresa_id: int) -> Categoria | None:
    return Categoria.query.filter_by(id=categoria_id, empresa_id=empresa_id).first()


@bp_categorias.get("")
@jwt_requerido
def listar_categorias():
    """Lista las categorías de la empresa.

    Parámetros:
        ``tipo``              → ``ingreso`` o ``egreso``
        ``incluir_inactivas`` → ``true`` para traer también las desactivadas
    """
    usuario = usuario_actual()
    idioma = idioma_solicitado()

    consulta = Categoria.query.filter_by(empresa_id=usuario.empresa_id)

    tipo = (request.args.get("tipo") or "").strip().lower()
    if tipo:
        if tipo not in TIPOS_CATEGORIA:
            return error("datos_invalidos", 400, detalle={"campo": "tipo"})
        consulta = consulta.filter(Categoria.tipo == tipo)

    incluir_inactivas = (request.args.get("incluir_inactivas") or "").lower() in (
        "1",
        "true",
        "si",
        "sí",
    )
    if not incluir_inactivas:
        consulta = consulta.filter(Categoria.activa.is_(True))

    categorias = consulta.order_by(Categoria.tipo, Categoria.nombre).all()
    return ok([categoria.to_dict(idioma) for categoria in categorias])


@bp_categorias.post("")
@solo_dueno
def crear_categoria():
    """Crea una categoría nueva."""
    dueno = usuario_actual()
    datos = request.get_json(silent=True) or {}

    nombre = limpiar_texto(datos.get("nombre"), 120)
    tipo = (limpiar_texto(datos.get("tipo"), 10) or "").lower()

    if not nombre or tipo not in TIPOS_CATEGORIA:
        return error(
            "datos_invalidos",
            400,
            detalle={"requisitos": "nombre y tipo ('ingreso' o 'egreso')"},
        )

    existe = Categoria.query.filter_by(
        empresa_id=dueno.empresa_id, nombre=nombre, tipo=tipo
    ).first()
    if existe:
        return error("conflicto", 409, detalle={"campo": "nombre"})

    categoria = Categoria(
        nombre=nombre,
        nombre_en=limpiar_texto(datos.get("nombre_en"), 120),
        tipo=tipo,
        icono=limpiar_texto(datos.get("icono"), 16),
        color=limpiar_texto(datos.get("color"), 20),
        empresa_id=dueno.empresa_id,
    )

    db.session.add(categoria)
    db.session.commit()

    return ok(categoria.to_dict(idioma_solicitado()), 201)


@bp_categorias.patch("/<int:categoria_id>")
@solo_dueno
def actualizar_categoria(categoria_id: int):
    """Edita nombre, traducción, ícono, color o reactiva la categoría."""
    dueno = usuario_actual()
    categoria = _categoria_de_la_empresa(categoria_id, dueno.empresa_id)

    if not categoria:
        return error("no_encontrado", 404)

    datos = request.get_json(silent=True) or {}

    if "nombre" in datos:
        nombre = limpiar_texto(datos.get("nombre"), 120)
        if not nombre:
            return error("datos_invalidos", 400, detalle={"campo": "nombre"})
        categoria.nombre = nombre

    for campo in ("nombre_en", "icono", "color"):
        if campo in datos:
            setattr(categoria, campo, limpiar_texto(datos.get(campo), 120))

    if "tipo" in datos:
        try:
            tipo = limpiar_texto(datos.get("tipo"), 10).lower()
        except AttributeError:
            tipo = ""
        if tipo not in TIPOS_CATEGORIA:
            return error("datos_invalidos", 400, detalle={"campo": "tipo"})
        categoria.tipo = tipo

    if "activa" in datos:
        categoria.activa = bool(datos.get("activa"))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error("conflicto", 409)

    return ok(categoria.to_dict(idioma_solicitado()))


@bp_categorias.delete("/<int:categoria_id>")
@solo_dueno
def eliminar_categoria(categoria_id: int):
    """Desactiva la categoría; solo la borra si nunca se usó.

    Igual que con los usuarios, borrar una categoría con movimientos dejaría
    las transacciones sin clasificar y rompería los reportes históricos.
    """
    dueno = usuario_actual()
    categoria = _categoria_de_la_empresa(categoria_id, dueno.empresa_id)

    if not categoria:
        return error("no_encontrado", 404)

    tiene_movimientos = (
        Transaccion.query.filter_by(categoria_id=categoria.id).count() > 0
    )

    if tiene_movimientos:
        categoria.activa = False
        db.session.commit()
        return ok(
            {
                "id": categoria.id,
                "activa": False,
                "accion": "desactivada",
                "motivo": "La categoría tiene movimientos registrados; se conserva el historial.",
            }
        )

    db.session.delete(categoria)
    db.session.commit()

    return ok({"id": categoria_id, "accion": "eliminada"})

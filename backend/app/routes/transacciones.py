"""Endpoints de transacciones: el dinero que entra y el que sale.

Aquí vive la restricción central del rol **cajero**, y se aplica en el
servidor, no en el navegador:

1. Solo puede registrar movimientos con la fecha de **hoy**.
2. Solo ve los movimientos de **hoy** (aunque pida otro rango de fechas).
3. Solo puede editar o borrar los que **él mismo** registró hoy.

El dueño no tiene ninguna de esas restricciones.
"""

from flask import Blueprint, request
from sqlalchemy import func, or_

from app.extensions import db
from app.models import Categoria, Transaccion
from app.models.transaccion import TIPO_EGRESO, TIPO_INGRESO
from app.utils.decorators import jwt_requerido, usuario_actual
from app.utils.fechas import hoy_local
from app.utils.respuestas import error, idioma_solicitado, ok
from app.utils.validacion import (
    DatoInvalido,
    a_decimal,
    a_entero,
    a_fecha,
    limpiar_texto,
    validar_metodo_pago,
    validar_tipo_movimiento,
)

bp_transacciones = Blueprint("transacciones", __name__)

LIMITE_POR_DEFECTO = 100
LIMITE_MAXIMO = 500


# ─────────────────────────── ayudas internas ───────────────────────────


def _validar_categoria(categoria_id, tipo: str, empresa_id: int) -> Categoria:
    """La categoría debe existir, ser de la empresa y corresponder al tipo."""
    categoria = Categoria.query.filter_by(
        id=categoria_id, empresa_id=empresa_id
    ).first()

    if not categoria:
        raise DatoInvalido("La categoría indicada no existe.")

    if categoria.tipo != tipo:
        raise DatoInvalido(
            "La categoría no corresponde al tipo de movimiento: "
            f"una categoría de {categoria.tipo} no sirve para un {tipo}."
        )

    if not categoria.activa:
        raise DatoInvalido("La categoría está desactivada.")

    return categoria


def _totales(consulta) -> dict:
    """Suma ingresos y egresos de una consulta ya filtrada."""
    ingresos = (
        consulta.filter(Transaccion.tipo == TIPO_INGRESO)
        .with_entities(func.coalesce(func.sum(Transaccion.monto), 0))
        .scalar()
    )
    egresos = (
        consulta.filter(Transaccion.tipo == TIPO_EGRESO)
        .with_entities(func.coalesce(func.sum(Transaccion.monto), 0))
        .scalar()
    )

    total_ingresos = float(ingresos or 0)
    total_egresos = float(egresos or 0)

    return {
        "ingresos": round(total_ingresos, 2),
        "egresos": round(total_egresos, 2),
        "saldo": round(total_ingresos - total_egresos, 2),
    }


def _consulta_base(usuario):
    """Consulta de transacciones de la empresa, ya acotada por rol."""
    consulta = Transaccion.query.filter_by(empresa_id=usuario.empresa_id)

    # Un cajero nunca sale del día de hoy, pase lo que pase con los filtros.
    if usuario.es_cajero:
        consulta = consulta.filter(Transaccion.fecha == hoy_local())

    return consulta


# ─────────────────────────────── endpoints ───────────────────────────────


@bp_transacciones.get("")
@jwt_requerido
def listar_transacciones():
    """Lista movimientos con filtros.

    Filtros disponibles (solo para el dueño): ``tipo``, ``categoria_id``,
    ``desde``, ``hasta``, ``metodo_pago``, ``usuario_id``, ``buscar``,
    ``limite`` y ``desplazamiento``.
    """
    usuario = usuario_actual()
    idioma = idioma_solicitado()
    consulta = _consulta_base(usuario)

    if usuario.es_dueno:
        tipo = (request.args.get("tipo") or "").strip().lower()
        if tipo:
            try:
                consulta = consulta.filter(
                    Transaccion.tipo == validar_tipo_movimiento(tipo)
                )
            except DatoInvalido as exc:
                return error("datos_invalidos", 400, mensaje=str(exc))

        if request.args.get("categoria_id"):
            try:
                consulta = consulta.filter(
                    Transaccion.categoria_id
                    == a_entero(request.args.get("categoria_id"), "categoria_id")
                )
            except DatoInvalido as exc:
                return error("datos_invalidos", 400, mensaje=str(exc))

        if request.args.get("usuario_id"):
            try:
                consulta = consulta.filter(
                    Transaccion.usuario_id
                    == a_entero(request.args.get("usuario_id"), "usuario_id")
                )
            except DatoInvalido as exc:
                return error("datos_invalidos", 400, mensaje=str(exc))

        if request.args.get("metodo_pago"):
            try:
                consulta = consulta.filter(
                    Transaccion.metodo_pago
                    == validar_metodo_pago(request.args.get("metodo_pago"))
                )
            except DatoInvalido as exc:
                return error("datos_invalidos", 400, mensaje=str(exc))

        for parametro, operador in (("desde", ">="), ("hasta", "<=")):
            if request.args.get(parametro):
                try:
                    fecha = a_fecha(request.args.get(parametro), parametro)
                except DatoInvalido as exc:
                    return error("datos_invalidos", 400, mensaje=str(exc))
                columna = Transaccion.fecha
                consulta = consulta.filter(
                    columna >= fecha if operador == ">=" else columna <= fecha
                )

        buscar = limpiar_texto(request.args.get("buscar"), 120)
        if buscar:
            patron = f"%{buscar}%"
            consulta = consulta.filter(
                or_(
                    Transaccion.descripcion.ilike(patron),
                    Categoria.nombre.ilike(patron),
                    Categoria.nombre_en.ilike(patron),
                )
            ).join(Categoria, Transaccion.categoria_id == Categoria.id)

    totales = _totales(consulta)

    try:
        limite = min(
            a_entero(request.args.get("limite", LIMITE_POR_DEFECTO), "limite"),
            LIMITE_MAXIMO,
        )
        desplazamiento = a_entero(
            request.args.get("desplazamiento", 0), "desplazamiento"
        )
    except DatoInvalido as exc:
        return error("datos_invalidos", 400, mensaje=str(exc))

    total = consulta.count()
    movimientos = (
        consulta.order_by(Transaccion.fecha.desc(), Transaccion.id.desc())
        .offset(max(desplazamiento, 0))
        .limit(max(limite, 1))
        .all()
    )

    return ok(
        {
            "transacciones": [mov.to_dict(idioma) for mov in movimientos],
            "totales": totales,
            "total_registros": total,
            "solo_hoy": usuario.es_cajero,
            "fecha": hoy_local().isoformat(),
        }
    )


@bp_transacciones.get("/resumen-dia")
@jwt_requerido
def resumen_dia():
    """Resumen del día: lo que ve el cajero al entrar.

    Es el único panorama financiero al que tiene acceso el cajero: cuánto
    entró, cuánto salió y el saldo del día.
    """
    usuario = usuario_actual()
    idioma = idioma_solicitado()
    hoy = hoy_local()

    consulta = Transaccion.query.filter_by(
        empresa_id=usuario.empresa_id, fecha=hoy
    )
    totales = _totales(consulta)

    ultimos = (
        consulta.order_by(Transaccion.id.desc()).limit(10).all()
    )

    return ok(
        {
            "fecha": hoy.isoformat(),
            "totales": totales,
            "cantidad_movimientos": consulta.count(),
            "ultimos_movimientos": [mov.to_dict(idioma) for mov in ultimos],
            "rol": usuario.rol,
        }
    )


@bp_transacciones.post("")
@jwt_requerido
def crear_transaccion():
    """Registra un movimiento.

    El cajero solo puede usar la fecha de hoy: si intenta registrar un
    movimiento con fecha pasada o futura, se rechaza con 403.
    """
    usuario = usuario_actual()
    idioma = idioma_solicitado()
    datos = request.get_json(silent=True) or {}
    hoy = hoy_local()

    try:
        monto = a_decimal(datos.get("monto"), "monto")
        tipo = validar_tipo_movimiento(datos.get("tipo"))
        metodo_pago = validar_metodo_pago(datos.get("metodo_pago"))
        categoria_id = a_entero(datos.get("categoria_id"), "categoria_id")
    except DatoInvalido as exc:
        return error("datos_invalidos", 400, mensaje=str(exc))

    # --- Regla del cajero: la fecha es siempre hoy ---
    if usuario.es_cajero:
        if datos.get("fecha"):
            try:
                if a_fecha(datos.get("fecha")) != hoy:
                    return error("cajero_solo_hoy", 403)
            except DatoInvalido as exc:
                return error("datos_invalidos", 400, mensaje=str(exc))
        fecha = hoy
    else:
        try:
            fecha = a_fecha(datos.get("fecha"), "fecha") if datos.get("fecha") else hoy
        except DatoInvalido as exc:
            return error("datos_invalidos", 400, mensaje=str(exc))

    try:
        _validar_categoria(categoria_id, tipo, usuario.empresa_id)
    except DatoInvalido as exc:
        return error("datos_invalidos", 400, mensaje=str(exc))

    transaccion = Transaccion(
        monto=monto,
        tipo=tipo,
        descripcion=limpiar_texto(datos.get("descripcion"), 250),
        fecha=fecha,
        metodo_pago=metodo_pago,
        categoria_id=categoria_id,
        empresa_id=usuario.empresa_id,
        usuario_id=usuario.id,
    )

    db.session.add(transaccion)
    db.session.commit()

    return ok(transaccion.to_dict(idioma), 201)


@bp_transacciones.patch("/<int:transaccion_id>")
@jwt_requerido
def actualizar_transaccion(transaccion_id: int):
    """Edita un movimiento respetando el alcance del rol."""
    usuario = usuario_actual()
    idioma = idioma_solicitado()

    transaccion = Transaccion.query.filter_by(
        id=transaccion_id, empresa_id=usuario.empresa_id
    ).first()

    if not transaccion:
        return error("no_encontrado", 404)

    # El cajero solo toca lo suyo y solo de hoy.
    if usuario.es_cajero and (
        transaccion.usuario_id != usuario.id or transaccion.fecha != hoy_local()
    ):
        return error("cajero_solo_propias", 403)

    datos = request.get_json(silent=True) or {}
    hoy = hoy_local()

    if "monto" in datos:
        try:
            transaccion.monto = a_decimal(datos.get("monto"), "monto")
        except DatoInvalido as exc:
            return error("datos_invalidos", 400, mensaje=str(exc))

    if "tipo" in datos:
        try:
            transaccion.tipo = validar_tipo_movimiento(datos.get("tipo"))
        except DatoInvalido as exc:
            return error("datos_invalidos", 400, mensaje=str(exc))

    if "metodo_pago" in datos:
        try:
            transaccion.metodo_pago = validar_metodo_pago(datos.get("metodo_pago"))
        except DatoInvalido as exc:
            return error("datos_invalidos", 400, mensaje=str(exc))

    if "descripcion" in datos:
        transaccion.descripcion = limpiar_texto(datos.get("descripcion"), 250)

    if "categoria_id" in datos:
        try:
            categoria_id = a_entero(datos.get("categoria_id"), "categoria_id")
            _validar_categoria(categoria_id, transaccion.tipo, usuario.empresa_id)
            transaccion.categoria_id = categoria_id
        except DatoInvalido as exc:
            return error("datos_invalidos", 400, mensaje=str(exc))

    if "fecha" in datos:
        # El cajero no puede mover un movimiento a otro día.
        if usuario.es_cajero:
            return error("cajero_solo_hoy", 403)
        try:
            transaccion.fecha = a_fecha(datos.get("fecha"), "fecha")
        except DatoInvalido as exc:
            return error("datos_invalidos", 400, mensaje=str(exc))

    # Si cambió el tipo, la categoría anterior puede quedar inconsistente.
    try:
        _validar_categoria(
            transaccion.categoria_id, transaccion.tipo, usuario.empresa_id
        )
    except DatoInvalido as exc:
        return error("datos_invalidos", 400, mensaje=str(exc))

    db.session.commit()
    return ok(transaccion.to_dict(idioma))


@bp_transacciones.delete("/<int:transaccion_id>")
@jwt_requerido
def eliminar_transaccion(transaccion_id: int):
    """Borra un movimiento. El cajero solo puede borrar los suyos de hoy."""
    usuario = usuario_actual()

    transaccion = Transaccion.query.filter_by(
        id=transaccion_id, empresa_id=usuario.empresa_id
    ).first()

    if not transaccion:
        return error("no_encontrado", 404)

    if usuario.es_cajero and (
        transaccion.usuario_id != usuario.id or transaccion.fecha != hoy_local()
    ):
        return error("cajero_solo_propias", 403)

    db.session.delete(transaccion)
    db.session.commit()

    return ok({"id": transaccion_id, "accion": "eliminada"})

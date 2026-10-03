"""Resumen consolidado para las tarjetas principales del frontend."""

from datetime import date, timedelta

from flask import Blueprint
from sqlalchemy import func

from app.models import CuentaCobrarPagar, Transaccion
from app.models.cuenta_cobrar_pagar import CUENTA_COBRAR, ESTADO_PAGADA
from app.models.transaccion import TIPO_EGRESO, TIPO_INGRESO
from app.utils.decorators import jwt_requerido, usuario_actual
from app.utils.fechas import hoy_local
from app.utils.respuestas import idioma_solicitado, ok

bp_dashboard = Blueprint("dashboard", __name__)


def _totales(consulta) -> dict:
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


@bp_dashboard.get("/resumen")
@jwt_requerido
def resumen_dashboard():
    """Devuelve datos reales acotados al alcance del rol autenticado."""
    usuario = usuario_actual()
    hoy = hoy_local()
    es_dueno = usuario.es_dueno
    desde = date(hoy.year, hoy.month, 1) if es_dueno else hoy

    consulta = (
        Transaccion.query.filter_by(empresa_id=usuario.empresa_id)
        .filter(Transaccion.fecha >= desde, Transaccion.fecha <= hoy)
    )
    movimientos = consulta.order_by(
        Transaccion.fecha.desc(), Transaccion.id.desc()
    ).limit(8).all()

    datos = {
        "rol": usuario.rol,
        "fecha": hoy.isoformat(),
        "periodo": {
            "tipo": "mes" if es_dueno else "dia",
            "desde": desde.isoformat(),
            "hasta": hoy.isoformat(),
        },
        "totales": _totales(consulta),
        "cantidad_movimientos": consulta.count(),
        "actividad": [
            movimiento.to_dict(idioma_solicitado())
            for movimiento in movimientos
        ],
        "flujo_diario": [],
        "cuentas_por_cobrar": None,
    }

    if es_dueno:
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        dias = {
            inicio_semana + timedelta(days=indice): {
                "fecha": (inicio_semana + timedelta(days=indice)).isoformat(),
                "ingresos": 0.0,
                "egresos": 0.0,
            }
            for indice in range(7)
        }
        movimientos_semana = Transaccion.query.filter(
            Transaccion.empresa_id == usuario.empresa_id,
            Transaccion.fecha >= inicio_semana,
            Transaccion.fecha <= hoy,
        ).all()
        for movimiento in movimientos_semana:
            clave = (
                "ingresos" if movimiento.tipo == TIPO_INGRESO else "egresos"
            )
            dias[movimiento.fecha][clave] += float(movimiento.monto or 0)
        datos["flujo_diario"] = [
            {
                **dia,
                "ingresos": round(dia["ingresos"], 2),
                "egresos": round(dia["egresos"], 2),
            }
            for dia in dias.values()
        ]

        cuentas_abiertas = CuentaCobrarPagar.query.filter(
            CuentaCobrarPagar.empresa_id == usuario.empresa_id,
            CuentaCobrarPagar.tipo == CUENTA_COBRAR,
            CuentaCobrarPagar.estado != ESTADO_PAGADA,
            CuentaCobrarPagar.monto_total > CuentaCobrarPagar.monto_pagado,
        )
        saldo_pendiente = cuentas_abiertas.with_entities(
            func.coalesce(
                func.sum(
                    CuentaCobrarPagar.monto_total
                    - CuentaCobrarPagar.monto_pagado
                ),
                0,
            )
        ).scalar()
        datos["cuentas_por_cobrar"] = {
            "saldo": round(float(saldo_pendiente or 0), 2),
            "abiertas": cuentas_abiertas.count(),
        }

    return ok(datos)

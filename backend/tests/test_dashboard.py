from datetime import timedelta

import pytest

from app import crear_app
from app.extensions import db
from app.models import Categoria, CuentaCobrarPagar, Transaccion, Usuario
from app.models.cuenta_cobrar_pagar import CUENTA_COBRAR, ESTADO_PARCIAL
from app.models.transaccion import TIPO_EGRESO, TIPO_INGRESO
from app.utils.fechas import hoy_local
from seed_data import sembrar


@pytest.fixture
def app():
    application = crear_app("testing")
    with application.app_context():
        db.create_all()
        sembrar(email="owner@example.com", password="OwnerPass123")
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _auth_headers(client, email, password):
    response = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200
    token = response.get_json()["datos"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_owner_returns_totals_weekly_flow_and_receivables(app, client):
    with app.app_context():
        owner = Usuario.query.filter_by(email="owner@example.com").first()
        income_category = Categoria.query.filter_by(tipo=TIPO_INGRESO).first()
        expense_category = Categoria.query.filter_by(tipo=TIPO_EGRESO).first()
        db.session.add_all(
            [
                Transaccion(
                    monto=1500,
                    tipo=TIPO_INGRESO,
                    descripcion="Order deposit",
                    fecha=hoy_local(),
                    categoria_id=income_category.id,
                    empresa_id=owner.empresa_id,
                    usuario_id=owner.id,
                ),
                Transaccion(
                    monto=350,
                    tipo=TIPO_EGRESO,
                    descripcion="Lumber",
                    fecha=hoy_local(),
                    categoria_id=expense_category.id,
                    empresa_id=owner.empresa_id,
                    usuario_id=owner.id,
                ),
                CuentaCobrarPagar(
                    tipo=CUENTA_COBRAR,
                    persona_nombre="Customer",
                    monto_total=5000,
                    monto_pagado=1000,
                    estado=ESTADO_PARCIAL,
                    empresa_id=owner.empresa_id,
                ),
            ]
        )
        db.session.commit()

    response = client.get(
        "/api/dashboard/resumen",
        headers=_auth_headers(client, "owner@example.com", "OwnerPass123"),
    )
    assert response.status_code == 200
    datos = response.get_json()["datos"]
    assert datos["totales"] == {
        "ingresos": 1500.0,
        "egresos": 350.0,
        "saldo": 1150.0,
    }
    assert datos["cuentas_por_cobrar"] == {"saldo": 4000.0, "abiertas": 1}
    assert len(datos["flujo_diario"]) == 7
    assert len(datos["actividad"]) == 2


def test_cashier_dashboard_is_limited_to_today_and_cannot_edit_categories(
    app, client
):
    owner_headers = _auth_headers(client, "owner@example.com", "OwnerPass123")
    created = client.post(
        "/api/usuarios",
        headers=owner_headers,
        json={
            "nombre": "Cashier",
            "email": "cashier@example.com",
            "password": "CashierPass123",
        },
    )
    assert created.status_code == 201

    with app.app_context():
        owner = Usuario.query.filter_by(email="owner@example.com").first()
        category = Categoria.query.filter_by(tipo=TIPO_INGRESO).first()
        db.session.add(
            Transaccion(
                monto=2500,
                tipo=TIPO_INGRESO,
                descripcion="Yesterday deposit",
                fecha=hoy_local() - timedelta(days=1),
                categoria_id=category.id,
                empresa_id=owner.empresa_id,
                usuario_id=owner.id,
            )
        )
        db.session.commit()

    cashier_headers = _auth_headers(
        client, "cashier@example.com", "CashierPass123"
    )
    summary = client.get("/api/dashboard/resumen", headers=cashier_headers)
    assert summary.status_code == 200
    datos = summary.get_json()["datos"]
    assert datos["periodo"]["tipo"] == "dia"
    assert datos["cantidad_movimientos"] == 0
    assert datos["cuentas_por_cobrar"] is None
    assert datos["flujo_diario"] == []

    categories = client.post(
        "/api/categorias",
        headers=cashier_headers,
        json={"nombre": "Not allowed", "tipo": "egreso"},
    )
    assert categories.status_code == 403
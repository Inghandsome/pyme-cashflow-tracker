"""Modelo de cuentas por cobrar y por pagar (fiados, anticipos y proveedores).

En una mueblería este módulo es central: un cliente aparta un pedido con
anticipo y liquida el resto a la entrega, y a su vez el taller queda a deber
materia prima a los proveedores.
"""

from app.extensions import db
from app.utils.fechas import ahora_utc, hoy_local

# --- Tipo de cuenta ---
CUENTA_COBRAR = "cobrar"
CUENTA_PAGAR = "pagar"
TIPOS_CUENTA = (CUENTA_COBRAR, CUENTA_PAGAR)

# --- Estados ---
ESTADO_PENDIENTE = "pendiente"
ESTADO_PARCIAL = "parcial"
ESTADO_PAGADA = "pagada"
ESTADO_VENCIDA = "vencida"
ESTADOS_CUENTA = (ESTADO_PENDIENTE, ESTADO_PARCIAL, ESTADO_PAGADA, ESTADO_VENCIDA)


class CuentaCobrarPagar(db.Model):
    """Una deuda: lo que un cliente debe (cobrar) o lo que debemos (pagar)."""

    __tablename__ = "cuenta_cobrar_pagar"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False, index=True)
    persona_nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(250))
    monto_total = db.Column(db.Numeric(12, 2), nullable=False)
    monto_pagado = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    fecha_vencimiento = db.Column(db.Date, index=True)
    estado = db.Column(
        db.String(12), nullable=False, default=ESTADO_PENDIENTE, index=True
    )
    empresa_id = db.Column(
        db.Integer, db.ForeignKey("empresa.id"), nullable=False, index=True
    )
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=ahora_utc)

    pagos = db.relationship(
        "PagoCuenta",
        back_populates="cuenta",
        cascade="all, delete-orphan",
        order_by="PagoCuenta.fecha_pago",
    )

    @property
    def saldo(self) -> float:
        """Cuánto falta por cobrar o pagar."""
        return round(float(self.monto_total or 0) - float(self.monto_pagado or 0), 2)

    @property
    def esta_liquidada(self) -> bool:
        return self.saldo <= 0

    def actualizar_estado(self) -> str:
        """Recalcula el estado a partir de los abonos y la fecha límite.

        Orden de prioridad: pagada > vencida > parcial > pendiente.
        """
        pagado = float(self.monto_pagado or 0)

        if self.esta_liquidada:
            self.estado = ESTADO_PAGADA
        elif self.fecha_vencimiento and self.fecha_vencimiento < hoy_local():
            self.estado = ESTADO_VENCIDA
        elif pagado > 0:
            self.estado = ESTADO_PARCIAL
        else:
            self.estado = ESTADO_PENDIENTE

        return self.estado

    def registrar_pago(self, monto: float, fecha_pago=None, notas: str | None = None):
        """Aplica un abono y deja el estado consistente."""
        pago = PagoCuenta(
            monto=monto,
            fecha_pago=fecha_pago or hoy_local(),
            notas=notas,
        )
        self.pagos.append(pago)
        self.monto_pagado = float(self.monto_pagado or 0) + float(monto)
        self.actualizar_estado()
        return pago

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "persona_nombre": self.persona_nombre,
            "descripcion": self.descripcion,
            "monto_total": float(self.monto_total or 0),
            "monto_pagado": float(self.monto_pagado or 0),
            "saldo": self.saldo,
            "fecha_vencimiento": self.fecha_vencimiento.isoformat()
            if self.fecha_vencimiento
            else None,
            "estado": self.estado,
            "pagos": [pago.to_dict() for pago in self.pagos],
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Cuenta {self.tipo} {self.persona_nombre} saldo={self.saldo}>"


class PagoCuenta(db.Model):
    """Un abono parcial (o total) aplicado a una cuenta."""

    __tablename__ = "pago_cuenta"

    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(
        db.Integer, db.ForeignKey("cuenta_cobrar_pagar.id"), nullable=False, index=True
    )
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False, default=hoy_local)
    notas = db.Column(db.String(250))

    cuenta = db.relationship("CuentaCobrarPagar", back_populates="pagos")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "monto": float(self.monto or 0),
            "fecha_pago": self.fecha_pago.isoformat() if self.fecha_pago else None,
            "notas": self.notas,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PagoCuenta {self.monto} cuenta={self.cuenta_id}>"

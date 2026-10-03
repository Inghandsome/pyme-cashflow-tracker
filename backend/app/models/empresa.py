"""Modelo de empresa (la mueblería)."""

from app.extensions import db
from app.utils.fechas import ahora_utc


class Empresa(db.Model):
    """El negocio al que pertenecen todos los usuarios y movimientos.

    En este sistema cada instalación atiende a **una sola** empresa, pero se
    modela como tabla porque los datos del negocio (nombre, umbral de alerta)
    son configurables por el dueño y porque deja la puerta abierta a
    multi-negocio sin rediseñar la base.
    """

    __tablename__ = "empresa"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    giro = db.Column(db.String(80), nullable=False, default="muebleria")
    direccion = db.Column(db.String(250))
    telefono = db.Column(db.String(40))
    # Si el saldo proyectado baja de este monto, la API levanta la alerta.
    umbral_alerta_saldo = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=ahora_utc)

    usuarios = db.relationship("Usuario", back_populates="empresa", lazy="dynamic")
    categorias = db.relationship("Categoria", back_populates="empresa", lazy="dynamic")
    transacciones = db.relationship(
        "Transaccion", back_populates="empresa", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "giro": self.giro,
            "direccion": self.direccion,
            "telefono": self.telefono,
            "umbral_alerta_saldo": float(self.umbral_alerta_saldo or 0),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Empresa {self.nombre}>"

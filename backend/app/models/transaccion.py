"""Modelo de transacciones: el dinero que entra y el dinero que sale."""

from app.extensions import db
from app.utils.fechas import ahora_utc, hoy_local

TIPO_INGRESO = "ingreso"
TIPO_EGRESO = "egreso"
TIPOS_MOVIMIENTO = (TIPO_INGRESO, TIPO_EGRESO)

METODO_EFECTIVO = "efectivo"
METODO_TRANSFERENCIA = "transferencia"
METODO_TARJETA = "tarjeta"
METODO_OTRO = "otro"
METODOS_PAGO = (METODO_EFECTIVO, METODO_TRANSFERENCIA, METODO_TARJETA, METODO_OTRO)


class Transaccion(db.Model):
    """Un movimiento de dinero de la mueblería.

    Guarda ``usuario_id`` para poder auditar **quién** capturó cada movimiento:
    es lo que permite que el dueño revise el trabajo del cajero y que el
    propio cajero solo pueda editar lo que él registró hoy.
    """

    __tablename__ = "transaccion"

    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    tipo = db.Column(db.String(10), nullable=False, index=True)
    descripcion = db.Column(db.String(250))
    # Fecha del movimiento (la del negocio, no la de captura).
    fecha = db.Column(db.Date, nullable=False, default=hoy_local, index=True)
    metodo_pago = db.Column(
        db.String(20), nullable=False, default=METODO_EFECTIVO, index=True
    )
    categoria_id = db.Column(
        db.Integer, db.ForeignKey("categoria.id"), nullable=False, index=True
    )
    empresa_id = db.Column(
        db.Integer, db.ForeignKey("empresa.id"), nullable=False, index=True
    )
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True
    )
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=ahora_utc)

    categoria = db.relationship("Categoria", back_populates="transacciones")
    empresa = db.relationship("Empresa", back_populates="transacciones")
    usuario = db.relationship("Usuario", back_populates="transacciones")

    @property
    def signo(self) -> int:
        """+1 si es ingreso, -1 si es egreso (para calcular saldos)."""
        return 1 if self.tipo == TIPO_INGRESO else -1

    @property
    def monto_con_signo(self) -> float:
        return self.signo * float(self.monto or 0)

    def to_dict(self, idioma: str = "es") -> dict:
        return {
            "id": self.id,
            "monto": float(self.monto or 0),
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "metodo_pago": self.metodo_pago,
            "categoria_id": self.categoria_id,
            "categoria": self.categoria.nombre_para(idioma) if self.categoria else None,
            "categoria_icono": self.categoria.icono if self.categoria else None,
            "registrado_por": self.usuario.nombre if self.usuario else None,
            "usuario_id": self.usuario_id,
            "fecha_creacion": self.fecha_creacion.isoformat()
            if self.fecha_creacion
            else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Transaccion {self.tipo} {self.monto} {self.fecha}>"

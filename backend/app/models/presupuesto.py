"""Modelo de presupuestos mensuales por categoría."""

from app.extensions import db


class Presupuesto(db.Model):
    """Cuánto planea gastar la mueblería en una categoría durante un mes.

    Se compara contra el gasto real del mes para pintar el semáforo:
    🟢 menos de 75 %, 🟡 entre 75 % y 99 %, 🔴 100 % o más.
    """

    __tablename__ = "presupuesto"
    __table_args__ = (
        db.UniqueConstraint(
            "empresa_id",
            "categoria_id",
            "mes",
            "anio",
            name="uq_presupuesto_empresa_categoria_periodo",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(
        db.Integer, db.ForeignKey("categoria.id"), nullable=False, index=True
    )
    monto_asignado = db.Column(db.Numeric(12, 2), nullable=False)
    mes = db.Column(db.Integer, nullable=False, index=True)
    anio = db.Column(db.Integer, nullable=False, index=True)
    empresa_id = db.Column(
        db.Integer, db.ForeignKey("empresa.id"), nullable=False, index=True
    )

    categoria = db.relationship("Categoria", back_populates="presupuestos")

    def to_dict(self, idioma: str = "es") -> dict:
        return {
            "id": self.id,
            "categoria_id": self.categoria_id,
            "categoria": self.categoria.nombre_para(idioma) if self.categoria else None,
            "monto_asignado": float(self.monto_asignado or 0),
            "mes": self.mes,
            "anio": self.anio,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Presupuesto {self.categoria_id} {self.mes}/{self.anio}>"

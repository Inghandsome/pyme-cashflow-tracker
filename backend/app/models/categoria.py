"""Modelo de categorías de ingresos y egresos.

Las categorías son **datos, no código**: el dueño puede crear, renombrar o
desactivar categorías desde la interfaz. Cada una guarda su nombre en español
y en inglés porque son registros de base de datos, no textos fijos del
frontend, y la interfaz es bilingüe.
"""

from app.extensions import db
from app.utils.fechas import ahora_utc

TIPO_INGRESO = "ingreso"
TIPO_EGRESO = "egreso"
TIPOS_CATEGORIA = (TIPO_INGRESO, TIPO_EGRESO)


class Categoria(db.Model):
    __tablename__ = "categoria"
    __table_args__ = (
        db.UniqueConstraint(
            "empresa_id", "nombre", "tipo", name="uq_categoria_empresa_nombre_tipo"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    nombre_en = db.Column(db.String(120))
    tipo = db.Column(db.String(10), nullable=False, index=True)
    icono = db.Column(db.String(16))
    color = db.Column(db.String(20))
    activa = db.Column(db.Boolean, nullable=False, default=True)
    empresa_id = db.Column(
        db.Integer, db.ForeignKey("empresa.id"), nullable=False, index=True
    )
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=ahora_utc)

    empresa = db.relationship("Empresa", back_populates="categorias")
    transacciones = db.relationship("Transaccion", back_populates="categoria")
    presupuestos = db.relationship("Presupuesto", back_populates="categoria")

    def nombre_para(self, idioma: str = "es") -> str:
        """Nombre traducido; si falta la traducción, cae al español."""
        if idioma == "en" and self.nombre_en:
            return self.nombre_en
        return self.nombre

    def to_dict(self, idioma: str = "es") -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "nombre_en": self.nombre_en,
            "nombre_mostrado": self.nombre_para(idioma),
            "tipo": self.tipo,
            "icono": self.icono,
            "color": self.color,
            "activa": self.activa,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Categoria {self.nombre} ({self.tipo})>"

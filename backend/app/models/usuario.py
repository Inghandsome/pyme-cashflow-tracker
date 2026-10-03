"""Modelo de usuario con roles (dueño / cajero)."""

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils.fechas import ahora_utc

# --- Roles ---
ROL_DUENO = "dueno"
ROL_CAJERO = "cajero"
ROLES_VALIDOS = (ROL_DUENO, ROL_CAJERO)

# --- Idiomas de la interfaz ---
IDIOMAS_VALIDOS = ("es", "en")


class Usuario(db.Model):
    """Persona que usa el sistema.

    - ``dueno``  → acceso completo (dashboard, presupuestos, flujo, reportes).
    - ``cajero`` → registra movimientos del día y ve un resumen básico.

    El rol viaja como *claim* dentro del JWT para que el backend autorice sin
    consultar la base en cada petición.

    Nota de diseño: todos los usuarios pertenecen a una empresa
    (``empresa_id``), no solo el dueño. Así el cajero creado por el dueño
    comparte categorías y movimientos del mismo negocio.
    """

    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default=ROL_CAJERO, index=True)
    idioma = db.Column(db.String(5), nullable=False, default="es")
    activo = db.Column(db.Boolean, nullable=False, default=True)
    empresa_id = db.Column(
        db.Integer, db.ForeignKey("empresa.id"), nullable=False, index=True
    )
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=ahora_utc)

    empresa = db.relationship("Empresa", back_populates="usuarios")
    transacciones = db.relationship("Transaccion", back_populates="usuario")

    # --- Contraseña ---
    def establecer_password(self, password: str) -> None:
        """Guarda la contraseña como hash (nunca en texto plano)."""
        self.password_hash = generate_password_hash(password)

    def verificar_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # --- Consultas de rol ---
    @property
    def es_dueno(self) -> bool:
        return self.rol == ROL_DUENO

    @property
    def es_cajero(self) -> bool:
        return self.rol == ROL_CAJERO

    # --- Serialización ---
    def to_dict(self) -> dict:
        """Datos públicos del usuario. Nunca incluye el hash de la contraseña."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
            "idioma": self.idioma,
            "activo": self.activo,
            "empresa": self.empresa.to_dict() if self.empresa else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Usuario {self.email} ({self.rol})>"

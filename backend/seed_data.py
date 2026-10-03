"""Datos iniciales del sistema (semilla).

Crea, si no existen:

1. La **empresa** (la mueblería) con su umbral de alerta.
2. El usuario **dueño**, tomando el correo y la contraseña de ``.env``.
3. Las **23 categorías** propias de una mueblería, con su traducción al inglés.

Es **idempotente**: se puede ejecutar varias veces sin duplicar nada, así que
es seguro correrlo otra vez después de actualizar el proyecto.

Uso::

    flask seed
    flask seed --email dueno@muebleria.com --password MiClaveSegura123
"""

import os

from app.extensions import db
from app.models import Categoria, Empresa, Usuario
from app.models.usuario import ROL_DUENO

# ─────────────────────────── categorías de mueblería ───────────────────────────
# (nombre en español, nombre en inglés, tipo, ícono)

CATEGORIAS_INGRESO = [
    ("Venta de muebles de contado", "Cash furniture sales", "💵"),
    ("Venta con tarjeta", "Card sales", "💳"),
    ("Transferencia / SPEI", "Bank transfer", "📱"),
    ("Anticipo de pedido", "Custom order deposit", "🪑"),
    ("Abono de cliente a crédito", "Customer credit payment", "📋"),
    ("Venta de muebles de línea", "Showroom sales", "🛋️"),
    ("Reparación y retapizado", "Repair and reupholstery", "🔧"),
    ("Flete cobrado al cliente", "Delivery charged to customer", "🚚"),
    ("Otros ingresos", "Other income", "📦"),
]

CATEGORIAS_EGRESO = [
    ("Madera y tableros (MDF, triplay)", "Lumber and boards", "🪵"),
    ("Telas, espumas y herrajes", "Fabric, foam and hardware", "🧵"),
    ("Barniz, pintura y acabados", "Varnish, paint and finishes", "🎨"),
    ("Herramientas y consumibles", "Tools and consumables", "🧰"),
    ("Carpinteros / tapiceros (destajo)", "Carpenters / upholsterers", "👷"),
    ("Nómina y sueldos", "Payroll and wages", "💼"),
    ("Renta del taller o local", "Workshop rent", "🏠"),
    ("Luz (CFE)", "Electricity", "⚡"),
    ("Agua", "Water", "💧"),
    ("Internet y teléfono", "Internet and phone", "📶"),
    ("Fletes y entregas", "Freight and deliveries", "🚚"),
    ("Mantenimiento de maquinaria", "Machinery maintenance", "🔩"),
    ("Impuestos / SAT", "Taxes", "📋"),
    ("Otros gastos", "Other expenses", "🏷️"),
]


def _obtener_o_crear_empresa() -> tuple[Empresa, bool]:
    """Devuelve la empresa única del sistema, creándola si hace falta."""
    empresa = Empresa.query.first()
    if empresa:
        return empresa, False

    empresa = Empresa(
        nombre=os.getenv("EMPRESA_NOMBRE", "Mueblería"),
        giro="muebleria",
        telefono=os.getenv("EMPRESA_TELEFONO") or None,
        umbral_alerta_saldo=0,
    )
    db.session.add(empresa)
    db.session.flush()  # asigna el id sin cerrar la transacción
    return empresa, True


def _obtener_o_crear_dueno(empresa: Empresa, email: str, password: str):
    """Crea el usuario dueño si no existe. Nunca duplica correos."""
    existente = Usuario.query.filter_by(email=email).first()
    if existente:
        return existente, False

    dueno = Usuario(
        nombre=os.getenv("DUENO_NOMBRE", "Dueño de la mueblería"),
        email=email,
        rol=ROL_DUENO,
        idioma="es",
        activo=True,
        empresa_id=empresa.id,
    )
    dueno.establecer_password(password)
    db.session.add(dueno)
    return dueno, True


def _sembrar_categorias(empresa: Empresa) -> int:
    """Inserta las categorías que falten. Devuelve cuántas creó."""
    creadas = 0

    for tipo, catalogo in (
        ("ingreso", CATEGORIAS_INGRESO),
        ("egreso", CATEGORIAS_EGRESO),
    ):
        for nombre, nombre_en, icono in catalogo:
            existe = Categoria.query.filter_by(
                empresa_id=empresa.id, nombre=nombre, tipo=tipo
            ).first()
            if existe:
                # Si ya existía sin traducción, la completamos.
                if not existe.nombre_en:
                    existe.nombre_en = nombre_en
                if not existe.icono:
                    existe.icono = icono
                continue

            db.session.add(
                Categoria(
                    nombre=nombre,
                    nombre_en=nombre_en,
                    tipo=tipo,
                    icono=icono,
                    activa=True,
                    empresa_id=empresa.id,
                )
            )
            creadas += 1

    return creadas


def sembrar(email: str | None = None, password: str | None = None) -> list[str]:
    """Ejecuta la semilla y devuelve las líneas de resultado."""
    email = (email or os.getenv("DUENO_EMAIL") or "dueno@muebleria.com").lower()
    password = password or os.getenv("DUENO_PASSWORD") or "CambiarEsta123"

    lineas: list[str] = []

    empresa, empresa_creada = _obtener_o_crear_empresa()
    lineas.append(
        f"Empresa: {'creada' if empresa_creada else 'ya existía'} → {empresa.nombre}"
    )

    dueno, dueno_creado = _obtener_o_crear_dueno(empresa, email, password)
    if dueno_creado:
        lineas.append(f"Dueño creado → {dueno.email}")
    else:
        lineas.append(f"Dueño ya existía → {dueno.email} (no se tocó su contraseña)")

    creadas = _sembrar_categorias(empresa)
    lineas.append(
        f"Categorías: {creadas} creadas, "
        f"{len(CATEGORIAS_INGRESO) + len(CATEGORIAS_EGRESO) - creadas} ya existían"
    )

    db.session.commit()

    lineas.append("")
    lineas.append("Listo. Ya puedes iniciar sesión con:")
    lineas.append(f"  correo:     {email}")
    lineas.append(f"  contraseña: {password}")
    lineas.append("")
    lineas.append("IMPORTANTE: cambia esa contraseña antes de desplegar en internet.")

    return lineas


# Permite ejecutarlo también sin el CLI de Flask:  python seed_data.py
# Es la vía más corta para dejar el sistema listo: crea las tablas y siembra
# los datos en un solo paso.
if __name__ == "__main__":  # pragma: no cover
    from app import crear_app

    aplicacion = crear_app()
    with aplicacion.app_context():
        db.create_all()
        for linea in sembrar():
            print(linea)

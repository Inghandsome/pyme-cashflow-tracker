"""Utilidades de fecha y hora.

Todas las fechas se guardan en **UTC sin zona horaria** (naive) para que
SQLite y PostgreSQL se comporten igual. La conversión a la hora local de la
mueblería se hace solo al calcular "el día de hoy".
"""

from datetime import date, datetime, timedelta, timezone

try:  # Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

from flask import current_app


def ahora_utc() -> datetime:
    """Momento actual en UTC, sin información de zona horaria."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def zona_local():
    """Zona horaria configurada de la mueblería (America/Mexico_City)."""
    nombre = current_app.config.get("ZONA_HORARIA", "America/Mexico_City")
    if ZoneInfo is None:
        return timezone(timedelta(hours=-6))  # respaldo: CST
    try:
        return ZoneInfo(nombre)
    except Exception:
        return timezone(timedelta(hours=-6))


def hoy_local() -> date:
    """Fecha de hoy según la zona horaria del negocio.

    Es la que se usa para el filtro diario del cajero: un movimiento
    registrado a las 23:50 en Chicontepec debe contar como el día correcto,
    no como el día siguiente en UTC.
    """
    return datetime.now(zona_local()).date()


def mes_actual() -> tuple[int, int]:
    """(mes, año) actuales en la zona del negocio."""
    hoy = hoy_local()
    return hoy.month, hoy.year


def rango_del_dia(dia: date | None = None) -> tuple[date, date]:
    """Inicio y fin (inclusive) del día indicado."""
    dia = dia or hoy_local()
    return dia, dia

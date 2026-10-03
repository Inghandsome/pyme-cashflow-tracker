"""Ayudas para validar y convertir lo que llega del frontend.

Toda la API recibe JSON del navegador, así que nada es confiable: los montos
pueden venir como texto, las fechas mal formadas y los textos vacíos. Estas
funciones convierten y fallan de forma explícita en vez de reventar con un 500.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.models.transaccion import METODOS_PAGO, TIPOS_MOVIMIENTO


class DatoInvalido(ValueError):
    """El cliente envió un valor que no se puede usar."""


def limpiar_texto(valor, maximo: int = 250) -> str | None:
    """Recorta espacios y limita la longitud. Devuelve ``None`` si queda vacío."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    return texto[:maximo]


def a_decimal(valor, campo: str = "monto", positivo: bool = True) -> Decimal:
    """Convierte a ``Decimal`` con 2 decimales."""
    if valor is None or valor == "":
        raise DatoInvalido(f"Falta el campo '{campo}'.")
    try:
        numero = Decimal(str(valor).replace(",", "").strip())
    except (InvalidOperation, AttributeError, ValueError) as exc:
        raise DatoInvalido(f"El campo '{campo}' debe ser un número.") from exc

    if positivo and numero <= 0:
        raise DatoInvalido(f"El campo '{campo}' debe ser mayor que cero.")

    return numero.quantize(Decimal("0.01"))


def a_entero(valor, campo: str) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError) as exc:
        raise DatoInvalido(f"El campo '{campo}' debe ser un número entero.") from exc


def a_fecha(valor, campo: str = "fecha") -> date:
    """Acepta ``YYYY-MM-DD`` o un objeto fecha ya construido."""
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    if isinstance(valor, datetime):
        return valor.date()
    if not valor:
        raise DatoInvalido(f"Falta el campo '{campo}'.")
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError as exc:
        raise DatoInvalido(
            f"El campo '{campo}' debe tener el formato AAAA-MM-DD."
        ) from exc


def validar_tipo_movimiento(valor) -> str:
    valor = (limpiar_texto(valor, 10) or "").lower()
    if valor not in TIPOS_MOVIMIENTO:
        raise DatoInvalido("El tipo debe ser 'ingreso' o 'egreso'.")
    return valor


def validar_metodo_pago(valor) -> str:
    """El método de pago es opcional: si no viene, se asume efectivo."""
    if not valor:
        return METODOS_PAGO[0]
    valor = str(valor).strip().lower()
    if valor not in METODOS_PAGO:
        raise DatoInvalido(
            "El método de pago debe ser: " + ", ".join(METODOS_PAGO) + "."
        )
    return valor


def validar_idioma(valor) -> str:
    from app.models.usuario import IDIOMAS_VALIDOS

    valor = (limpiar_texto(valor, 5) or "es").lower()
    if valor not in IDIOMAS_VALIDOS:
        raise DatoInvalido("El idioma debe ser 'es' o 'en'.")
    return valor


def validar_mes_anio(mes, anio) -> tuple[int, int]:
    mes = a_entero(mes, "mes")
    anio = a_entero(anio, "anio")
    if not 1 <= mes <= 12:
        raise DatoInvalido("El mes debe estar entre 1 y 12.")
    if not 2000 <= anio <= 2100:
        raise DatoInvalido("El año no es válido.")
    return mes, anio

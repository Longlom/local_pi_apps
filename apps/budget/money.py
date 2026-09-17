from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

TWOPLACES = Decimal("0.01")


def parse_money(raw: str) -> int:
    """Parse a decimal string into integer minor units (cents)."""
    text = (raw or "").strip().replace(" ", "").replace(",", ".")
    if not text:
        raise ValueError("Amount is required")
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Invalid amount") from exc
    if value < 0:
        raise ValueError("Amount cannot be negative")
    cents = (value.quantize(TWOPLACES, rounding=ROUND_HALF_UP) * 100).to_integral_value()
    return int(cents)


def format_money(cents: int, currency: str) -> str:
    sign = "-" if cents < 0 else ""
    value = Decimal(abs(cents)) / 100
    return f"{sign}{value:,.2f} {currency}".replace(",", " ")


def field_money(cents: int) -> str:
    return f"{Decimal(cents) / 100:.2f}"


def ten_percent(cents: int) -> int:
    return int((Decimal(cents) * Decimal("0.10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

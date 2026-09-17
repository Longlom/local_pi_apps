from __future__ import annotations

from typing import Any

COLORS = {
    "ten": "#C9941A",
    "ten_usd": "#D8AD49",
    "savings": "#36BEB0",
    "savings_usd": "#1E8AA8",
    "daughter": "#D46A8A",
    "daughter_usd": "#A84D6E",
    "everyday": "#F5C200",
    "usd": "#1E8AA8",
    "spent": "#E8583A",
}


def segments(items: list[tuple[str, str, int]], colors: dict[str, str] | None = None) -> list[dict[str, Any]]:
    palette = colors or COLORS
    total = sum(max(cents, 0) for _, _, cents in items)
    circumference = 314.16
    out: list[dict[str, Any]] = []
    offset = 0.0
    for key, label, cents in items:
        value = max(cents, 0)
        pct = (value / total * 100) if total else 0.0
        dash = circumference * pct / 100
        out.append(
            {
                "key": key,
                "label": label,
                "cents": value,
                "pct": pct,
                "dash": round(dash, 2),
                "gap": round(circumference - dash, 2),
                "offset": round(offset, 2),
                "color": palette.get(key, "#666"),
            }
        )
        offset -= dash
    return out

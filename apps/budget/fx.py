from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

_CACHE: dict[str, Any] = {"at": 0.0, "quote": None}
_TTL = 60 * 60


def _get(url: str, timeout: float = 4.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "rasp-budget/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _from_cbr() -> dict[str, Any]:
    data = _get("https://www.cbr-xml-daily.ru/daily_json.js")
    usd = data["Valute"]["USD"]
    rate = Decimal(str(usd["Value"])) / Decimal(str(usd.get("Nominal") or 1))
    as_of = str(data.get("Date", ""))[:10]
    return {"rate": rate, "as_of": as_of, "source": "CBR"}


def _from_erapi() -> dict[str, Any]:
    data = _get("https://open.er-api.com/v6/latest/USD")
    rate = Decimal(str(data["rates"]["RUB"]))
    as_of = str(data.get("time_last_update_utc", ""))[:16]
    return {"rate": rate, "as_of": as_of or datetime.now(timezone.utc).date().isoformat(), "source": "open.er-api"}


def usd_to_rub() -> dict[str, Any] | None:
    now = time.time()
    if _CACHE["quote"] and now - _CACHE["at"] < _TTL:
        return _CACHE["quote"]
    for loader in (_from_cbr, _from_erapi):
        try:
            quote = loader()
            quote["fetched"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            _CACHE["quote"] = quote
            _CACHE["at"] = now
            return quote
        except Exception:
            continue
    return _CACHE["quote"]


def usd_cents_to_rub_cents(usd_cents: int, rate: Decimal) -> int:
    return int((Decimal(usd_cents) * rate).quantize(Decimal("1")))

from __future__ import annotations

import os
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import charts
import db
import fx
from money import field_money, format_money, parse_money, ten_percent

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / os.environ.get("DATA_DIR", "data")
DB_PATH = DATA_DIR / "budget.sqlite"
BASE_CURRENCY = os.environ.get("BASE_CURRENCY", "RUB")
SECRET = os.environ.get("SESSION_SECRET", "rasp-budget-lan")

POT_LABELS = {
    "ten": "10%",
    "ten_usd": "10% USD",
    "everyday": "Everyday",
    "savings": "Savings",
    "savings_usd": "Savings USD",
    "daughter": "Daughter",
    "daughter_usd": "Daughter USD",
    "usd": "USD cash",
}
SOURCE_LABELS = {
    "job_5": "Job (5th)",
    "job_20": "Job (20th)",
    "extra": "Extra income",
}
CATEGORY_LABELS = {
    "food": "Food",
    "cafes": "Cafes",
    "housing": "Housing",
    "utilities": "Utilities",
    "transport": "Transport",
    "health": "Health",
    "kids": "Kids",
    "clothes": "Clothes",
    "entertainment": "Entertainment",
    "subscriptions": "Subscriptions",
    "gifts": "Gifts",
    "other": "Other",
}

STATIC_VERSION = str(int((APP_DIR / "static" / "style.css").stat().st_mtime))

app = FastAPI(title="Family budget")
app.add_middleware(SessionMiddleware, secret_key=SECRET, max_age=14 * 24 * 3600)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
templates.env.globals.update(
    fmt=lambda cents, currency=None: format_money(cents, currency or BASE_CURRENCY),
    fmt_usd=lambda cents: format_money(cents, "USD"),
    field=field_money,
    pot_label=lambda pot: POT_LABELS.get(pot, pot),
    source_label=lambda src: SOURCE_LABELS.get(src, src),
    category_label=lambda category: CATEGORY_LABELS.get(category, category),
    base_currency=BASE_CURRENCY,
    static_version=STATIC_VERSION,
)


SAVED_ACCOUNTS = {"ten", "savings", "daughter", "usd"}


def account_of(pot: str) -> str | None:
    for account, pots in db.ACCOUNT_POTS.items():
        if pot in pots:
            return account
    return None


def counted_totals(
    bals: dict[str, int],
    usd_rub: dict[str, int],
    excluded: set[str],
) -> dict[str, int]:
    total_rub = 0
    saved_stock = 0
    held_usd = 0
    held_usd_rub = 0
    for account, pots in db.ACCOUNT_POTS.items():
        if account in excluded:
            continue
        for pot in pots:
            if pot in db.POTS_USD:
                rub = usd_rub.get(pot, 0)
                total_rub += rub
                held_usd += bals[pot]
                held_usd_rub += rub
                if account in SAVED_ACCOUNTS:
                    saved_stock += rub
            else:
                total_rub += bals[pot]
                if account in SAVED_ACCOUNTS:
                    saved_stock += bals[pot]
    return {
        "total_rub": total_rub,
        "saved_stock": saved_stock,
        "held_usd": held_usd,
        "held_usd_rub": held_usd_rub,
    }


def safe_back(request: Request) -> str:
    referer = request.headers.get("referer") or "/"
    parsed = urlparse(referer)
    path = parsed.path or "/"
    if not path.startswith("/") or path.startswith("//"):
        return "/"
    return f"{path}?{parsed.query}" if parsed.query else path


def flash(request: Request, message: str, kind: str = "error") -> None:
    request.session.setdefault("flashes", []).append({"msg": message, "kind": kind})


def pops(request: Request) -> list[dict]:
    items = request.session.pop("flashes", [])
    return items


def parse_month(raw: str | None) -> tuple[int, int]:
    today = date.today()
    if not raw:
        return today.year, today.month
    year_s, month_s = raw.split("-", 1)
    year, month = int(year_s), int(month_s)
    if month < 1 or month > 12:
        raise ValueError("bad month")
    return year, month


def parse_rate(raw: str) -> int:
    try:
        rate = Decimal((raw or "").strip().replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Invalid rate") from exc
    if rate <= 0:
        raise ValueError("Rate must be greater than zero")
    return int((rate * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def parse_optional_money(raw: str) -> int:
    return parse_money(raw) if (raw or "").strip() else 0


def make_rate_chart(rates: list[dict]) -> dict | None:
    chronological = list(reversed(rates))
    if not chronological:
        return None
    values = [row["rate_milli"] / 1000 for row in chronological]
    low, high = min(values), max(values)
    spread = high - low or 1
    width, height, pad = 600, 160, 16
    points = []
    for index, value in enumerate(values):
        x = pad if len(values) == 1 else pad + index * (width - 2 * pad) / (len(values) - 1)
        y = height - pad - (value - low) * (height - 2 * pad) / spread
        points.append(f"{x:.1f},{y:.1f}")
    return {"points": " ".join(points), "low": low, "high": high}


def month_nav(year: int, month: int) -> dict[str, str]:
    if month == 1:
        prev_y, prev_m = year - 1, 12
    else:
        prev_y, prev_m = year, month - 1
    if month == 12:
        next_y, next_m = year + 1, 1
    else:
        next_y, next_m = year, month + 1
    return {
        "current": f"{year:04d}-{month:02d}",
        "prev": f"{prev_y:04d}-{prev_m:02d}",
        "next": f"{next_y:04d}-{next_m:02d}",
        "label": date(year, month, 1).strftime("%B %Y"),
        "last_day": f"{year:04d}-{month:02d}-{monthrange(year, month)[1]:02d}",
    }


def ctx(request: Request, **extra):
    with db.session(DB_PATH) as conn:
        bals = db.balances(conn)
        excluded = db.excluded_accounts(conn)
    quote = extra.get("quote")
    if "quote" not in extra:
        quote = fx.usd_to_rub()
    data = {
        "request": request,
        "flashes": pops(request),
        "balances": bals,
        "today": db.today_iso(),
        "nav": extra.pop("nav", None),
        "quote": quote,
        "rate_text": f"{quote['rate']:.2f}" if quote else None,
        "excluded": extra.get("excluded", excluded),
        "count_accounts": db.COUNT_ACCOUNTS,
    }
    data.update(extra)
    return data


def page(request: Request, name: str, **extra):
    return templates.TemplateResponse(request, name, ctx(request, **extra))


@app.post("/exclude")
def exclude_toggle(request: Request, account: str = Form()):
    try:
        with db.session(DB_PATH) as conn:
            db.toggle_excluded_account(conn, account)
    except ValueError as exc:
        flash(request, str(exc))
    return RedirectResponse(safe_back(request), status_code=303)


@app.get("/")
def month_page(request: Request, month: str | None = None):
    try:
        year, mon = parse_month(month)
    except ValueError:
        year, mon = date.today().year, date.today().month
    nav = month_nav(year, mon)
    with db.session(DB_PATH) as conn:
        summary = db.month_summary(conn, year, mon)
        incomes = db.list_incomes(conn, summary["start"], summary["end"])
        expenses = db.list_expenses(conn, summary["start"], summary["end"])
        trades = db.list_fx(conn, summary["start"], summary["end"])
        deposits = db.list_sleeve_deposits(conn, summary["start"], summary["end"])
        rates = db.rate_history(conn)
        bals = db.balances(conn)
        categories = db.spend_by_category(conn, summary["start"], summary["end"])
        excluded = db.excluded_accounts(conn)

    quote = fx.usd_to_rub()
    usd_rub_cents = 0
    ten_usd_rub_cents = 0
    savings_usd_rub_cents = 0
    daughter_usd_rub_cents = 0
    if quote:
        usd_rub_cents = fx.usd_cents_to_rub_cents(bals["usd"], quote["rate"])
        ten_usd_rub_cents = fx.usd_cents_to_rub_cents(bals["ten_usd"], quote["rate"])
        savings_usd_rub_cents = fx.usd_cents_to_rub_cents(
            bals["savings_usd"], quote["rate"]
        )
        daughter_usd_rub_cents = fx.usd_cents_to_rub_cents(
            bals["daughter_usd"], quote["rate"]
        )
        spent_usd_rub = fx.usd_cents_to_rub_cents(summary["spent_usd"], quote["rate"])
    else:
        spent_usd_rub = 0

    usd_rub = {
        "usd": usd_rub_cents,
        "ten_usd": ten_usd_rub_cents,
        "savings_usd": savings_usd_rub_cents,
        "daughter_usd": daughter_usd_rub_cents,
    }
    counted = counted_totals(bals, usd_rub, excluded)
    all_items = [
        ("ten", "10%", bals["ten"]),
        ("ten_usd", "10% USD", ten_usd_rub_cents),
        ("savings", "Savings", bals["savings"]),
        ("savings_usd", "Savings USD", savings_usd_rub_cents),
        ("daughter", "Daughter", bals["daughter"]),
        ("daughter_usd", "Daughter USD", daughter_usd_rub_cents),
        ("everyday", "Everyday", bals["everyday"]),
        ("usd", "USD cash", usd_rub_cents),
    ]
    all_items = [item for item in all_items if account_of(item[0]) not in excluded]

    def stock_view(key: str, label: str, items: list[tuple[str, str, int]]) -> dict:
        return {
            "key": key,
            "label": label,
            "segments": charts.segments(items),
            "total": sum(max(cents, 0) for _, _, cents in items),
        }

    stock_views = [
        stock_view(
            "all",
            "All",
            all_items,
        ),
        stock_view(
            "savings",
            "Savings",
            [
                ("savings", "Savings RUB", bals["savings"]),
                ("savings_usd", "Savings USD", savings_usd_rub_cents),
            ],
        ),
        stock_view(
            "daughter",
            "Daughter",
            [
                ("daughter", "Daughter RUB", bals["daughter"]),
                ("daughter_usd", "Daughter USD", daughter_usd_rub_cents),
            ],
        ),
        stock_view(
            "everyday",
            "Everyday",
            [
                ("everyday", "Everyday", bals["everyday"]),
                ("usd", "USD cash", usd_rub_cents),
            ],
        ),
        stock_view(
            "ten",
            "10%",
            [
                ("ten", "10% RUB", bals["ten"]),
                ("ten_usd", "10% USD", ten_usd_rub_cents),
            ],
        ),
    ]
    month_flow = charts.segments(
        [
            ("ten", "Into 10%", summary["ten"]),
            ("savings", "Savings bank", summary["savings"]),
            ("usd", "Bought USD", summary["usd_local"]),
            ("spent", "Spent", summary["spent_local"] + spent_usd_rub),
            ("everyday", "Everyday leftover", max(summary["everyday"] - summary["spent_local"] - summary["usd_local"], 0)),
        ]
    )
    cat_max = max((row["amount_cents"] for row in categories), default=0)
    cat_bars = [
        {
            **row,
            "pct": (row["amount_cents"] / cat_max * 100) if cat_max else 0,
        }
        for row in categories
    ]
    total_rub = counted["total_rub"]
    saved_stock = counted["saved_stock"]
    held_usd = counted["held_usd"]
    held_usd_rub = counted["held_usd_rub"]

    return page(
        request,
        "month.html",
        nav=nav,
        summary=summary,
        incomes=incomes,
        expenses=expenses,
        trades=trades,
        deposits=deposits,
        quote=quote,
        usd_rub_cents=usd_rub_cents,
        ten_usd_rub_cents=ten_usd_rub_cents,
        savings_usd_rub_cents=savings_usd_rub_cents,
        daughter_usd_rub_cents=daughter_usd_rub_cents,
        rates=rates,
        rate_chart=make_rate_chart(rates),
        stock_views=stock_views,
        month_flow=month_flow,
        cat_bars=cat_bars,
        total_rub=total_rub,
        saved_stock=saved_stock,
        excluded=excluded,
        held_usd=held_usd,
        held_usd_rub=held_usd_rub,
        rate_text=f"{quote['rate']:.2f}" if quote else None,
    )


@app.get("/income")
def income_form(request: Request):
    return page(request, "income.html")


@app.post("/income")
def income_save(
    request: Request,
    occurred_on: str = Form(),
    source: str = Form(),
    gross: str = Form(),
    ten: str = Form(),
    everyday: str = Form(),
    savings: str = Form(),
    note: str = Form(""),
):
    try:
        gross_c = parse_money(gross)
        ten_c = parse_money(ten)
        everyday_c = parse_money(everyday)
        savings_c = parse_money(savings)
        with db.session(DB_PATH) as conn:
            db.add_income(
                conn, occurred_on, gross_c, source, note.strip(), ten_c, everyday_c, savings_c
            )
        flash(request, "Income recorded.", "ok")
        return RedirectResponse("/", status_code=303)
    except ValueError as exc:
        flash(request, str(exc))
        return RedirectResponse("/income", status_code=303)


@app.get("/income/{income_id}")
def income_edit(request: Request, income_id: int):
    with db.session(DB_PATH) as conn:
        entry = db.get_income(conn, income_id)
    if entry is None:
        flash(request, "Income not found.")
        return RedirectResponse("/", status_code=303)
    return page(request, "income.html", entry=entry)


@app.post("/income/{income_id}")
def income_update(
    request: Request,
    income_id: int,
    occurred_on: str = Form(),
    source: str = Form(),
    gross: str = Form(),
    ten: str = Form(),
    everyday: str = Form(),
    savings: str = Form(),
    note: str = Form(""),
):
    try:
        with db.session(DB_PATH) as conn:
            db.update_income(
                conn,
                income_id,
                occurred_on,
                parse_money(gross),
                source,
                note.strip(),
                parse_money(ten),
                parse_money(everyday),
                parse_money(savings),
            )
        flash(request, "Income updated.", "ok")
        return RedirectResponse("/", status_code=303)
    except ValueError as exc:
        flash(request, str(exc))
        return RedirectResponse(f"/income/{income_id}", status_code=303)


@app.get("/expense")
def expense_form(request: Request):
    return page(request, "expense.html", categories=CATEGORY_LABELS)


@app.post("/expense")
def expense_save(
    request: Request,
    occurred_on: str = Form(),
    pot: str = Form(),
    amount: str = Form(),
    category: str = Form(""),
    note: str = Form(""),
    confirm_ten: str | None = Form(None),
):
    try:
        amount_c = parse_money(amount)
        with db.session(DB_PATH) as conn:
            db.add_expense(
                conn,
                occurred_on,
                pot,
                amount_c,
                category.strip(),
                note.strip(),
                confirmed_ten=bool(confirm_ten),
            )
        flash(request, "Expense recorded.", "ok")
        return RedirectResponse("/", status_code=303)
    except ValueError as exc:
        flash(request, str(exc))
        return RedirectResponse("/expense", status_code=303)


@app.get("/expense/{expense_id}")
def expense_edit(request: Request, expense_id: int):
    with db.session(DB_PATH) as conn:
        entry = db.get_expense(conn, expense_id)
    if entry is None:
        flash(request, "Expense not found.")
        return RedirectResponse("/", status_code=303)
    return page(request, "expense.html", categories=CATEGORY_LABELS, entry=entry)


@app.post("/expense/{expense_id}")
def expense_update(
    request: Request,
    expense_id: int,
    occurred_on: str = Form(),
    pot: str = Form(),
    amount: str = Form(),
    category: str = Form(""),
    note: str = Form(""),
    confirm_ten: str | None = Form(None),
):
    try:
        with db.session(DB_PATH) as conn:
            db.update_expense(
                conn,
                expense_id,
                occurred_on,
                pot,
                parse_money(amount),
                category.strip(),
                note.strip(),
                confirmed_ten=bool(confirm_ten),
            )
        flash(request, "Expense updated.", "ok")
        return RedirectResponse("/", status_code=303)
    except ValueError as exc:
        flash(request, str(exc))
        return RedirectResponse(f"/expense/{expense_id}", status_code=303)


@app.get("/usd")
def usd_form(request: Request):
    return page(request, "usd.html")


@app.post("/usd")
def usd_save(
    request: Request,
    occurred_on: str = Form(),
    from_pot: str = Form(),
    local_spent: str = Form(),
    usd_got: str = Form(),
    note: str = Form(""),
):
    try:
        local_c = parse_money(local_spent)
        usd_c = parse_money(usd_got)
        with db.session(DB_PATH) as conn:
            db.add_fx(conn, occurred_on, from_pot, local_c, usd_c, note.strip())
        flash(request, "USD cash recorded.", "ok")
        return RedirectResponse("/", status_code=303)
    except ValueError as exc:
        flash(request, str(exc))
        return RedirectResponse("/usd", status_code=303)


@app.get("/sleeves")
def sleeves_form(request: Request, account: str = "ten"):
    if account not in db.SLEEVE_ACCOUNTS:
        account = "ten"
    with db.session(DB_PATH) as conn:
        rates = db.rate_history(conn)
    return page(
        request,
        "sleeves.html",
        account=account,
        rates=rates,
        rate_chart=make_rate_chart(rates),
    )


@app.post("/sleeves")
def sleeves_save(
    request: Request,
    occurred_on: str = Form(),
    account: str = Form(),
    mode: str = Form(),
    rub_amount: str = Form(""),
    usd_amount: str = Form(""),
    rate: str = Form(""),
    note: str = Form(""),
):
    try:
        rub_cents = parse_optional_money(rub_amount)
        usd_cents = parse_optional_money(usd_amount)
        rate_milli = parse_rate(rate) if usd_cents else 0
        with db.session(DB_PATH) as conn:
            if mode == "conversion":
                if not rub_cents or not usd_cents:
                    raise ValueError("RUB spent and USD received are required")
                db.add_fx(
                    conn,
                    occurred_on,
                    account,
                    rub_cents,
                    usd_cents,
                    note.strip(),
                    to_pot=f"{account}_usd",
                    rate_milli=rate_milli,
                )
            elif mode == "deposit":
                db.add_sleeve_deposit(
                    conn,
                    occurred_on,
                    account,
                    rub_cents,
                    usd_cents,
                    rate_milli,
                    note.strip(),
                )
            else:
                raise ValueError("Choose how the money was added")
        flash(request, "Account balances updated.", "ok")
        return RedirectResponse("/", status_code=303)
    except ValueError as exc:
        flash(request, str(exc))
        return RedirectResponse(f"/sleeves?account={account}", status_code=303)


@app.get("/opening")
def opening_form(request: Request):
    with db.session(DB_PATH) as conn:
        opening = db.opening_balances(conn)
    return page(request, "opening.html", opening=opening)


@app.post("/opening")
def opening_save(
    request: Request,
    ten: str = Form(),
    everyday: str = Form(),
    savings: str = Form(),
    ten_usd: str = Form(),
    savings_usd: str = Form(),
    daughter: str = Form(),
    daughter_usd: str = Form(),
    usd: str = Form(),
):
    try:
        amounts = {
            "ten": parse_money(ten),
            "everyday": parse_money(everyday),
            "savings": parse_money(savings),
            "ten_usd": parse_money(ten_usd),
            "savings_usd": parse_money(savings_usd),
            "daughter": parse_money(daughter),
            "daughter_usd": parse_money(daughter_usd),
            "usd": parse_money(usd),
        }
        with db.session(DB_PATH) as conn:
            db.set_opening(conn, amounts)
        flash(request, "Opening balances saved. Later incomes and expenses sit on top of these.", "ok")
        return RedirectResponse("/", status_code=303)
    except ValueError as exc:
        flash(request, str(exc))
        return RedirectResponse("/opening", status_code=303)


@app.get("/api/ten-percent")
def api_ten(gross: str = "0"):
    try:
        cents = parse_money(gross)
    except ValueError:
        cents = 0
    ten = ten_percent(cents)
    return {"gross": cents, "ten": ten, "rest": cents - ten}

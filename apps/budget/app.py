from __future__ import annotations

import os
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import charts
import db
import fx
from money import field_money, format_money, parse_money, ten_percent
from schemas import (
    CATEGORY_ENUM,
    DATE_DESC,
    DESCRIPTION,
    EXCLUDE_ACCOUNT_ENUM,
    MONEY_DESC,
    MONTH_DESC,
    POT_ENUM,
    REDIRECT_303,
    SLEEVE_ACCOUNT_ENUM,
    SLEEVE_MODE_ENUM,
    SOURCE_ENUM,
    TRANSFER_TO_ENUM,
    TAGS,
    TenPercentResponse,
)

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

app = FastAPI(
    title="Rasp Budget",
    description=DESCRIPTION,
    version="1.0.0",
    openapi_tags=TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
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


@app.post(
    "/exclude",
    tags=["Settings"],
    summary="Toggle account exclusion from totals",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def exclude_toggle(
    request: Request,
    account: str = Form(description=EXCLUDE_ACCOUNT_ENUM),
):
    try:
        with db.session(DB_PATH) as conn:
            db.toggle_excluded_account(conn, account)
    except ValueError as exc:
        flash(request, str(exc))
    return RedirectResponse(safe_back(request), status_code=303)


METRIC_DETAILS = frozenset({"ten", "saved", "spent"})


@app.get(
    "/",
    tags=["Dashboard"],
    summary="Monthly dashboard",
    response_class=HTMLResponse,
    responses={200: {"description": "Rendered month.html"}},
)
def month_page(
    request: Request,
    month: str | None = Query(default=None, description=MONTH_DESC),
    detail: str | None = Query(
        default=None,
        description="Drill-down for headline cards: ten | saved | spent",
    ),
):
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
        corrections = db.list_corrections(conn, summary["start"], summary["end"])
        transfers = db.list_transfers(conn, summary["start"], summary["end"])
        rates = db.rate_history(conn)
        bals = db.balances(conn)
        categories = db.spend_by_category(conn, summary["start"], summary["end"])
        excluded = db.excluded_accounts(conn)
        metric_detail = detail if detail in METRIC_DETAILS else None
        detail_items: list[dict] = []
        if metric_detail == "ten":
            detail_items = db.month_ten_details(conn, summary["start"], summary["end"])
        elif metric_detail == "saved":
            detail_items = db.month_saved_details(conn, summary["start"], summary["end"])
        elif metric_detail == "spent":
            detail_items = db.month_spent_details(conn, summary["start"], summary["end"])

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

    detail_totals = {
        "ten": summary["ten"],
        "saved": summary["saved_local"],
        "spent": summary["spent_local"],
    }

    return page(
        request,
        "month.html",
        nav=nav,
        summary=summary,
        incomes=incomes,
        expenses=expenses,
        trades=trades,
        deposits=deposits,
        corrections=corrections,
        transfers=transfers,
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
        metric_detail=metric_detail,
        detail_items=detail_items,
        detail_totals=detail_totals,
    )


@app.get(
    "/income",
    tags=["Income"],
    summary="New income form",
    response_class=HTMLResponse,
)
def income_form(request: Request):
    return page(request, "income.html")


@app.post(
    "/income",
    tags=["Income"],
    summary="Create income",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def income_save(
    request: Request,
    occurred_on: str = Form(description=DATE_DESC),
    source: str = Form(description=SOURCE_ENUM),
    gross: str = Form(description=MONEY_DESC),
    ten: str = Form(description=f"10% pot allocation. {MONEY_DESC}"),
    everyday: str = Form(description=f"Everyday pot allocation. {MONEY_DESC}"),
    savings: str = Form(description=f"Savings pot allocation. {MONEY_DESC}"),
    note: str = Form("", description="Optional note"),
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


@app.get(
    "/income/{income_id}",
    tags=["Income"],
    summary="Edit income form",
    response_class=HTMLResponse,
    responses={303: REDIRECT_303},
)
def income_edit(request: Request, income_id: int):
    with db.session(DB_PATH) as conn:
        entry = db.get_income(conn, income_id)
    if entry is None:
        flash(request, "Income not found.")
        return RedirectResponse("/", status_code=303)
    return page(request, "income.html", entry=entry)


@app.post(
    "/income/{income_id}",
    tags=["Income"],
    summary="Update income",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def income_update(
    request: Request,
    income_id: int,
    occurred_on: str = Form(description=DATE_DESC),
    source: str = Form(description=SOURCE_ENUM),
    gross: str = Form(description=MONEY_DESC),
    ten: str = Form(description=f"10% pot allocation. {MONEY_DESC}"),
    everyday: str = Form(description=f"Everyday pot allocation. {MONEY_DESC}"),
    savings: str = Form(description=f"Savings pot allocation. {MONEY_DESC}"),
    note: str = Form("", description="Optional note"),
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


@app.get(
    "/expense",
    tags=["Expense"],
    summary="New expense form",
    response_class=HTMLResponse,
)
def expense_form(request: Request):
    return page(request, "expense.html", categories=CATEGORY_LABELS)


@app.post(
    "/expense",
    tags=["Expense"],
    summary="Create expense",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def expense_save(
    request: Request,
    occurred_on: str = Form(description=DATE_DESC),
    pot: str = Form(description=POT_ENUM),
    amount: str = Form(description=MONEY_DESC),
    category: str = Form("", description=CATEGORY_ENUM),
    note: str = Form("", description="Optional note"),
    confirm_ten: str | None = Form(
        None,
        description="Required when spending from ten or ten_usd",
    ),
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


@app.get(
    "/expense/{expense_id}",
    tags=["Expense"],
    summary="Edit expense form",
    response_class=HTMLResponse,
    responses={303: REDIRECT_303},
)
def expense_edit(request: Request, expense_id: int):
    with db.session(DB_PATH) as conn:
        entry = db.get_expense(conn, expense_id)
    if entry is None:
        flash(request, "Expense not found.")
        return RedirectResponse("/", status_code=303)
    return page(request, "expense.html", categories=CATEGORY_LABELS, entry=entry)


@app.post(
    "/expense/{expense_id}",
    tags=["Expense"],
    summary="Update expense",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def expense_update(
    request: Request,
    expense_id: int,
    occurred_on: str = Form(description=DATE_DESC),
    pot: str = Form(description=POT_ENUM),
    amount: str = Form(description=MONEY_DESC),
    category: str = Form("", description=CATEGORY_ENUM),
    note: str = Form("", description="Optional note"),
    confirm_ten: str | None = Form(
        None,
        description="Required when moving spend into ten or ten_usd",
    ),
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


@app.get(
    "/transfer",
    tags=["Transfers"],
    summary="Move RUB from everyday to a savings account",
    response_class=HTMLResponse,
)
def transfer_form(
    request: Request,
    to: str = Query(default="savings", description=TRANSFER_TO_ENUM),
):
    if to not in db.SLEEVE_ACCOUNTS:
        to = "savings"
    return page(request, "transfer.html", to_account=to)


@app.post(
    "/transfer",
    tags=["Transfers"],
    summary="Record transfer from everyday",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def transfer_save(
    request: Request,
    occurred_on: str = Form(description=DATE_DESC),
    to_pot: str = Form(description=TRANSFER_TO_ENUM),
    amount: str = Form(description=MONEY_DESC),
    note: str = Form("", description="Optional note"),
):
    try:
        with db.session(DB_PATH) as conn:
            db.add_transfer(
                conn,
                occurred_on,
                to_pot,
                parse_money(amount),
                note.strip(),
            )
        flash(request, "Transfer recorded.", "ok")
        return RedirectResponse("/", status_code=303)
    except ValueError as exc:
        flash(request, str(exc))
        return RedirectResponse(f"/transfer?to={to_pot}", status_code=303)


@app.get(
    "/usd",
    tags=["USD purchase"],
    summary="New USD purchase form",
    response_class=HTMLResponse,
)
def usd_form(request: Request):
    return page(request, "usd.html")


@app.post(
    "/usd",
    tags=["USD purchase"],
    summary="Record USD purchase",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def usd_save(
    request: Request,
    occurred_on: str = Form(description=DATE_DESC),
    from_pot: str = Form(description="Source RUB pot (usually everyday)"),
    local_spent: str = Form(description=f"RUB spent. {MONEY_DESC}"),
    usd_got: str = Form(description=f"USD received. {MONEY_DESC}"),
    note: str = Form("", description="Optional note"),
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


@app.get(
    "/sleeves",
    tags=["Sleeves"],
    summary="Sleeve conversion/deposit form",
    response_class=HTMLResponse,
)
def sleeves_form(
    request: Request,
    account: str = Query(default="ten", description=SLEEVE_ACCOUNT_ENUM),
):
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


@app.post(
    "/sleeves",
    tags=["Sleeves"],
    summary="Record sleeve conversion or deposit",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def sleeves_save(
    request: Request,
    occurred_on: str = Form(description=DATE_DESC),
    account: str = Form(description=SLEEVE_ACCOUNT_ENUM),
    mode: str = Form(description=SLEEVE_MODE_ENUM),
    rub_amount: str = Form("", description=f"RUB amount. {MONEY_DESC}"),
    usd_amount: str = Form("", description=f"USD amount. {MONEY_DESC}"),
    rate: str = Form("", description="Exchange rate; required when usd_amount > 0"),
    note: str = Form("", description="Optional note"),
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


@app.get(
    "/opening",
    tags=["Opening balances"],
    summary="Opening balances form",
    response_class=HTMLResponse,
)
def opening_form(request: Request):
    with db.session(DB_PATH) as conn:
        opening = db.opening_balances(conn)
    return page(request, "opening.html", opening=opening)


@app.post(
    "/opening",
    tags=["Opening balances"],
    summary="Save opening balances",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def opening_save(
    request: Request,
    ten: str = Form(description=f"10% RUB. {MONEY_DESC}"),
    everyday: str = Form(description=f"Everyday RUB. {MONEY_DESC}"),
    savings: str = Form(description=f"Savings RUB. {MONEY_DESC}"),
    ten_usd: str = Form(description=f"10% USD. {MONEY_DESC}"),
    savings_usd: str = Form(description=f"Savings USD. {MONEY_DESC}"),
    daughter: str = Form(description=f"Daughter RUB. {MONEY_DESC}"),
    daughter_usd: str = Form(description=f"Daughter USD. {MONEY_DESC}"),
    usd: str = Form(description=f"USD cash. {MONEY_DESC}"),
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


@app.get(
    "/correct",
    tags=["Corrections"],
    summary="Correct balances form",
    response_class=HTMLResponse,
)
def correct_form(request: Request):
    with db.session(DB_PATH) as conn:
        bals = db.balances(conn)
    return page(request, "correct.html", bals=bals)


@app.post(
    "/correct",
    tags=["Corrections"],
    summary="Correct one or more pot balances",
    response_class=RedirectResponse,
    status_code=303,
    responses={303: REDIRECT_303},
)
def correct_save(
    request: Request,
    occurred_on: str = Form(description=DATE_DESC),
    note: str = Form("", description="Optional note, applied to every pot corrected"),
    ten: str = Form(description=f"Corrected 10% RUB balance. {MONEY_DESC}"),
    everyday: str = Form(description=f"Corrected everyday balance. {MONEY_DESC}"),
    savings: str = Form(description=f"Corrected savings RUB balance. {MONEY_DESC}"),
    daughter: str = Form(description=f"Corrected daughter RUB balance. {MONEY_DESC}"),
    ten_usd: str = Form(description=f"Corrected 10% USD balance. {MONEY_DESC}"),
    savings_usd: str = Form(description=f"Corrected savings USD balance. {MONEY_DESC}"),
    daughter_usd: str = Form(description=f"Corrected daughter USD balance. {MONEY_DESC}"),
    usd: str = Form(description=f"Corrected USD cash balance. {MONEY_DESC}"),
):
    targets = {
        "ten": ten,
        "everyday": everyday,
        "savings": savings,
        "daughter": daughter,
        "ten_usd": ten_usd,
        "savings_usd": savings_usd,
        "daughter_usd": daughter_usd,
        "usd": usd,
    }
    try:
        target_cents = {pot: parse_money(raw) for pot, raw in targets.items()}
        with db.session(DB_PATH) as conn:
            bals = db.balances(conn)
            changed = 0
            for pot, target in target_cents.items():
                delta = target - bals[pot]
                if delta:
                    db.add_correction(conn, occurred_on, pot, delta, note.strip())
                    changed += 1
        if changed:
            flash(request, f"Corrected {changed} pot{'s' if changed != 1 else ''}.", "ok")
        else:
            flash(request, "Nothing to correct — every amount matched the current balance.", "ok")
        return RedirectResponse("/", status_code=303)
    except ValueError as exc:
        flash(request, str(exc))
        return RedirectResponse("/correct", status_code=303)


@app.get(
    "/api/ten-percent",
    tags=["JSON API"],
    summary="Calculate 10% income split",
    response_model=TenPercentResponse,
)
def api_ten(
    gross: str = Query(default="0", description=MONEY_DESC),
):
    try:
        cents = parse_money(gross)
    except ValueError:
        cents = 0
    ten = ten_percent(cents)
    return {"gross": cents, "ten": ten, "rest": cents - ten}

from __future__ import annotations

import sqlite3
from calendar import monthrange
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

SLEEVE_ACCOUNTS = ("ten", "savings", "daughter")
POTS_LOCAL = ("ten", "everyday", "savings", "daughter")
POTS_USD = ("ten_usd", "savings_usd", "daughter_usd", "usd")
POTS_ALL = POTS_LOCAL + POTS_USD
COUNT_ACCOUNTS = (
    ("ten", "10%"),
    ("savings", "Savings"),
    ("daughter", "Daughter"),
    ("everyday", "Everyday"),
    ("usd", "USD cash"),
)
ACCOUNT_POTS = {
    "ten": ("ten", "ten_usd"),
    "savings": ("savings", "savings_usd"),
    "daughter": ("daughter", "daughter_usd"),
    "everyday": ("everyday",),
    "usd": ("usd",),
}
SOURCES = ("job_5", "job_20", "extra")
EXPENSE_CATEGORIES = (
    "food", "cafes", "housing", "utilities", "transport", "health",
    "kids", "clothes", "entertainment", "subscriptions", "gifts", "other",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS opening_balances (
    pot TEXT PRIMARY KEY,
    amount_cents INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS incomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_on TEXT NOT NULL,
    gross_cents INTEGER NOT NULL,
    source TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    income_id INTEGER NOT NULL REFERENCES incomes(id) ON DELETE CASCADE,
    pot TEXT NOT NULL,
    amount_cents INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_on TEXT NOT NULL,
    pot TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fx_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_on TEXT NOT NULL,
    from_pot TEXT NOT NULL,
    local_cents INTEGER NOT NULL,
    usd_cents INTEGER NOT NULL,
    to_pot TEXT NOT NULL DEFAULT 'usd',
    rate_milli INTEGER NOT NULL DEFAULT 0,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sleeve_deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_on TEXT NOT NULL,
    account TEXT NOT NULL,
    rub_cents INTEGER NOT NULL DEFAULT 0,
    usd_cents INTEGER NOT NULL DEFAULT 0,
    rate_milli INTEGER NOT NULL DEFAULT 0,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    fx_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(fx_trades)").fetchall()
    }
    if "to_pot" not in fx_columns:
        conn.execute("ALTER TABLE fx_trades ADD COLUMN to_pot TEXT NOT NULL DEFAULT 'usd'")
    if "rate_milli" not in fx_columns:
        conn.execute("ALTER TABLE fx_trades ADD COLUMN rate_milli INTEGER NOT NULL DEFAULT 0")
    conn.execute(
        """
        UPDATE fx_trades
        SET rate_milli = ROUND(local_cents * 1000.0 / usd_cents)
        WHERE rate_milli = 0 AND usd_cents > 0
        """
    )
    for pot in POTS_ALL:
        conn.execute(
            "INSERT OR IGNORE INTO opening_balances(pot, amount_cents) VALUES(?, 0)",
            (pot,),
        )
    conn.commit()
    return conn


@contextmanager
def session(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def month_bounds(year: int, month: int) -> tuple[str, str]:
    last = monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last:02d}"


def _sum(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0] or 0)


def balances(conn: sqlite3.Connection) -> dict[str, int]:
    out = {
        pot: _sum(conn, "SELECT amount_cents FROM opening_balances WHERE pot=?", (pot,))
        for pot in POTS_ALL
    }
    for pot in POTS_LOCAL:
        out[pot] += _sum(
            conn,
            "SELECT COALESCE(SUM(amount_cents),0) FROM allocations WHERE pot=?",
            (pot,),
        )
        out[pot] -= _sum(
            conn,
            "SELECT COALESCE(SUM(amount_cents),0) FROM expenses WHERE pot=?",
            (pot,),
        )
        out[pot] -= _sum(
            conn,
            "SELECT COALESCE(SUM(local_cents),0) FROM fx_trades WHERE from_pot=?",
            (pot,),
        )
    for account in SLEEVE_ACCOUNTS:
        out[account] += _sum(
            conn,
            "SELECT COALESCE(SUM(rub_cents),0) FROM sleeve_deposits WHERE account=?",
            (account,),
        )
        usd_pot = f"{account}_usd"
        out[usd_pot] += _sum(
            conn,
            "SELECT COALESCE(SUM(usd_cents),0) FROM sleeve_deposits WHERE account=?",
            (account,),
        )
    for pot in POTS_USD:
        out[pot] += _sum(
            conn,
            "SELECT COALESCE(SUM(usd_cents),0) FROM fx_trades WHERE to_pot=?",
            (pot,),
        )
        out[pot] -= _sum(
            conn,
            "SELECT COALESCE(SUM(amount_cents),0) FROM expenses WHERE pot=?",
            (pot,),
        )
    return out


def month_summary(conn: sqlite3.Connection, year: int, month: int) -> dict[str, Any]:
    start, end = month_bounds(year, month)
    ten = _sum(
        conn,
        """
        SELECT COALESCE(SUM(a.amount_cents),0)
        FROM allocations a
        JOIN incomes i ON i.id = a.income_id
        WHERE a.pot='ten' AND i.occurred_on BETWEEN ? AND ?
        """,
        (start, end),
    )
    savings = _sum(
        conn,
        """
        SELECT COALESCE(SUM(a.amount_cents),0)
        FROM allocations a
        JOIN incomes i ON i.id = a.income_id
        WHERE a.pot='savings' AND i.occurred_on BETWEEN ? AND ?
        """,
        (start, end),
    )
    usd_bought = _sum(
        conn,
        "SELECT COALESCE(SUM(usd_cents),0) FROM fx_trades WHERE occurred_on BETWEEN ? AND ?",
        (start, end),
    )
    usd_local = _sum(
        conn,
        """
        SELECT COALESCE(SUM(local_cents),0) FROM fx_trades
        WHERE occurred_on BETWEEN ? AND ? AND from_pot='everyday'
        """,
        (start, end),
    )
    spent_local = _sum(
        conn,
        """
        SELECT COALESCE(SUM(amount_cents),0) FROM expenses
        WHERE occurred_on BETWEEN ? AND ?
          AND pot NOT IN ('usd', 'ten_usd', 'savings_usd', 'daughter_usd')
        """,
        (start, end),
    )
    spent_usd = _sum(
        conn,
        """
        SELECT COALESCE(SUM(amount_cents),0) FROM expenses
        WHERE occurred_on BETWEEN ? AND ?
          AND pot IN ('usd', 'ten_usd', 'savings_usd', 'daughter_usd')
        """,
        (start, end),
    )
    income_gross = _sum(
        conn,
        "SELECT COALESCE(SUM(gross_cents),0) FROM incomes WHERE occurred_on BETWEEN ? AND ?",
        (start, end),
    )
    everyday = _sum(
        conn,
        """
        SELECT COALESCE(SUM(a.amount_cents),0)
        FROM allocations a
        JOIN incomes i ON i.id = a.income_id
        WHERE a.pot='everyday' AND i.occurred_on BETWEEN ? AND ?
        """,
        (start, end),
    )
    return {
        "ten": ten,
        "savings": savings,
        "everyday": everyday,
        "saved_local": ten + savings + usd_local,
        "usd_bought": usd_bought,
        "usd_local": usd_local,
        "spent_local": spent_local,
        "spent_usd": spent_usd,
        "income_gross": income_gross,
        "start": start,
        "end": end,
    }


def _validate_income_split(source: str, gross_cents: int, ten: int, everyday: int, savings: int) -> None:
    if source not in SOURCES:
        raise ValueError("Unknown income source")
    if ten + everyday + savings != gross_cents:
        raise ValueError("10% + everyday + savings must equal the income")
    if min(ten, everyday, savings) < 0:
        raise ValueError("Split amounts cannot be negative")


def add_income(
    conn: sqlite3.Connection,
    occurred_on: str,
    gross_cents: int,
    source: str,
    note: str,
    ten: int,
    everyday: int,
    savings: int,
) -> int:
    _validate_income_split(source, gross_cents, ten, everyday, savings)
    cur = conn.execute(
        """
        INSERT INTO incomes(occurred_on, gross_cents, source, note, created_at)
        VALUES(?,?,?,?,?)
        """,
        (occurred_on, gross_cents, source, note, datetime.now().isoformat(timespec="seconds")),
    )
    income_id = int(cur.lastrowid)
    for pot, amount in (("ten", ten), ("everyday", everyday), ("savings", savings)):
        conn.execute(
            "INSERT INTO allocations(income_id, pot, amount_cents) VALUES(?,?,?)",
            (income_id, pot, amount),
        )
    return income_id


def get_income(conn: sqlite3.Connection, income_id: int) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT i.*,
               SUM(CASE WHEN a.pot='ten' THEN a.amount_cents ELSE 0 END) AS ten_cents,
               SUM(CASE WHEN a.pot='everyday' THEN a.amount_cents ELSE 0 END) AS everyday_cents,
               SUM(CASE WHEN a.pot='savings' THEN a.amount_cents ELSE 0 END) AS savings_cents
        FROM incomes i
        JOIN allocations a ON a.income_id = i.id
        WHERE i.id = ?
        GROUP BY i.id
        """,
        (income_id,),
    ).fetchone()


def update_income(
    conn: sqlite3.Connection,
    income_id: int,
    occurred_on: str,
    gross_cents: int,
    source: str,
    note: str,
    ten: int,
    everyday: int,
    savings: int,
) -> None:
    existing = get_income(conn, income_id)
    if existing is None:
        raise ValueError("Income not found")
    _validate_income_split(source, gross_cents, ten, everyday, savings)
    bals = balances(conn)
    bals["ten"] += ten - int(existing["ten_cents"])
    bals["everyday"] += everyday - int(existing["everyday_cents"])
    bals["savings"] += savings - int(existing["savings_cents"])
    if min(bals["ten"], bals["everyday"], bals["savings"]) < 0:
        raise ValueError("This split would make a pot go negative")
    conn.execute(
        """
        UPDATE incomes
        SET occurred_on=?, gross_cents=?, source=?, note=?
        WHERE id=?
        """,
        (occurred_on, gross_cents, source, note, income_id),
    )
    conn.execute("DELETE FROM allocations WHERE income_id=?", (income_id,))
    for pot, amount in (("ten", ten), ("everyday", everyday), ("savings", savings)):
        conn.execute(
            "INSERT INTO allocations(income_id, pot, amount_cents) VALUES(?,?,?)",
            (income_id, pot, amount),
        )


def get_expense(conn: sqlite3.Connection, expense_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM expenses WHERE id=?", (expense_id,)).fetchone()


def _require_expense_fields(pot: str, amount_cents: int, category: str) -> None:
    if pot not in POTS_ALL:
        raise ValueError("Unknown pot")
    if amount_cents <= 0:
        raise ValueError("Expense must be greater than zero")
    if category not in EXPENSE_CATEGORIES:
        raise ValueError("Choose an expense category")


def add_expense(
    conn: sqlite3.Connection,
    occurred_on: str,
    pot: str,
    amount_cents: int,
    category: str,
    note: str,
    confirmed_ten: bool,
) -> int:
    _require_expense_fields(pot, amount_cents, category)
    if pot in ("ten", "ten_usd") and not confirmed_ten:
        raise ValueError("Spending from the 10% pot needs an extra confirmation")
    bals = balances(conn)
    if bals[pot] < amount_cents:
        raise ValueError("Not enough money in that pot")
    cur = conn.execute(
        """
        INSERT INTO expenses(occurred_on, pot, amount_cents, category, note, created_at)
        VALUES(?,?,?,?,?,?)
        """,
        (
            occurred_on,
            pot,
            amount_cents,
            category,
            note,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    return int(cur.lastrowid)


def update_expense(
    conn: sqlite3.Connection,
    expense_id: int,
    occurred_on: str,
    pot: str,
    amount_cents: int,
    category: str,
    note: str,
    confirmed_ten: bool,
) -> None:
    existing = get_expense(conn, expense_id)
    if existing is None:
        raise ValueError("Expense not found")
    _require_expense_fields(pot, amount_cents, category)
    switching_into_ten = pot in ("ten", "ten_usd") and existing["pot"] != pot
    if switching_into_ten and not confirmed_ten:
        raise ValueError("Spending from the 10% pot needs an extra confirmation")
    bals = balances(conn)
    bals[existing["pot"]] += int(existing["amount_cents"])
    if bals[pot] < amount_cents:
        raise ValueError("Not enough money in that pot")
    conn.execute(
        """
        UPDATE expenses
        SET occurred_on=?, pot=?, amount_cents=?, category=?, note=?
        WHERE id=?
        """,
        (occurred_on, pot, amount_cents, category, note, expense_id),
    )


def add_fx(
    conn: sqlite3.Connection,
    occurred_on: str,
    from_pot: str,
    local_cents: int,
    usd_cents: int,
    note: str,
    to_pot: str = "usd",
    rate_milli: int | None = None,
) -> int:
    allowed = {
        ("everyday", "usd"),
        ("ten", "ten_usd"),
        ("savings", "savings_usd"),
        ("daughter", "daughter_usd"),
    }
    if (from_pot, to_pot) not in allowed:
        raise ValueError("The RUB and USD sleeves must belong to the same account")
    if local_cents <= 0 or usd_cents <= 0:
        raise ValueError("Both local spent and USD received must be greater than zero")
    bals = balances(conn)
    if bals[from_pot] < local_cents:
        raise ValueError("Not enough money in that pot")
    calculated_rate = round(local_cents * 1000 / usd_cents)
    if rate_milli and abs(rate_milli - calculated_rate) > 5:
        raise ValueError("Rate does not match the RUB and USD amounts")
    actual_rate = calculated_rate
    if actual_rate <= 0:
        raise ValueError("Rate must be greater than zero")
    cur = conn.execute(
        """
        INSERT INTO fx_trades(
            occurred_on, from_pot, local_cents, usd_cents,
            to_pot, rate_milli, note, created_at
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            occurred_on,
            from_pot,
            local_cents,
            usd_cents,
            to_pot,
            actual_rate,
            note,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    return int(cur.lastrowid)


def add_sleeve_deposit(
    conn: sqlite3.Connection,
    occurred_on: str,
    account: str,
    rub_cents: int,
    usd_cents: int,
    rate_milli: int,
    note: str,
) -> int:
    if account not in SLEEVE_ACCOUNTS:
        raise ValueError("Choose the 10%, savings, or daughter account")
    if rub_cents < 0 or usd_cents < 0 or (rub_cents == 0 and usd_cents == 0):
        raise ValueError("Add a RUB or USD amount")
    if usd_cents > 0 and rate_milli <= 0:
        raise ValueError("Rate is required when adding USD")
    cur = conn.execute(
        """
        INSERT INTO sleeve_deposits(
            occurred_on, account, rub_cents, usd_cents, rate_milli, note, created_at
        ) VALUES(?,?,?,?,?,?,?)
        """,
        (
            occurred_on,
            account,
            rub_cents,
            usd_cents,
            rate_milli,
            note,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    return int(cur.lastrowid)


def set_opening(conn: sqlite3.Connection, amounts: dict[str, int]) -> None:
    for pot, amount in amounts.items():
        if pot not in POTS_ALL:
            raise ValueError("Unknown pot")
        if amount < 0:
            raise ValueError("Opening balance cannot be negative")
        conn.execute(
            "UPDATE opening_balances SET amount_cents=? WHERE pot=?",
            (amount, pot),
        )


def opening_balances(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT pot, amount_cents FROM opening_balances").fetchall()
    return {row["pot"]: int(row["amount_cents"]) for row in rows}


def list_incomes(conn: sqlite3.Connection, start: str, end: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT i.*,
               SUM(CASE WHEN a.pot='ten' THEN a.amount_cents ELSE 0 END) AS ten_cents,
               SUM(CASE WHEN a.pot='everyday' THEN a.amount_cents ELSE 0 END) AS everyday_cents,
               SUM(CASE WHEN a.pot='savings' THEN a.amount_cents ELSE 0 END) AS savings_cents
        FROM incomes i
        JOIN allocations a ON a.income_id = i.id
        WHERE i.occurred_on BETWEEN ? AND ?
        GROUP BY i.id
        ORDER BY i.occurred_on DESC, i.id DESC
        """,
        (start, end),
    ).fetchall()


def list_expenses(conn: sqlite3.Connection, start: str, end: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT * FROM expenses
        WHERE occurred_on BETWEEN ? AND ?
        ORDER BY occurred_on DESC, id DESC
        """,
        (start, end),
    ).fetchall()


def list_fx(conn: sqlite3.Connection, start: str, end: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT * FROM fx_trades
        WHERE occurred_on BETWEEN ? AND ?
        ORDER BY occurred_on DESC, id DESC
        """,
        (start, end),
    ).fetchall()


def list_sleeve_deposits(
    conn: sqlite3.Connection, start: str, end: str
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT * FROM sleeve_deposits
        WHERE occurred_on BETWEEN ? AND ?
        ORDER BY occurred_on DESC, id DESC
        """,
        (start, end),
    ).fetchall()


def rate_history(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT occurred_on, from_pot AS account, local_cents, usd_cents,
               rate_milli, 'conversion' AS kind
        FROM fx_trades
        UNION ALL
        SELECT occurred_on, account, 0 AS local_cents, usd_cents,
               rate_milli, 'deposit' AS kind
        FROM sleeve_deposits
        WHERE usd_cents > 0
        ORDER BY occurred_on DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def spend_by_category(conn: sqlite3.Connection, start: str, end: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT CASE WHEN category = '' THEN 'uncategorized' ELSE category END AS category,
               SUM(amount_cents) AS amount_cents
        FROM expenses
        WHERE occurred_on BETWEEN ? AND ?
          AND pot NOT IN ('usd', 'ten_usd', 'savings_usd', 'daughter_usd')
        GROUP BY 1
        ORDER BY amount_cents DESC
        """,
        (start, end),
    ).fetchall()
    return [{"category": row["category"], "amount_cents": int(row["amount_cents"])} for row in rows]


def excluded_accounts(conn: sqlite3.Connection) -> set[str]:
    row = conn.execute(
        "SELECT value FROM settings WHERE key='excluded_accounts'"
    ).fetchone()
    if not row or not row["value"]:
        return set()
    return {item for item in row["value"].split(",") if item in ACCOUNT_POTS}


def toggle_excluded_account(conn: sqlite3.Connection, account: str) -> set[str]:
    if account not in ACCOUNT_POTS:
        raise ValueError("Unknown account")
    current = excluded_accounts(conn)
    if account in current:
        current.remove(account)
    else:
        current.add(account)
    conn.execute(
        """
        INSERT INTO settings(key, value) VALUES('excluded_accounts', ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (",".join(sorted(current)),),
    )
    return current


def today_iso() -> str:
    return date.today().isoformat()

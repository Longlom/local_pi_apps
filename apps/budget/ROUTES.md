# Rasp Budget — Route Reference

All 19 endpoints exposed by `app.py`. Every mutating route follows the same
shape: validate in Python, write inside one `db.session()` transaction,
flash a message into the signed session cookie, then issue a 303 redirect
(so a page reload never resubmits a form).

**Notation** — `field:type`, a trailing `?` marks optional.
`money` = decimal string (`"1234.56"`) parsed to integer cents ·
`date` = `YYYY-MM-DD` · `enum{…}` = fixed set of values.

## State model

```
RUB pot balance = opening + income allocations + sleeve deposits (RUB)
                  + transfers in (savings accounts only)
                  − expenses − USD purchased from here − transfers out (everyday)

USD pot balance = opening + USD purchased into here + sleeve deposits (USD)
                  − expenses
```

---

## Dashboard

### `GET /`
Renders `month.html`.

- **Query:** `month:date?` (`YYYY-MM`, defaults to the current month) ·
  `detail:enum{ten|saved|spent}?` — drill-down for the three headline cards
- **Reads:** balances, `month_summary`, incomes/expenses/fx_trades/sleeve_deposits
  for the range, line-item details when `detail` is set, `rate_history`,
  `spend_by_category`, `excluded_accounts`, plus a live `fx.usd_to_rub()` quote.
  No writes.

**Headline drill-down** (`/?month=YYYY-MM&detail=saved` etc.): lists every
transaction that makes up that month's **Into 10%**, **Managed to save**, or
**Spent** total, with dates and amounts. Income and expense rows link to edit.

---

## Income

Every paycheck is split three ways at entry time: into the 10% pot, everyday
spending, and savings.

### `GET /income`
Renders `income.html` (blank).

### `POST /income`
- **Payload:** `occurred_on:date` · `source:enum{job_5|job_20|extra}` ·
  `gross:money` · `ten:money` · `everyday:money` · `savings:money` · `note:text?`
- **Rule:** `ten + everyday + savings` must equal `gross` exactly, none may be negative.
- **Writes:** `incomes` (1 row) + `allocations` (3 rows: ten, everyday, savings)
- **Response:** redirect `/` (ok) · redirect `/income` (error, flashed)

### `GET /income/{id}`
Renders `income.html` prefilled. Unknown id flashes "Income not found." and
redirects to `/`.

### `POST /income/{id}`
- **Payload:** same 7 fields as create
- **Rule:** same split rule, plus: the pot deltas (new minus old split) are
  re-applied to current balances and rejected if any pot would go negative.
- **Writes:** `UPDATE incomes` · `DELETE` + re-`INSERT allocations`

---

## Expense

Spends straight from a pot; the 10% pot gets an extra confirmation because
it isn't meant to be touched casually.

### `GET /expense`
Renders `expense.html` (12 categories).

### `POST /expense`
- **Payload:** `occurred_on:date` · `pot:enum{8 pots}` · `amount:money` ·
  `category:enum{12}` · `note:text?` · `confirm_ten:bool?`
- **Rule:** `amount > 0`; category required; spending from `ten` / `ten_usd`
  needs `confirm_ten` checked; the pot must hold enough.
- **Writes:** `expenses` (1 row)
- **Response:** redirect `/` (ok) · redirect `/expense` (error)

### `GET /expense/{id}`
Renders `expense.html` prefilled.

### `POST /expense/{id}`
- **Payload:** same fields as create
- **Rule:** `confirm_ten` is only required when the edit moves the expense
  into `ten` / `ten_usd` from a different pot; the balance check credits
  back the row's old amount first.
- **Writes:** `UPDATE expenses`

---

## Transfers

Move rubles from Everyday into a savings account without counting it as
spending.

### `GET /transfer`
Renders `transfer.html`.

- **Query:** `to:enum{ten|savings|daughter} = savings`

### `POST /transfer`
- **Payload:** `occurred_on:date` · `to_pot:enum{ten|savings|daughter}` ·
  `amount:money` · `note:text?`
- **Rule:** `amount > 0`; everyday must hold enough.
- **Writes:** `transfers` (1 row)
- **Response:** redirect `/` (ok) · redirect `/transfer?to=…` (error)

Transfers appear in the month ledger under **Income** and count toward
**Managed to save** for the month.

---

## USD purchase

Turns everyday RUB into physical USD cash. The exchange rate is never
entered — it's derived from the two amounts.

### `GET /usd`
Renders `usd.html` (blank).

### `POST /usd`
- **Payload:** `occurred_on:date` · `from_pot:text` (usually `everyday`) ·
  `local_spent:money` · `usd_got:money` · `note:text?`
- **Rule:** `(from_pot → usd)` must be an allowed pair, both amounts `> 0`,
  and `from_pot` must hold enough. Rate is computed as
  `local_cents × 1000 ÷ usd_cents`.
- **Writes:** `fx_trades` (1 row, `to_pot = "usd"`)

---

## Sleeves — 10% / savings / daughter

Each of these three accounts carries a RUB sleeve and a USD sleeve. This is
the only screen with two payload shapes behind one form, switched by `mode`.

### `GET /sleeves`
Renders `sleeves.html`.

- **Query:** `account:enum{ten|savings|daughter} = ten`

### `POST /sleeves`
- **Payload:** `occurred_on:date` · `account:enum{ten|savings|daughter}` ·
  `mode:enum{conversion|deposit}` · `rub_amount:money?` · `usd_amount:money?` ·
  `rate:text?` · `note:text?`
- **`mode=conversion`:** same-account RUB→USD, like the `/usd` flow but
  scoped to this sleeve. Both amounts required; a supplied rate is checked
  against the calculated one (±5‰ tolerance) before it's accepted.
  Writes `fx_trades` (`to_pot = account_usd`).
- **`mode=deposit`:** a direct top-up — money that didn't come from another
  pot (a gift, a manual correction). Needs a RUB or USD amount (not both
  zero); a rate is required only if `usd_amount > 0`.
  Writes `sleeve_deposits` (1 row).
- **Response:** redirect `/` (ok) · redirect `/sleeves?account=…` (error)

---

## Opening balances

The zero-point every later income, expense, and trade stacks on top of —
see the balance formulas above.

### `GET /opening`
Renders `opening.html` prefilled.

### `POST /opening`
- **Payload:** `ten:money` · `everyday:money` · `savings:money` ·
  `ten_usd:money` · `savings_usd:money` · `daughter:money` ·
  `daughter_usd:money` · `usd:money` (all 8 required)
- **Rule:** every amount must be non-negative.
- **Writes:** `UPDATE opening_balances` (8 rows)

---

## Balance corrections

When a pot balance drifts from reality (bank fees, rounding, cash on hand),
set what each account **should** be today. Only changed pots get a correction
row; the delta is applied on top of the normal balance formula.

### `GET /correct`
Renders `correct.html` with current balances prefilled for all 8 pots.

### `POST /correct`
- **Payload:** `occurred_on:date` · `note:text` · `ten:money` · `everyday:money`
  · `savings:money` · `daughter:money` · `ten_usd:money` · `savings_usd:money`
  · `daughter_usd:money` · `usd:money` (all 8 required)
- **Rule:** each target must be non-negative; unchanged pots are skipped.
- **Writes:** one `corrections` row per pot whose target differs from the
  current balance (`delta_cents = target − current`).
- **Response:** redirect `/` (ok) · redirect `/correct` (error)

Corrections appear in the month ledger: negative deltas under **Spends**,
positive under **Income**.

---

## Settings

One toggle: drop an account out of the "total counted" figure without
touching its balance.

### `POST /exclude`
- **Payload:** `account:enum{ten|savings|daughter|everyday|usd}`
- **Writes:** toggles a row in `settings`
- **Response:** redirect back to `Referer` (`safe_back`, path-only)

---

## JSON API

The one non-HTML response — powers the live 10% split preview on the
income form as you type.

### `GET /api/ten-percent`
Returns `application/json`.

- **Query:** `gross:money = "0"`
- **Returns:** `{ gross, ten, rest }` — pure calculation via
  `money.ten_percent()`, no DB access

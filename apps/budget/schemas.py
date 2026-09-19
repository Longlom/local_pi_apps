"""OpenAPI models and metadata for the budget app."""

from __future__ import annotations

from pydantic import BaseModel, Field

DESCRIPTION = """
Family budget tracker for LAN use.

Most routes render HTML forms or return **303 redirects** after a write.
Mutating routes validate in Python, persist inside one database transaction,
flash a message into the signed session cookie, then redirect so reload never
resubmits a form.

**Money fields** are decimal strings (`"1234.56"`) parsed to integer cents.
**Dates** use `YYYY-MM-DD`; month filters use `YYYY-MM`.

### Balance model

```
RUB pot = opening + income allocations + sleeve deposits (RUB)
          + transfers in (savings accounts)
          − expenses − USD purchased from here − transfers out (everyday)

USD pot = opening + USD purchased into here + sleeve deposits (USD)
          − expenses
```
"""

TAGS = [
    {
        "name": "Dashboard",
        "description": "Monthly overview with balances, flows, and charts.",
    },
    {
        "name": "Income",
        "description": "Record paychecks split across 10%, everyday, and savings pots.",
    },
    {
        "name": "Expense",
        "description": "Spend from a pot; 10% pots require explicit confirmation.",
    },
    {
        "name": "Transfers",
        "description": "Move RUB from everyday into a savings account (10%, savings, daughter).",
    },
    {
        "name": "USD purchase",
        "description": "Convert everyday RUB into physical USD cash.",
    },
    {
        "name": "Sleeves",
        "description": "RUB/USD sleeve conversions and direct deposits for ten, savings, daughter.",
    },
    {
        "name": "Opening balances",
        "description": "Set the zero-point every later transaction stacks on.",
    },
    {
        "name": "Corrections",
        "description": "Nudge any pot's balance to match reality (cash counts, bank drift) without touching opening balances.",
    },
    {
        "name": "Settings",
        "description": "Toggle accounts excluded from total-counted figures.",
    },
    {
        "name": "JSON API",
        "description": "Non-HTML endpoints for live UI calculations.",
    },
]

MONEY_DESC = 'Decimal string, e.g. `"1234.56"` (parsed to integer cents)'
DATE_DESC = "ISO date `YYYY-MM-DD`"
MONTH_DESC = "Month filter `YYYY-MM` (defaults to current month)"

POT_ENUM = "ten | ten_usd | everyday | savings | savings_usd | daughter | daughter_usd | usd"
SOURCE_ENUM = "job_5 | job_20 | extra"
CATEGORY_ENUM = (
    "food | cafes | housing | utilities | transport | health | "
    "kids | clothes | entertainment | subscriptions | gifts | other"
)
SLEEVE_ACCOUNT_ENUM = "ten | savings | daughter"
TRANSFER_TO_ENUM = SLEEVE_ACCOUNT_ENUM
EXCLUDE_ACCOUNT_ENUM = "ten | savings | daughter | everyday | usd"
SLEEVE_MODE_ENUM = "conversion | deposit"

REDIRECT_303 = {
    "description": "Redirect after successful write or validation error (flash message in session).",
}


class TenPercentResponse(BaseModel):
    gross: int = Field(..., description="Gross amount in cents")
    ten: int = Field(..., description="10% allocation in cents")
    rest: int = Field(..., description="Remainder after 10% in cents")

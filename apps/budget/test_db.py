import tempfile
import unittest
import sqlite3
from pathlib import Path

import db
from money import parse_money, ten_percent


class BudgetDbTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "t.sqlite"
        self.conn = db.connect(self.path)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_income_split_and_month(self):
        gross = parse_money("10000")
        ten = ten_percent(gross)
        everyday = parse_money("6000")
        savings = gross - ten - everyday
        db.add_income(self.conn, "2026-09-05", gross, "job_5", "", ten, everyday, savings)
        bals = db.balances(self.conn)
        self.assertEqual(bals["ten"], ten)
        self.assertEqual(bals["everyday"], everyday)
        self.assertEqual(bals["savings"], savings)
        summary = db.month_summary(self.conn, 2026, 9)
        self.assertEqual(summary["ten"], ten)
        self.assertEqual(summary["saved_local"], ten + savings)
        db.add_expense(
            self.conn, "2026-09-06", "everyday", parse_money("500"), "food", "", False
        )
        self.assertEqual(db.balances(self.conn)["everyday"], everyday - parse_money("500"))
        summary = db.month_summary(self.conn, 2026, 9)
        self.assertEqual(summary["spent_local"], parse_money("500"))

    def test_ten_needs_confirm(self):
        db.add_income(
            self.conn, "2026-09-20", 10000, "job_20", "", 1000, 5000, 4000
        )
        with self.assertRaises(ValueError):
            db.add_expense(self.conn, "2026-09-21", "ten", 100, "other", "", False)

    def test_fx_is_not_spend(self):
        db.add_income(
            self.conn, "2026-09-20", 10000, "job_20", "", 1000, 5000, 4000
        )
        db.add_fx(self.conn, "2026-09-21", "everyday", 2000, 50, "")
        bals = db.balances(self.conn)
        self.assertEqual(bals["everyday"], 3000)
        self.assertEqual(bals["usd"], 50)
        summary = db.month_summary(self.conn, 2026, 9)
        self.assertEqual(summary["spent_local"], 0)
        self.assertEqual(summary["usd_bought"], 50)
        self.assertEqual(summary["saved_local"], 1000 + 4000 + 2000)

    def test_ten_and_savings_have_separate_usd_sleeves_and_rates(self):
        db.add_income(
            self.conn, "2026-09-20", 100000, "job_20", "", 10000, 50000, 40000
        )
        db.add_fx(
            self.conn,
            "2026-09-21",
            "ten",
            9000,
            100,
            "",
            to_pot="ten_usd",
            rate_milli=90000,
        )
        db.add_fx(
            self.conn,
            "2026-09-22",
            "savings",
            18200,
            200,
            "",
            to_pot="savings_usd",
            rate_milli=91000,
        )
        bals = db.balances(self.conn)
        self.assertEqual(bals["ten"], 1000)
        self.assertEqual(bals["ten_usd"], 100)
        self.assertEqual(bals["savings"], 21800)
        self.assertEqual(bals["savings_usd"], 200)
        self.assertEqual(bals["usd"], 0)
        rates = db.rate_history(self.conn)
        self.assertEqual([row["rate_milli"] for row in rates], [91000, 90000])

    def test_external_deposits_add_rub_and_usd_to_each_account(self):
        db.add_sleeve_deposit(
            self.conn, "2026-09-21", "ten", 5000, 100, 92500, "cash"
        )
        db.add_sleeve_deposit(
            self.conn, "2026-09-22", "savings", 7000, 200, 93000, "bank"
        )
        bals = db.balances(self.conn)
        self.assertEqual(bals["ten"], 5000)
        self.assertEqual(bals["ten_usd"], 100)
        self.assertEqual(bals["savings"], 7000)
        self.assertEqual(bals["savings_usd"], 200)

    def test_usd_sleeve_spending_and_categories(self):
        db.set_opening(self.conn, {"ten_usd": 1000, "savings_usd": 1000})
        with self.assertRaisesRegex(ValueError, "extra confirmation"):
            db.add_expense(
                self.conn, "2026-09-21", "ten_usd", 100, "food", "", False
            )
        db.add_expense(
            self.conn, "2026-09-21", "savings_usd", 100, "food", "", False
        )
        self.assertEqual(db.balances(self.conn)["savings_usd"], 900)
        with self.assertRaisesRegex(ValueError, "category"):
            db.add_expense(
                self.conn, "2026-09-21", "savings_usd", 100, "random", "", False
            )

    def test_rate_must_match_conversion_amounts(self):
        db.set_opening(self.conn, {"savings": 10000})
        with self.assertRaisesRegex(ValueError, "does not match"):
            db.add_fx(
                self.conn,
                "2026-09-21",
                "savings",
                9000,
                100,
                "",
                to_pot="savings_usd",
                rate_milli=80000,
            )

    def test_existing_database_is_migrated_without_losing_fx(self):
        legacy_path = Path(self.tmp.name) / "legacy.sqlite"
        legacy = sqlite3.connect(legacy_path)
        legacy.executescript(
            """
            CREATE TABLE fx_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_on TEXT NOT NULL,
                from_pot TEXT NOT NULL,
                local_cents INTEGER NOT NULL,
                usd_cents INTEGER NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            INSERT INTO fx_trades(
                occurred_on, from_pot, local_cents, usd_cents, note, created_at
            ) VALUES('2026-09-01', 'everyday', 9000, 100, '', '2026-09-01');
            """
        )
        legacy.commit()
        legacy.close()
        migrated = db.connect(legacy_path)
        row = migrated.execute("SELECT * FROM fx_trades").fetchone()
        self.assertEqual(row["to_pot"], "usd")
        self.assertEqual(row["rate_milli"], 90000)
        self.assertIn("ten_usd", db.opening_balances(migrated))
        self.assertIn("savings_usd", db.opening_balances(migrated))
        self.assertIn("daughter_usd", db.opening_balances(migrated))
        migrated.close()

    def test_daughter_account_has_separate_sleeves(self):
        db.add_sleeve_deposit(
            self.conn, "2026-09-21", "daughter", 3000, 50, 90000, "gift"
        )
        bals = db.balances(self.conn)
        self.assertEqual(bals["daughter"], 3000)
        self.assertEqual(bals["daughter_usd"], 50)
        db.add_fx(
            self.conn,
            "2026-09-22",
            "daughter",
            1800,
            20,
            "",
            to_pot="daughter_usd",
            rate_milli=90000,
        )
        bals = db.balances(self.conn)
        self.assertEqual(bals["daughter"], 1200)
        self.assertEqual(bals["daughter_usd"], 70)
        db.add_expense(
            self.conn, "2026-09-23", "daughter", 200, "kids", "toy", False
        )
        self.assertEqual(db.balances(self.conn)["daughter"], 1000)

    def test_excluded_accounts_persist_and_toggle(self):
        self.assertEqual(db.excluded_accounts(self.conn), set())
        db.toggle_excluded_account(self.conn, "daughter")
        db.toggle_excluded_account(self.conn, "ten")
        self.assertEqual(db.excluded_accounts(self.conn), {"daughter", "ten"})
        db.toggle_excluded_account(self.conn, "daughter")
        self.assertEqual(db.excluded_accounts(self.conn), {"ten"})
        self.conn.commit()
        again = db.connect(self.path)
        self.assertEqual(db.excluded_accounts(again), {"ten"})
        again.close()
        with self.assertRaises(ValueError):
            db.toggle_excluded_account(self.conn, "nope")

    def test_month_saved_details_lists_all_parts(self):
        db.add_income(
            self.conn, "2026-09-05", 10000, "job_5", "", 1000, 5000, 4000
        )
        db.add_transfer(self.conn, "2026-09-10", "daughter", 2000, "")
        db.add_fx(self.conn, "2026-09-12", "everyday", 3000, 30, "")
        items = db.month_saved_details(
            self.conn, "2026-09-01", "2026-09-30"
        )
        kinds = {item["kind"] for item in items}
        self.assertEqual(kinds, {"income_ten", "income_savings", "transfer", "usd_buy"})
        self.assertEqual(
            sum(item["amount_cents"] for item in items),
            1000 + 4000 + 2000 + 3000,
        )
        ten_only = db.month_ten_details(self.conn, "2026-09-01", "2026-09-30")
        self.assertEqual(len(ten_only), 1)
        self.assertEqual(ten_only[0]["amount_cents"], 1000)

    def test_monthly_flow_history_accumulates(self):
        db.add_income(
            self.conn, "2026-08-20", 10000, "job_20", "", 1000, 5000, 4000
        )
        db.add_income(
            self.conn, "2026-09-20", 20000, "job_20", "", 2000, 8000, 10000
        )
        db.add_expense(
            self.conn, "2026-09-21", "everyday", 1500, "food", "", False
        )
        history = db.monthly_flow_history(self.conn)
        self.assertEqual(len(history), 2)
        aug, sep = history
        self.assertEqual(aug["ym"], "2026-08")
        self.assertEqual(aug["ten"], 1000)
        self.assertEqual(aug["ten_cum"], 1000)
        self.assertEqual(sep["ten"], 2000)
        self.assertEqual(sep["ten_cum"], 3000)
        self.assertEqual(sep["spent_local"], 1500)
        self.assertEqual(sep["spent_cum"], 1500)

    def test_transfer_moves_rub_from_everyday_to_savings(self):
        db.set_opening(self.conn, {"everyday": 10000})
        db.add_transfer(self.conn, "2026-09-21", "savings", 3000, "monthly top-up")
        db.add_transfer(self.conn, "2026-09-22", "ten", 1000, "")
        bals = db.balances(self.conn)
        self.assertEqual(bals["everyday"], 6000)
        self.assertEqual(bals["savings"], 3000)
        self.assertEqual(bals["ten"], 1000)
        summary = db.month_summary(self.conn, 2026, 9)
        self.assertEqual(summary["transferred"], 4000)
        self.assertEqual(summary["saved_local"], 4000)
        with self.assertRaisesRegex(ValueError, "Not enough"):
            db.add_transfer(self.conn, "2026-09-23", "daughter", 7000, "")
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            db.add_transfer(self.conn, "2026-09-23", "daughter", 0, "")

    def test_correction_adjusts_balance(self):
        db.set_opening(self.conn, {"everyday": 5000, "savings": 10000})
        db.add_correction(
            self.conn, "2026-09-21", "everyday", 500, "found cash"
        )
        db.add_correction(
            self.conn, "2026-09-22", "savings", -2000, "bank fee"
        )
        bals = db.balances(self.conn)
        self.assertEqual(bals["everyday"], 5500)
        self.assertEqual(bals["savings"], 8000)
        rows = db.list_corrections(self.conn, 2026, 9)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["delta_cents"], -2000)
        with self.assertRaisesRegex(ValueError, "matches the current balance"):
            db.add_correction(self.conn, "2026-09-23", "everyday", 0, "")

    def test_income_and_expense_can_be_deleted(self):
        income_id = db.add_income(
            self.conn, "2026-09-20", 10000, "job_20", "", 1000, 5000, 4000
        )
        expense_id = db.add_expense(
            self.conn, "2026-09-21", "everyday", 500, "food", "", False
        )
        db.delete_expense(self.conn, expense_id)
        self.assertIsNone(db.get_expense(self.conn, expense_id))
        self.assertEqual(db.balances(self.conn)["everyday"], 5000)
        db.delete_income(self.conn, income_id)
        self.assertIsNone(db.get_income(self.conn, income_id))
        self.assertEqual(db.balances(self.conn)["ten"], 0)

        blocked_id = db.add_income(
            self.conn, "2026-09-22", 10000, "job_20", "", 1000, 5000, 4000
        )
        db.add_expense(
            self.conn, "2026-09-23", "everyday", 4500, "food", "", False
        )
        with self.assertRaisesRegex(ValueError, "negative"):
            db.delete_income(self.conn, blocked_id)

    def test_income_and_expense_can_be_edited(self):
        income_id = db.add_income(
            self.conn, "2026-09-20", 10000, "job_20", "pay", 1000, 5000, 4000
        )
        expense_id = db.add_expense(
            self.conn, "2026-09-21", "everyday", 500, "food", "lunch", False
        )
        db.update_income(
            self.conn, income_id, "2026-09-20", 12000, "extra", "bonus", 1200, 4800, 6000
        )
        row = db.get_income(self.conn, income_id)
        self.assertEqual(row["gross_cents"], 12000)
        self.assertEqual(row["source"], "extra")
        self.assertEqual(row["ten_cents"], 1200)
        self.assertEqual(row["savings_cents"], 6000)
        db.update_expense(
            self.conn, expense_id, "2026-09-22", "everyday", 800, "cafes", "dinner", False
        )
        spent = db.get_expense(self.conn, expense_id)
        self.assertEqual(spent["amount_cents"], 800)
        self.assertEqual(spent["category"], "cafes")
        self.assertEqual(spent["occurred_on"], "2026-09-22")
        self.assertEqual(db.balances(self.conn)["everyday"], 4000)
        with self.assertRaisesRegex(ValueError, "negative"):
            db.update_income(
                self.conn, income_id, "2026-09-20", 100, "extra", "", 10, 90, 0
            )


if __name__ == "__main__":
    unittest.main()

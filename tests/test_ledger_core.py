import pandas as pd

from ledger_core import categorize_with_rules, monthly_summary, parse_expense_lines


def test_rules_categorize_travel():
    assert categorize_with_rules("Bus fare to client site") == "Travel"


def test_rules_default_other():
    assert categorize_with_rules("Unusual one-off cost") == "Other"


def test_parse_three_and_two_fields():
    rows = parse_expense_lines("2026-10-12 | Bus fare | 85\nNotebook | 185")
    assert len(rows) == 2
    assert rows[0]["amount"] == 85
    assert rows[0]["date"] == "2026-10-12"
    assert rows[1]["description"] == "Notebook"


def test_monthly_summary():
    df = pd.DataFrame([
        {"date": "2026-10-01", "description": "Bus", "amount": 50, "category": "Travel"},
        {"date": "2026-10-02", "description": "Pen", "amount": 20, "category": "Office supplies"},
        {"date": "2026-09-02", "description": "Meal", "amount": 30, "category": "Meals"},
    ])
    report = monthly_summary(df, "2026-10")
    assert report["total"] == 70
    assert report["count"] == 2

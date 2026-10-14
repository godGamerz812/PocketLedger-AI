from datetime import date

import pandas as pd
import requests

CATEGORIES = [
    "Travel", "Meals", "Office supplies", "Software", "Internet & phone",
    "Equipment", "Marketing", "Professional services", "Utilities", "Other",
]

RULES = {
    "Travel": ["bus", "train", "taxi", "cab", "fuel", "petrol", "metro", "flight", "parking", "travel"],
    "Meals": ["lunch", "dinner", "breakfast", "meal", "coffee", "tea", "restaurant", "snack"],
    "Office supplies": ["paper", "pen", "notebook", "stationery", "printer", "ink", "folder"],
    "Software": ["software", "subscription", "domain", "hosting", "saas", "app license", "design tool"],
    "Internet & phone": ["internet", "broadband", "wifi", "mobile recharge", "phone bill", "data plan"],
    "Equipment": ["laptop", "monitor", "keyboard", "mouse", "webcam", "headphone", "equipment"],
    "Marketing": ["advert", "marketing", "promotion", "business card", "campaign"],
    "Professional services": ["consultant", "accountant", "legal", "freelancer", "professional fee"],
    "Utilities": ["electricity", "water bill", "gas bill", "utility"],
}


def categorize_with_rules(description: str) -> str:
    text = description.lower()
    for category, keywords in RULES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"


def ollama_categorize(description: str, base_url: str, model: str, timeout: int = 12) -> str:
    """Ask a configured Ollama server for one category; raise on failure."""
    prompt = (
        "Classify this expense into exactly one category from this list: "
        + ", ".join(CATEGORIES)
        + ". Return only the category name. Expense: "
        + description[:500]
    )
    response = requests.post(
        base_url.rstrip("/") + "/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    response.raise_for_status()
    answer = response.json().get("response", "").strip().strip('"').strip("'")
    for category in CATEGORIES:
        if answer.casefold() == category.casefold():
            return category
    raise ValueError("Model response did not match an allowed category.")


def parse_expense_lines(text: str):
    """Parse date | description | amount or description | amount."""
    rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        try:
            if len(parts) == 3:
                expense_date, description, amount = parts
                date.fromisoformat(expense_date)
            elif len(parts) == 2:
                description, amount = parts
                expense_date = date.today().isoformat()
            else:
                continue
            value = float(amount.replace(",", "").replace("₹", "").strip())
            if description and value > 0:
                rows.append({"date": expense_date, "description": description, "amount": value})
        except (ValueError, TypeError):
            continue
    return rows


def monthly_summary(df: pd.DataFrame, month: str):
    chosen = df[df["date"].astype(str).str.startswith(month)].copy()
    chosen["amount"] = pd.to_numeric(chosen["amount"], errors="coerce").fillna(0)
    by_category = (
        chosen.groupby("category", as_index=False)["amount"].sum()
        .sort_values("amount", ascending=False)
        .rename(columns={"category": "Category", "amount": "Total (₹)"})
    )
    return {
        "total": float(chosen["amount"].sum()),
        "count": int(len(chosen)),
        "by_category": by_category,
    }

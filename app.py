import os
from datetime import date

import pandas as pd
import streamlit as st

from ledger_core import (
    CATEGORIES,
    categorize_with_rules,
    monthly_summary,
    ollama_categorize,
    parse_expense_lines,
)

st.set_page_config(page_title="PocketLedger AI", page_icon="🧾", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1120px; padding-top: 1.8rem;}
.hero {padding: 1.5rem 1.6rem; border-radius: 18px; background: linear-gradient(120deg,#102a43,#176b63); color:white; margin-bottom:1rem;}
.hero h1 {color:white; margin-bottom:.2rem;}
.hero p {color:#d8e9e7; margin-bottom:0;}
</style>
""", unsafe_allow_html=True)

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(
        columns=["date", "description", "amount", "category", "notes", "categorization_method"]
    )

st.markdown("""
<div class="hero">
  <h1>🧾 PocketLedger AI</h1>
  <p>A privacy-first expense desk for freelancers and independent businesses.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("AI settings")
    model = st.text_input("Ollama model", value=os.getenv("OLLAMA_MODEL", "gemma3:1b"))
    ollama_url = st.text_input("Ollama URL", value=os.getenv("OLLAMA_URL", "http://localhost:11434"))
    st.caption("Ollama mode uses the open-weight model you configure. If unavailable, the app can use a transparent rules fallback.")
    ai_mode = st.radio("Categorization mode", ["Try local open model", "Rules-only fallback"])
    st.divider()
    st.markdown("**Privacy note**")
    st.caption("Entries stay in this Streamlit session. In Ollama mode, descriptions are sent to the Ollama endpoint you configure.")

tab_add, tab_ledger, tab_report, tab_about = st.tabs(
    ["➕ Add expenses", "📚 Ledger", "📊 Monthly report", "ℹ️ About"]
)

with tab_add:
    st.subheader("Add a single expense")
    with st.form("single_expense", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        desc = c1.text_input("What was the expense?", placeholder="e.g. Printer paper for client work")
        amount = c2.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
        c3, c4 = st.columns(2)
        expense_date = c3.date_input("Date", value=date.today())
        manual_category = c4.selectbox("Category", ["Auto-detect"] + CATEGORIES)
        notes = st.text_input("Optional note", placeholder="Client, invoice number, or context")
        submitted = st.form_submit_button("Add expense", type="primary")

    if submitted:
        if not desc.strip() or amount <= 0:
            st.error("Enter an expense description and an amount greater than zero.")
        else:
            category, method = manual_category, "manual"
            if category == "Auto-detect":
                category, method = categorize_with_rules(desc), "rules"
                if ai_mode == "Try local open model":
                    try:
                        category = ollama_categorize(desc, ollama_url, model)
                        method = f"ollama:{model}"
                    except Exception as exc:
                        st.warning(f"Local model unavailable; used rules fallback. Details: {exc}")
            row = {
                "date": expense_date.isoformat(),
                "description": desc.strip(),
                "amount": float(amount),
                "category": category,
                "notes": notes.strip(),
                "categorization_method": method,
            }
            st.session_state.expenses = pd.concat(
                [st.session_state.expenses, pd.DataFrame([row])], ignore_index=True
            )
            st.success(f"Added ₹{amount:,.2f} under {category} using {method}.")

    st.divider()
    st.subheader("Quick import from text")
    st.write("Paste one expense per line: date | description | amount. Date is optional.")
    bulk_text = st.text_area(
        "Expense lines", height=150,
        placeholder="2026-10-12 | Bus fare to client site | 85\n2026-10-12 | Design software subscription | 499"
    )
    if st.button("Parse and add lines"):
        parsed = parse_expense_lines(bulk_text)
        if not parsed:
            st.info("No valid lines found. Use date | description | amount or description | amount.")
        else:
            new_rows = []
            for item in parsed:
                category, method = categorize_with_rules(item["description"]), "rules"
                if ai_mode == "Try local open model":
                    try:
                        category = ollama_categorize(item["description"], ollama_url, model)
                        method = f"ollama:{model}"
                    except Exception:
                        method = "rules (Ollama unavailable)"
                new_rows.append({**item, "category": category, "notes": "", "categorization_method": method})
            st.session_state.expenses = pd.concat(
                [st.session_state.expenses, pd.DataFrame(new_rows)], ignore_index=True
            )
            st.success(f"Added {len(new_rows)} expense(s). Review them in the Ledger tab.")

with tab_ledger:
    st.subheader("Expense ledger")
    df = st.session_state.expenses.copy()
    if df.empty:
        st.info("Your ledger is empty. Add an expense or load labelled demo data.")
        if st.button("Load clearly labelled demo data"):
            st.session_state.expenses = pd.DataFrame([
                {"date": "2026-10-12", "description": "Notebook and pens for client workshop", "amount": 185.0, "category": "Office supplies", "notes": "DEMO DATA", "categorization_method": "rules"},
                {"date": "2026-10-13", "description": "Monthly design software subscription", "amount": 499.0, "category": "Software", "notes": "DEMO DATA", "categorization_method": "rules"},
                {"date": "2026-10-14", "description": "Bus fare to customer meeting", "amount": 72.0, "category": "Travel", "notes": "DEMO DATA", "categorization_method": "rules"},
            ])
            st.rerun()
    else:
        total = float(pd.to_numeric(df["amount"], errors="coerce").fillna(0).sum())
        m1, m2, m3 = st.columns(3)
        m1.metric("Recorded expenses", len(df))
        m2.metric("Total spend", f"₹{total:,.2f}")
        m3.metric("Categories", df["category"].nunique())
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download ledger as CSV", data=df.to_csv(index=False).encode("utf-8"),
            file_name="pocketledger-expenses.csv", mime="text/csv"
        )
        if st.button("Clear current session ledger"):
            st.session_state.expenses = pd.DataFrame(
                columns=["date", "description", "amount", "category", "notes", "categorization_method"]
            )
            st.rerun()

with tab_report:
    st.subheader("Monthly spending summary")
    df = st.session_state.expenses.copy()
    if df.empty:
        st.info("Add expenses first to generate a report.")
    else:
        months = sorted(df["date"].astype(str).str[:7].dropna().unique(), reverse=True)
        selected_month = st.selectbox("Choose month", months)
        report = monthly_summary(df, selected_month)
        a, b = st.columns(2)
        a.metric("Month total", f"₹{report['total']:,.2f}")
        b.metric("Number of entries", report["count"])
        st.dataframe(report["by_category"], use_container_width=True, hide_index=True)
        st.download_button(
            "Download monthly report",
            data=report["by_category"].to_csv(index=False).encode("utf-8"),
            file_name=f"pocketledger-{selected_month}-summary.csv", mime="text/csv"
        )
        st.caption("This is a bookkeeping aid, not tax or accounting advice.")

with tab_about:
    st.subheader("What makes PocketLedger different?")
    st.markdown("""
- **Local-first AI option:** connect to an open-weight model through Ollama on a machine you control.
- **No paid AI API required:** rules-only mode works without an AI service.
- **Clear provenance:** each row records whether categorization was manual, model-based, or rules-based.
- **Portable data:** export your ledger and monthly category totals as CSV.
- **Honest limitations:** receipt-image OCR, multi-device sync, and tax advice are not provided.
""")
    st.markdown("**Who might pay for it?** Freelancers, tutors, creators, and small shops that want a lightweight expense workflow.")
    st.markdown("**Why open innovation matters:** users can inspect the code, choose or replace an open-weight model, run inference on infrastructure they control, and avoid lock-in to one provider.")

st.caption("PocketLedger AI • Hacktoberfest 2026 Week 2 — Side Hustle • Prototype")

# PocketLedger AI 🧾

A privacy-first expense organizer for freelancers and small businesses, built for the **Hacktoberfest 2026 Week 2: Side Hustle** challenge.

## Features

- Add individual expenses or import multiple lines.
- Categorize expenses with an open-weight model served by Ollama, or use a rules-based fallback.
- Review a ledger and export it to CSV.
- Generate monthly spending totals by category.
- Track whether each category was selected manually, by rules, or by the model.

## Run locally

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
~~~

On Windows, activate the environment with .venv\Scripts\activate. Open the local URL printed by Streamlit.

## Enable open-weight AI with Ollama

1. Install Ollama from https://ollama.com/.
2. Pull a model supported by your device, for example:

   ~~~bash
   ollama pull gemma3:1b
   ~~~

3. Ensure the Ollama server is running.
4. In the app sidebar, enter the model name and server URL, then select **Try local open model**.

The default endpoint is http://localhost:11434. If the model cannot be reached or its answer is not one of the allowed categories, the app falls back to rules-based categorization. No hosted AI API is used by this app.

## Import format

Use one expense per line:

~~~text
2026-10-12 | Bus fare to client site | 85
2026-10-12 | Design software subscription | 499
Notebook and pens | 185
~~~

The date is optional. When omitted, today's date is used.

## Privacy and limitations

- Entries live in the current Streamlit session; persistent storage and multi-device sync are not implemented.
- In Ollama mode, descriptions are sent to the Ollama endpoint configured by the user. Use an endpoint you control for local-first processing.
- This is a bookkeeping aid prototype, not tax advice.
- Receipt-image OCR, multi-user accounts, automatic bank imports, and invoice payments are not implemented.

## Why open innovation matters

An open-weight model can run on a device or server controlled by the user and can be swapped for another compatible model. That gives small operators more control over privacy, cost, and provider choice. The transparent fallback also keeps basic categorization available when no model is installed.

## Demo checklist

1. Add a manual expense.
2. Import two or three expenses.
3. Open the ledger and download its CSV.
4. Open the monthly report.
5. If Ollama is configured, show one real model-categorized expense and its method label.

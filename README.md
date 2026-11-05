# Logistics Cost Auditor Tool (AI-Powered Overbilling Detection)

An intelligent, type-safe data pipeline designed to automate supply chain cost audits. The tool ingests unstructured logistics invoices from major carriers (e.g., Maersk, MSC), extracts billing metrics using the Google GenAI SDK [†], maps them into validated Pydantic schemas, and flags discrepancies against baseline contract rate matrices to prevent overbilling.

## 🛠️ Tech Stack & Features
* **Zero-Regex Ingestion:** Leverages Gemini structural parsing for strict validation.
* **Overbilling Leakage Detection:** Audits base ocean freight rates against dynamic contractual data layers.
* **Hidden Charge Detection:** Automatically flags unapproved demurrage, detention, and localized port storage line items.

## 🚀 Getting Started
```bash
pip install google-genai pydantic pandas openpyxl
export GEMINI_API_KEY="your_api_key_here"
python main.py
```

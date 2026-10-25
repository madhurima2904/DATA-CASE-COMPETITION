# Request Form module (Tianjiao)

Part of the team prototype for the SMU DSA Data Case Competition 2026 (Lives Group MDM).
Uses the team's synthetic data package in `../data/raw`. **Synthetic / demonstration only - no real Microsoft 365 or SAP B1 integration.**

## What it shows

| Page | Brief question it answers |
|---|---|
| **New request** | One form for Customer / Item / Vendor / Cost Center. Required fields enforced, some only when relevant (e.g. a licence number for reagents and Product C). Live duplicate check against the SAP B1 mock master data (fuzzy name match + registration number). Sensitive fields (bank, credit) are masked and stored separately for Finance. Shows the approval route before submitting. |
| **Request tracker** | "My requests" / "Waiting on me" / "All". Each request shows its approval steps, status and an audit trail (who did what, when). Includes the 36 team history requests (`mdm_requests.csv` + `approval_logs.csv`). Demo buttons approve the current step and hand off to SAP B1 (mock code). |
| **Inbox triage** | NLP classifier (TF-IDF + logistic regression) labels customer messages as Purchase order / Enquiry / Follow-up / MDM setup, so only real orders count as demand. Orders from customers not in SAP B1 are routed to MDM setup first. |
| **Admin: form rules** | The MDM team edits field rules and the approval routing as tables; the form changes immediately - no IT. **Duplicate review** finds likely duplicates across SPD / QTS / QTG: on the seeded test data it finds **11 of 11** alias customers with **0 false alarms**, and all 3 duplicate item codes. |

## Run it

From the repository root:

```bash
pip install -r request_form/requirements.txt
cd request_form
python generate_data.py      # creates the message data for Inbox triage (run once)
streamlit run app.py
```

## Data used

Reads (never modifies) `../data/raw/`: `customers.csv`, `items.csv`, `vendors.csv`, `cost_centers.csv`, `users_and_roles.csv`, `mdm_requests.csv`, `approval_logs.csv`.

Writes only inside `request_form/data/`:
- `new_requests.csv`, `new_approval_logs.csv` - requests and approval events created during a demo (same columns as the team tables; "Reset demo data" clears them)
- `finance_vault.csv` - sensitive fields, separate from the request record
- `messages_train.csv`, `inbox_demo.csv` - synthetic labelled messages (from `generate_data.py`)

Linked to the team data:
- Drop-down options (country, entity, customer type, product group, category, unit, regulatory status) are read live from `data/raw` using `@file.column` in `field_rules.csv`.
- On the mock SAP handoff, the approved record is added with the **same columns as the team master file** to `request_form/data/new_<file>.csv` (e.g. `new_items.csv` gets `I014`), plus a row in `new_sapb1_mock_master_snapshot.csv`. The duplicate check then includes it, so the same request cannot be created twice.

Config the MDM team edits: `config/field_rules.csv`, `config/approval_matrix.csv` (starts from the team's `approval_rules.csv`, plus `condition` and `sla_hours` columns).

## Demo script (about 60 seconds)

1. **New request -> Customer**, type "KL Medical Center 2": duplicates C017 / C077 appear and submit is blocked.
2. **Item**, pick category "Diagnostic reagent": shelf life and licence number become required.
3. Fill a **Cost Center** request and submit -> new request R037.
4. **Request tracker**: switch "Signed in as" to Wei Jie Lim (Finance) -> "Waiting on me" -> approve; then Priya (MDM Analyst) -> approve -> post to SAP B1. Open the audit trail.
5. **Inbox triage**: an order from an unknown hospital is routed to MDM setup.
6. **Admin**: tick "required" on a field, save, show the form change; open Duplicate review.

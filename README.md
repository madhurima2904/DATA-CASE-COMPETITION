# LivesFlow: Modernizing Master Data Management at Lives Group

LivesFlow is a working prototype for SMU DSA Society 2026 Data Case Competition (brief: *Modernizing Master Data Management at Lives Group*). It replaces the email-driven process for creating and changing master records (Customers, Vendors, Items, Cost Centers) in SAP Business One, and adds regional purchasing analytics and demand forecasting built on the same data.

**Demo video:** [INSERT YouTube link]

---

## What it does

| Area | What the prototype shows |
|---|---|
| **Intake and duplicate screening** | Request form checks required fields and runs an automatic duplicate check (similarity of 80% or higher) before an approver sees the request. |
| **Approvals** | Role-based "Waiting on me" queue for each approver, with the approval chain, SLA, and masked sensitive fields. |
| **Overdue and escalation** | Reminders at the SLA; escalation at twice the SLA. |
| **Audit trail** | Append-only log of every action. Rows are added, never edited. |
| **Rules without IT** | The MDM team edits approval rules in an Admin tab. Every previous version is kept. |
| **SAP handoff** | Fully approved requests appear in a queue with the code that would be created in SAP B1. |
| **Regional analytics** | Confirmed orders and enquiries across SPD, QTS, and QTG and five countries, for Products A, B, and C, with growth measures over a 6–12 month window. |
| **Demand forecast** | Walk-forward backtest of four models (6-month moving average, linear regression, XGBoost, LightGBM), scored by WAPE. The best performer produces a six-month forecast. |
| **Exception report** | Flags months outside the forecast band and enquiry spikes. |

Purchase orders and enquiries feed the regional and forecasting views. MDM setup requests move through the approval workflow. The two streams are kept separate.

---

## Repository layout

```
.
├── app.py                      # Main Streamlit app: navigation and global styling
├── pages/
│   ├── demand_forecast.py      # Backtest and six-month forecast
│   ├── regional_analytics.py   # Regional summary, sales opportunities, cross-entity view
│   ├── exception_dashboard.py  # Forecast exceptions and enquiry spikes
│   └── master_data_records.py  # Intake, duplicate check, approvals, SAP handoff queue
├── approvals.py                # Routing, progress, SLA, reminders, audit logging, masking
├── approvals_app.py            # Stand-alone approvals app (role selector, Admin tab)
├── test_approvals.py           # Scripted walk-through of one request through approvals
├── add_demo_sensitive.py       # Adds demo bank and credit columns to the request data
├── reset_demo.sh               # Restores the demo copies from the raw data
├── requirements.txt
└── data/
    ├── raw/                    # Source CSVs (see Data below)
    ├── demo/                   # Working copies used by the approvals app
    └── processed/              # Mock SAP B1 handoff database (created by the app)
```

---

## Setup

Requires Python 3.10 or later.

```bash
git clone <repository-url>
cd <repository-folder>
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install xgboost lightgbm       # required by the forecast page; see note below
```

> **Note:** `demand_forecast.py` imports `xgboost` and `lightgbm`, which are not yet listed in `requirements.txt`. Add them there to make installation a single step. `rapidfuzz` is listed but not currently used; duplicate matching uses Python's standard `difflib.SequenceMatcher`.

---

## Data

The app reads CSV files from `data/raw/`. The prototype runs on **synthetic data** covering five countries, Products A, B, and C, and the SPD, QTS, and QTG entities, because no live SAP extract was used. Results demonstrate the method and are not findings about Lives Group's real business.

Files expected in `data/raw/`:

- `mdm_requests.csv`: master data requests and their status
- `approval_rules.csv`: which approver roles are needed for each request type, entity, and country
- `approval_logs.csv`: audit trail of approval events
- `users_and_roles.csv`: people, roles, entities, and active status
- Sales and purchase-order data used by the regional, forecast, and exception pages

Before using the approvals app, create the demo copies:

```bash
bash reset_demo.sh
```

This copies the approval files from `data/raw/` into `data/demo/`. Run it from the repository root. To add demo bank and credit fields to the request data, run `python add_demo_sensitive.py`.

---

## Running the app

Main dashboard (regional analytics, forecast, exceptions, master data):

```bash
streamlit run app.py
```

Approvals app (approver views, reminders, audit trail, rules admin):

```bash
streamlit run approvals_app.py
```

In the approvals app, use the **Signed in as** selector in the sidebar to switch between approvers and see each person's view. Only the MDM Analyst can edit approval rules.

---

## Testing the approval flow

`test_approvals.py` walks request `R003` through procurement, finance, and MDM approval, printing the status after each step and the audit trail. It writes to `data/demo/`, so run `bash reset_demo.sh` afterwards to restore the demo state.

```bash
python test_approvals.py
```

---

## Limitations

This is a prototype built for a case competition. The following parts are simulated:

- **SAP Business One:** the handoff writes to a local SQLite database (`data/processed/mock_sap_handoffs.sqlite3`). The app does not connect to a real SAP system. A production version would call the SAP B1 Service Layer.
- **Teams and Outlook:** approval cards are not sent. The app logs that a card would be sent. A production version would deliver them through Power Automate.
- **Sign-in:** the "Signed in as" selector is a role switch for demonstration. It is not authentication. Field masking shows how role-based access would work, but it is not a security model.
- **Data:** synthetic, as described above.

---

## Roadmap

- Connect the SAP handoff to SAP B1 Service Layer in a test instance
- Send approval cards through Teams and Outlook via Power Automate
- Add Microsoft 365 sign-in so roles come from the directory
- Extend forecasting beyond Products A, B, and C

---

## Team

Team LivesFlow, SMU DSA Society 2026 Data Case Competition.

## Licence

[INSERT licence, or remove this section]

# LivesFlow: Modernizing Master Data Management at Lives Group

LivesFlow is a working prototype for SMU DSA Society 2026 Data Case Competition (brief: *Modernizing Master Data Management at Lives Group*). It replaces the email-driven process for creating and changing master records (Customers, Vendors, Items, Cost Centers) in SAP Business One, and adds regional purchasing analytics and demand forecasting built on the same data.

**Demo video:** [INSERT YouTube link]

---

## What it does

| Area | What the prototype shows |
|---|---|
| **Intake and duplicate screening** | One request form for all four record types (Customer, Vendor, Item, Cost Center) that shows only the fields each type needs, with conditional rules (e.g. Product C items need a licence number). Before an approver sees the request, it checks names and registration numbers against existing records: 80% similarity or higher shows a warning, 90% or higher is blocked unless the requester gives a reason. A request tracker shows each request's approval progress. |
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
├── reset_demo.sh               # Resets the demo (form output, approvals copies, handoff database)
├── reset_demo.bat              # Same as reset_demo.sh, for Windows
├── mdm_request_form/
│   └── request_form/
│       ├── app.py              # Request form app (new request, duplicate check, request tracker, admin)
│       ├── mdm.py              # Field rules, duplicate matching, approval routing
│       ├── config/             # field_rules.csv and approval_matrix.csv (shared with the approvals app)
│       └── data/               # Seed data; new_*.csv files are written here by the form and approvals
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
```

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

On Windows, run `reset_demo.bat` instead. This copies the approval files from `data/raw/` into `data/demo/`, clears requests submitted through the form, restores the shared approval rules, and clears the handoff database. Run it from the repository root. To add demo bank and credit fields to the request data, run `python add_demo_sensitive.py`.

---

## Running the app

The prototype is three Streamlit apps that share the same CSV files. Start each one from the repository root in its own terminal:

```bash
streamlit run mdm_request_form/request_form/app.py                    # Request form, port 8501
streamlit run approvals_app.py --server.port 8502                     # Approvals
streamlit run app.py --server.port 8503                               # LivesFlow dashboard
```

The sections below describe each app.

Request form (new request with duplicate check, request tracker, admin for field rules and routing):

```bash
streamlit run mdm_request_form/request_form/app.py
```

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

## End-to-end demo (about 5 minutes)

Run `reset_demo.bat` (Windows) or `bash reset_demo.sh`, start the three apps as above, then follow one request:

1. **Request form:** New request, Item. Type `C - Diag Device 3`; it is blocked as a duplicate. Change it to `C - Diagnostic Analyzer 4`, Product C, fill in the rest including the licence number, and submit. The request is `R037`.
2. **Approvals app:** sign in as Siti Rahman, then Daniel Wong, then Priya Shah, and approve `R037` each time.
3. **LivesFlow, Master Data Records:** `R037` is first in the queue. Fill in reviewer and notes, tick the box, and save. In Master Data Directory, Item, the new item `I014` is listed.
4. **Request form, Request tracker:** `R037` shows Completed (3/3) with `I014`.

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

Team Hamster, SMU DSA Society 2026 Data Case Competition.


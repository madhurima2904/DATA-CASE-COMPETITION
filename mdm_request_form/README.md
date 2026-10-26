# MDM Request Form (Tianjiao)

Request-form part of our Lives Group MDM prototype. Uses the shared synthetic data in `data/raw` (found automatically in a parent folder). **Demo only - not connected to Microsoft 365 or SAP B1.**

| Folder | What it is | How to open |
|---|---|---|
| `power_apps/MDM_Request_Form_Mockup.html` | Teams / Power Apps-style mock-up of the request form, approvals and SAP handoff | Double-click, no install |
| `request_form/` | Streamlit prototype with the same logic, plus inbox triage (NLP) and an admin page for field rules | Windows: double-click `run_request_form.bat`; or `pip install -r request_form/requirements.txt` then `streamlit run app.py` inside `request_form/` |

Key results on the seeded test data: the duplicate check finds **11 of 11** alias customers with **0 false alarms**, and all 3 duplicate item codes.

Details: see `request_form/README.md`. To rebuild the HTML mock-up after data changes: `python power_apps/build_mockup.py`.

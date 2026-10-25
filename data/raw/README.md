# README

# LivesFlow Team Data Package — SYNTHETIC / DEMONSTRATION ONLY

This package builds on the original LivesFlow synthetic data. It is NOT from Lives Group, Microsoft 365, or SAP B1. Countries SG/MY/TH/ID/VN are assumptions. Synthetic demand covers 2025-10 to 2026-09. All money denominated in illustrative SGD.

## TEAM OWNERSHIP

Tianjiao (requests): customers.csv, items.csv, vendors.csv, cost_centers.csv, mdm_requests.csv, customer_canonical_mapping.csv, sap_b1_mock_master_snapshot.csv, and the seeded-duplicate files (injection_log.csv, item_injection_log.csv, injection_summary.csv, inject_duplicates.py).
Liangyu (approvals): mdm_requests.csv, approval_logs.csv, approval_rules.csv, users_and_roles.csv, sap_b1_mock_master_snapshot.csv.
Madhu (forecasting): purchase_orders.csv, monthly_demand.csv, forecast_baseline_backtest.csv, forecast_oct2026_baseline.csv. The baseline is a 3-month moving average, NOT ML.
Nicolyne (regional analytics): purchase_orders.csv, customers.csv, items.csv, regional_monthly_kpis.csv, order_status_monthly.csv.

## KEY JOINS / DEFINITIONS

purchase_orders.customer_id = customers.customer_id
purchase_orders.item_id = items.item_id
mdm_requests.request_id = approval_logs.request_id
All forecast/region volume KPIs FILTER order_status = ‘Confirmed’. Enquiries and cancellations are excluded from confirmed demand, but can be charted separately. A purchase order and an MDM request are different events.
monthly_demand has 12 months x 5 countries x 3 product groups = 180 rows.
regional_monthly_kpis is computed from Confirmed purchase order rows. Customer alias IDs and duplicate item codes are deliberate tests and not actual company data (see SEEDED DUPLICATES below).
forecast_baseline_backtest predictions use only earlier months, starting after the first six months. This demonstrates method rather than guaranteed performance.
No real Microsoft or SAP integration is included; use mocked handoff. Never claim the SAP mock codes were provided by SAP.

## SEEDED DUPLICATES (synthetic, on purpose)

customers.csv, items.csv, purchase_orders.csv, sap_b1_mock_master_snapshot.csv and customer_canonical_mapping.csv contain duplicate master records that were seeded to demonstrate the effect of duplicates on a regional view. They are not duplicates found in Lives Group data.

- Customers: 86 records = 75 real customers + 11 alias records (C076-C086). Aliases have active_status Review and a canonical_customer_id pointing to the real customer. 5 aliases sit in a different business entity from the real customer; 2 have no registration_no, so name matching alone must catch them.
- Orders: 27 confirmed orders sit under alias customer_ids (2.6% of 1,026 confirmed orders). Total units and value are unchanged; country and product totals are unchanged; business entity totals shift.
- Items: 13 records = 10 original + 3 duplicate codes (I011 of I002, I012 of I004, I013 of I009). 67 confirmed orders (6.5%) use a duplicate item code. Items have no canonical_item_id column: use item_injection_log.csv as the answer key, or detect duplicates by name, category and product_group.
- SAP mock snapshot: 129 rows, including mock records for every alias customer and duplicate item.
- Answer keys: injection_log.csv (customers), item_injection_log.csv (items), injection_summary.csv (headline counts). inject_duplicates.py documents how the seeded files were made (seed 2026). It expects the earlier 77-customer / 10-item files as input, so do not run it on the current files.
- For consolidated customer views, always group by canonical_customer_id, never by customer_id. Count distinct customers on canonical_customer_id.

## START HERE

1. Team members should use the same CSVs, preferably with a shared GitHub repository.
2. Validate joins and confirm consistent KPIs.
3. Do not overwrite original transaction tables with derived summaries.
4. Use DATA_DICTIONARY.csv to see all columns and row counts.
5. Never treat customer_id as the customer: aggregate by canonical_customer_id.
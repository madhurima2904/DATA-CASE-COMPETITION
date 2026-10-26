#!/bin/bash
mkdir -p data/demo
cp data/raw/approval_logs.csv data/raw/mdm_requests.csv data/raw/approval_rules.csv data/demo/
rm -rf data/demo/rules_history
# Request form demo output and the mock SAP handoff history
rm -f mdm_request_form/request_form/data/new_*.csv
rm -f data/processed/mock_sap_handoffs.sqlite3
echo "Demo data reset."

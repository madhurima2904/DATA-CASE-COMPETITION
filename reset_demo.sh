#!/bin/bash
mkdir -p data/demo
cp data/raw/approval_logs.csv data/raw/mdm_requests.csv data/raw/approval_rules.csv data/demo/
rm -rf data/demo/rules_history
echo "Demo data reset."
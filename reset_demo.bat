@echo off
REM Reset all demo data (Windows version of reset_demo.sh)
cd /d "%~dp0"
if not exist data\demo mkdir data\demo
copy /Y data\raw\approval_logs.csv data\demo\ >nul
copy /Y data\raw\mdm_requests.csv data\demo\ >nul
copy /Y data\raw\approval_rules.csv data\demo\ >nul
if exist data\demo\rules_history rmdir /S /Q data\demo\rules_history
del /Q mdm_request_form\request_form\data\new_*.csv 2>nul
del /Q data\processed\mock_sap_handoffs.sqlite3 2>nul
cp mdm_request_form/request_form/config/approval_matrix_baseline.csv mdm_request_form/request_form/config/approval_matrix.csv
echo Demo data reset.

from approvals import *

rid = "R003"   # pending Vendor request, QTG, Thailand

print("=== 1. Which approvers does R003 need? ===")
steps, current = progress(rid)
print(steps[["step_order", "approver_role", "sla_hours", "done"]])
print("Waiting on now:", list(current["approver_role"]))

print("\n=== 2. Procurement approves ===")
add_log(rid, "Test Person", "Procurement", "Approved", "Looks fine")
print(update_request(rid))

print("\n=== 3. Finance approves ===")
add_log(rid, "Wei Jie", "Finance", "Approved", "Bank details checked")
print(update_request(rid))

print("\n=== 4. MDM Analyst approves ===")
add_log(rid, "Priya", "MDM Analyst", "Approved", "Final check done")
print(update_request(rid))

print("\n=== 5. Audit trail for R003 ===")
logs = load(LOGS)
print(logs[logs["request_id"] == rid][["event_id", "actor", "actor_role", "action"]])
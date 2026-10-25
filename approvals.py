import pandas as pd
from datetime import datetime

# ---------- File locations ----------
RULES = "data/raw/approval_rules.csv"        # the rules (MDM team edits these)
LOGS = "data/demo/approval_logs.csv"         # the audit trail (we only add rows)
REQUESTS = "data/demo/mdm_requests.csv"      # the requests (we update status)


# ---------- Helpers ----------
def load(path):
    """Read a CSV. Everything as text, blanks instead of NaN."""
    return pd.read_csv(path, dtype=str).fillna("")


def now():
    """Current time, in the same format as the existing logs."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def add_log(request_id, actor, actor_role, action, comments=""):
    """Add ONE new row to the audit log. Never edits old rows."""
    logs = load(LOGS)
    last = logs["event_id"].str[1:].astype(int).max() if len(logs) else 0
    row = {
        "event_id": f"E{last + 1:04d}",      # E0117 -> E0118
        "request_id": request_id,
        "event_time": now(),
        "actor": actor,
        "actor_role": actor_role,
        "action": action,
        "comments": comments,
    }
    pd.concat([logs, pd.DataFrame([row])]).to_csv(LOGS, index=False)


# ---------- Routing: which approvers does this request need? ----------
def steps_for(request):
    rules = load(RULES)
    r = rules[(rules["request_type"] == request["request_type"])
              & (rules["requires_review"] == "Yes")]
    # keep rules for ALL entities/countries, or for this request's entity/country
    for col in ["entity", "country"]:
        if col in r.columns:
            r = r[r[col].isin(["ALL", request[col]])]
    r = r.assign(step_order=r["step_order"].astype(int))
    return r.sort_values("step_order")


# ---------- Progress: who has approved, who must act now? ----------
def progress(request_id):
    req = load(REQUESTS).set_index("request_id").loc[request_id]
    steps = steps_for(req)

    logs = load(LOGS)
    logs = logs[logs["request_id"] == request_id]
    approved_roles = set(logs.loc[logs["action"] == "Approved", "actor_role"])

    steps = steps.assign(done=steps["approver_role"].isin(approved_roles))
    still_open = steps[~steps["done"]]

    if still_open.empty:
        current = still_open                  # nobody left to approve
    else:
        lowest = still_open["step_order"].min()
        current = still_open[still_open["step_order"] == lowest]

    return steps, current


# ---------- Status: write status + current_step back to mdm_requests ----------
def update_request(request_id):
    steps, current = progress(request_id)
    logs = load(LOGS)
    actions = list(logs.loc[logs["request_id"] == request_id, "action"])

    if "SAP handoff complete" in actions:
        status, step = "Completed", "Finalized"
    elif "Rejected" in actions:
        status, step = "Rejected", "Closed"
    elif actions and actions[-1] == "Changes requested":
        status, step = "Returned for correction", "Correction requested"
    elif current.empty:
        status, step = "Approved - SAP pending", "SAP handoff"
    else:
        status = "Pending approval"
        step = " + ".join(current["approver_role"]) + " review"

    reqs = load(REQUESTS)
    reqs.loc[reqs["request_id"] == request_id, ["status", "current_step"]] = [status, step]
    reqs.to_csv(REQUESTS, index=False)
    return status, step
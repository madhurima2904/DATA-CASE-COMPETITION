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

# ---------- Reminders ----------
NOTICES = ["Reminder sent", "Escalated"]

def hours_waiting(request_id):
    """Hours since the last real action (reminders don't reset the clock)."""
    logs = load(LOGS)
    logs = logs[(logs["request_id"] == request_id) & (~logs["action"].isin(NOTICES))]
    last = pd.to_datetime(logs["event_time"]).max()
    return (datetime.now() - last).total_seconds() / 3600


def overdue_list():
    rows = []
    for rid in load(REQUESTS).query("status == 'Pending approval'")["request_id"]:
        _, current = progress(rid)
        if current.empty:
            continue
        sla = current["sla_hours"].astype(float).min()
        hrs = hours_waiting(rid)
        if hrs > sla:
            rows.append({
                "request_id": rid,
                "waiting_on": " + ".join(current["approver_role"]),
                "hours_waiting": round(hrs),
                "sla_hours": int(sla),
                "escalate": hrs > 2 * sla,
            })
    return pd.DataFrame(rows)


def send_reminders():
    """Log a reminder (or escalation) once per overdue request."""
    sent = 0
    logs = load(LOGS)
    for _, r in overdue_list().iterrows():
        last_action = logs[logs["request_id"] == r["request_id"]].iloc[-1]["action"]
        if last_action in NOTICES:
            continue                        # already reminded, don't spam
        action = "Escalated" if r["escalate"] else "Reminder sent"
        for role in r["waiting_on"].split(" + "):
            add_log(r["request_id"], "system", role, action,
                    f"Waiting {r['hours_waiting']}h, SLA {r['sla_hours']}h")
        sent += 1
    return sent
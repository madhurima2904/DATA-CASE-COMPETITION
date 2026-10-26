import os
import pandas as pd
from datetime import datetime

# ---------- File locations ----------
RULES = "data/demo/approval_rules.csv"       # demo copy, editable in the Admin tab
LOGS = "data/demo/approval_logs.csv"
REQUESTS = "data/demo/mdm_requests.csv"
RULES_HISTORY = "data/demo/rules_history"    # every old version of the rules

NOTICES = ["Reminder sent", "Escalated"]
SYSTEM_EVENTS = NOTICES + ["Routed"]
SENSITIVE_WORDS = ["bank", "account", "iban", "swift", "credit"]


# ---------- Helpers ----------
def load(path):
    return pd.read_csv(path, dtype=str).fillna("")


def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def add_log(request_id, actor, actor_role, action, comments=""):
    """Add ONE new row to the audit log. Never edits old rows."""
    logs = load(LOGS)
    last = logs["event_id"].str[1:].astype(int).max() if len(logs) else 0
    row = {"event_id": f"E{last + 1:04d}", "request_id": request_id,
           "event_time": now(), "actor": actor, "actor_role": actor_role,
           "action": action, "comments": comments}
    pd.concat([logs, pd.DataFrame([row])]).to_csv(LOGS, index=False)


# ---------- Routing ----------
def steps_for(request):
    rules = load(RULES)
    r = rules[(rules["request_type"] == request["request_type"])
              & (rules["requires_review"] == "Yes")]
    for col in ["entity", "country"]:
        if col in r.columns:
            r = r[r[col].isin(["ALL", request[col]])]
    r = r.assign(step_order=r["step_order"].astype(int))
    return r.sort_values("step_order")


def progress(request_id):
    req = load(REQUESTS).set_index("request_id").loc[request_id]
    steps = steps_for(req)
    logs = load(LOGS)
    logs = logs[logs["request_id"] == request_id]
    approved_roles = set(logs.loc[logs["action"] == "Approved", "actor_role"])

    steps = steps.assign(done=steps["approver_role"].isin(approved_roles))
    still_open = steps[~steps["done"]]
    if still_open.empty:
        current = still_open
    else:
        current = still_open[still_open["step_order"] == still_open["step_order"].min()]
    return steps, current


# ---------- NEW: approval cards sent ----------
def notify(request_id, roles):
    """Log that each approver was sent a Teams + Outlook approval card (once)."""
    logs = load(LOGS)
    sent = set(logs.loc[(logs["request_id"] == request_id)
                        & (logs["action"] == "Routed"), "actor_role"])
    for role in roles:
        if role not in sent:
            add_log(request_id, "system", role, "Routed",
                    "Approval card sent in Teams and Outlook")


# ---------- Status ----------
def update_request(request_id):
    steps, current = progress(request_id)
    logs = load(LOGS)
    actions = list(logs.loc[logs["request_id"] == request_id, "action"])
    actions = [a for a in actions if a not in SYSTEM_EVENTS]   # ignore system rows

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
        notify(request_id, list(current["approver_role"]))     # NEW

    reqs = load(REQUESTS)
    reqs.loc[reqs["request_id"] == request_id, ["status", "current_step"]] = [status, step]
    reqs.to_csv(REQUESTS, index=False)
    return status, step


def start_approval(request_id):
    """NEW: the request form calls this right after saving a new request."""
    return update_request(request_id)


# ---------- Reminders ----------
def hours_waiting(request_id):
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
            rows.append({"request_id": rid,
                         "waiting_on": " + ".join(current["approver_role"]),
                         "hours_waiting": round(hrs), "sla_hours": int(sla),
                         "escalate": hrs > 2 * sla})
    return pd.DataFrame(rows)


def send_reminders():
    sent = 0
    logs = load(LOGS)
    for _, r in overdue_list().iterrows():
        rlogs = logs[logs["request_id"] == r["request_id"]]
        if len(rlogs) and rlogs.iloc[-1]["action"] in NOTICES:
            continue                                  # already reminded
        action = "Escalated" if r["escalate"] else "Reminder sent"
        for role in r["waiting_on"].split(" + "):
            add_log(r["request_id"], "system", role, action,
                    f"Waiting {r['hours_waiting']}h, SLA {r['sla_hours']}h")
        sent += 1
    return sent


# ---------- NEW: sensitive fields ----------
def is_sensitive(column):
    return any(word in column.lower() for word in SENSITIVE_WORDS)


def masked(record, role):
    """Hide bank / credit fields from everyone except Finance."""
    return {col: ("Provided · Finance only" if val else "")
            if is_sensitive(col) and role != "Finance" else val
            for col, val in record.items()}


# ---------- NEW: rules editing without IT ----------
def save_rules(new_rules, editor):
    os.makedirs(RULES_HISTORY, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    load(RULES).to_csv(f"{RULES_HISTORY}/approval_rules_{stamp}.csv", index=False)
    new_rules.to_csv(RULES, index=False)
    add_log("RULES", editor, "MDM Analyst", "Rules changed",
            f"Previous version kept as approval_rules_{stamp}.csv")
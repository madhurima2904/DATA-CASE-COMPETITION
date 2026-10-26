"""Core logic for the MDM request form prototype: config, validation,
duplicate detection, intent classification and request storage.

Master data and the request/approval history come from the team data package
in ../data/raw (synthetic). New requests created in the demo are written to
request_form/data/ so the shared raw files are never overwritten."""
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).parent
CONFIG = ROOT / "config"
DATA = ROOT / "data"                       # files owned by this module
RAW = None                                 # shared team data package, set below

def find_raw(start):
    """Locate the team data package (data/raw) in this folder or any parent folder."""
    for p in [start, *start.parents]:
        if (p / "data" / "raw" / "customers.csv").exists():
            return p / "data" / "raw"
    raise FileNotFoundError("Could not find data/raw/customers.csv above " + str(start))


RAW = find_raw(ROOT)

DOMAINS = ["Customer", "Item", "Vendor", "Cost Center"]
NAME_FIELD = {"Customer": "customer_name", "Item": "item_name",
              "Vendor": "vendor_name", "Cost Center": "cost_center_name"}

# How each team master file maps onto a common shape: code, name, entity, country, reg_no
MASTER_SPEC = {
    "Customer": ("customers.csv", {"customer_id": "code", "customer_name": "name",
                                   "business_entity": "entity", "registration_no": "reg_no"}),
    "Item": ("items.csv", {"item_id": "code", "item_name": "name"}),
    "Vendor": ("vendors.csv", {"vendor_id": "code", "vendor_name": "name", "business_entity": "entity"}),
    "Cost Center": ("cost_centers.csv", {"cost_center_id": "code", "cost_center_name": "name"}),
}


# ---------- configuration (editable by the MDM team, no code changes) ----------

def load_field_rules():
    df = pd.read_csv(CONFIG / "field_rules.csv", dtype=str).fillna("")
    for col in ("required", "sensitive"):
        df[col] = df[col].str.upper().eq("TRUE")
    return df


def save_field_rules(df):
    out = df.copy()
    for col in ("required", "sensitive"):
        out[col] = out[col].map(lambda v: "TRUE" if bool(v) else "FALSE")
    out.to_csv(CONFIG / "field_rules.csv", index=False)


def load_approval_matrix():
    return pd.read_csv(CONFIG / "approval_matrix.csv", dtype=str).fillna("")


def save_approval_matrix(df):
    df.to_csv(CONFIG / "approval_matrix.csv", index=False)


def field_options(rule):
    """Options for a select field. '@file.column' reads the distinct values from the
    team data in data/raw, so the form always matches the master data."""
    opts = rule["options"].strip()
    if opts.startswith("@") and "." in opts:
        file, col = opts[1:].split(".", 1)
        path = RAW / f"{file}.csv"
        if path.exists():
            values = pd.read_csv(path, dtype=str)[col].dropna().str.strip()
            return sorted(v for v in values.unique() if v)
        return []
    return [o for o in opts.split("|") if o]


def load_users():
    return pd.read_csv(RAW / "users_and_roles.csv", dtype=str).fillna("")


def condition_met(condition, values):
    """Condition syntax: 'field=v1|v2;other=v3'. Clauses separated by ';' are OR-ed,
    values separated by '|' are alternatives. Empty condition is always true."""
    condition = (condition or "").strip()
    if not condition:
        return True
    for clause in condition.split(";"):
        if "=" not in clause:
            continue
        field, allowed = clause.split("=", 1)
        options = [a.strip() for a in allowed.split("|")]
        if str(values.get(field.strip(), "")).strip() in options:
            return True
    return False


def is_required(rule, values):
    return bool(rule["required"]) or (bool(rule["required_if"]) and condition_met(rule["required_if"], values))


# ---------- incomplete-submission checks ----------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SWIFT_RE = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")


def validate(domain, values, rules):
    """Return a list of human-readable problems. Empty list means complete."""
    problems = []
    for _, rule in rules[rules["domain"] == domain].iterrows():
        v = values.get(rule["field"])
        empty = v is None or str(v).strip() == "" or (rule["type"] == "number" and v == 0)
        if is_required(rule, values) and empty:
            problems.append(f"{rule['label']} is required")
            continue
        if empty:
            continue
        if rule["type"] == "email" and not EMAIL_RE.match(str(v)):
            problems.append(f"{rule['label']} is not a valid email")
        if rule["field"] == "swift_code" and not SWIFT_RE.match(str(v).upper()):
            problems.append("SWIFT code must be 8 or 11 letters/digits")
    return problems


# ---------- duplicate detection ----------

ABBREVIATIONS = {
    "natl": "national", "univ": "university", "hosp": "hospital", "intl": "international",
    "gen": "general", "med": "medical", "ctr": "centre", "center": "centre", "inst": "institute",
    "lab": "laboratory", "labs": "laboratory", "diag": "diagnostic", "clinc": "clinic",
    "sg": "singapore", "kl": "kuala lumpur", "hcmc": "ho chi minh city", "bkk": "bangkok",
}
STOPWORDS = {"pte", "ltd", "limited", "inc", "co", "the", "sdn", "bhd", "pt", "tbk"}


def normalise(name):
    tokens = re.sub(r"[^a-z0-9 ]", " ", str(name).lower()).split()
    tokens = [ABBREVIATIONS.get(t, t) for t in tokens]
    tokens = [str(int(t)) if t.isdigit() else t for t in tokens]   # "01" == "1"
    return " ".join(t for t in tokens if t not in STOPWORDS)


def similarity(a, b):
    """0-100 name similarity on normalised names; robust to word order, spacing and
    abbreviations. Different branch numbers ("... 02" vs "... 09") are penalised."""
    a, b = normalise(a), normalise(b)
    if not a or not b:
        return 0
    mixed = (fuzz.token_set_ratio(a, b) + fuzz.token_sort_ratio(a, b)) / 2
    score = max(mixed, fuzz.ratio(a.replace(" ", ""), b.replace(" ", "")))
    nums_a = {t for t in a.split() if t.isdigit()}
    nums_b = {t for t in b.split() if t.isdigit()}
    if nums_a and nums_b and nums_a != nums_b:
        score *= 0.7
    return score


def load_master_raw(domain):
    """Team master file plus records created through this form (after SAP handoff)."""
    file, _ = MASTER_SPEC[domain]
    team = pd.read_csv(RAW / file, dtype=str).fillna("")
    new = DATA / f"new_{file}"
    if new.exists():
        team = pd.concat([team, pd.read_csv(new, dtype=str).fillna("")], ignore_index=True)
    return team


def load_master(domain):
    _, rename = MASTER_SPEC[domain]
    df = load_master_raw(domain).rename(columns=rename)
    for col in ("entity", "country", "reg_no"):
        if col not in df.columns:
            df[col] = ""
    return df


def find_duplicates(domain, name, reg_no="", country="", limit=5):
    """Fuzzy-match a proposed name (and exact registration number) against existing
    master records. Returns a DataFrame with a 0-100 match score, best first."""
    master = load_master(domain)
    if not str(name).strip() and not str(reg_no).strip():
        return master.head(0).assign(score=[], reason=[])
    scores, reasons = [], []
    for _, row in master.iterrows():
        s, reason = similarity(name, row["name"]), "Similar name"
        if country and row["country"] and row["country"] != country:
            s *= 0.8
        if reg_no and row["reg_no"] and row["reg_no"].strip().upper() == str(reg_no).strip().upper():
            s, reason = 100, "Same registration no."
        scores.append(round(s))
        reasons.append(reason)
    out = master.assign(score=scores, reason=reasons)
    return out[out["score"] >= 75].sort_values("score", ascending=False).head(limit)


def duplicate_level(score):
    if score >= 90:
        return "block"
    if score >= 80:
        return "warn"
    return "ok"


def find_cross_entity_duplicates(domain="Customer", threshold=90):
    """Pairs of existing records that look like the same real-world entity
    (same country, similar name or same registration number)."""
    rows = load_master(domain).to_dict("records")
    pairs = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if a["country"] and b["country"] and a["country"] != b["country"]:
                continue
            s, reason = similarity(a["name"], b["name"]), "Similar name"
            if domain == "Item" and (a.get("category") != b.get("category")):
                continue
            if a["reg_no"] and a["reg_no"] == b["reg_no"]:
                s, reason = 100, "Same registration no."
            if s >= threshold:
                pairs.append({"record_a": f"{a['code']} {a['name']} ({a['entity'] or '-'})",
                              "record_b": f"{b['code']} {b['name']} ({b['entity'] or '-'})",
                              "score": round(s), "reason": reason,
                              "cross_entity": "Yes" if a["entity"] and b["entity"] and a["entity"] != b["entity"] else "No",
                              "_a": a["code"], "_b": b["code"]})
    return pd.DataFrame(pairs, columns=["record_a", "record_b", "score", "reason", "cross_entity", "_a", "_b"])


def evaluate_customer_dedup(threshold=90):
    """Compare detected customer pairs with the seeded answer key (canonical_customer_id)."""
    cust = pd.read_csv(RAW / "customers.csv", dtype=str).fillna("")
    truth = {frozenset((r.customer_id, r.canonical_customer_id))
             for r in cust.itertuples() if r.customer_id != r.canonical_customer_id}
    pairs = find_cross_entity_duplicates("Customer", threshold)
    found = {frozenset((a, b)) for a, b in zip(pairs["_a"], pairs["_b"])}
    tp = len(found & truth)
    return {"seeded": len(truth), "detected": len(found), "correct": tp,
            "false_alarms": len(found - truth), "missed": len(truth - found),
            "precision": tp / len(found) if found else 0.0, "recall": tp / len(truth) if truth else 0.0}


# ---------- intent classification: orders vs enquiries vs follow-ups vs MDM setup ----------

ROUTING = {
    "Purchase order": "Order desk - counts toward confirmed demand",
    "Enquiry": "Regional sales team - excluded from demand",
    "Follow-up": "Account owner - linked to the existing order",
    "MDM setup": "Start a Customer request in the MDM form",
}


def train_classifier():
    df = pd.read_csv(DATA / "messages_train.csv")
    x_train, x_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.25, random_state=0, stratify=df["label"])
    model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                          LogisticRegression(C=10, max_iter=2000))
    model.fit(x_train, y_train)
    return model, accuracy_score(y_test, model.predict(x_test))


def classify(model, text, sender_org=""):
    proba = model.predict_proba([text])[0]
    best = proba.argmax()
    label, conf = model.classes_[best], float(proba[best])
    note = ""
    if label == "Purchase order" and sender_org:
        matches = find_duplicates("Customer", sender_org)
        if matches.empty or matches.iloc[0]["score"] < 90:
            label, note = "MDM setup", "Order from a customer not found in SAP B1 - create the account first"
    return {"label": label, "confidence": conf, "needs_review": conf < 0.6,
            "route": ROUTING[label], "note": note}


# ---------- requests and approval history ----------
# Team tables: mdm_requests.csv + approval_logs.csv (read only).
# Demo additions: data/new_requests.csv + data/new_approval_logs.csv.

REQ_COLS = ["request_id", "submitted_at", "request_type", "record_name", "requestor", "country",
            "entity", "status", "current_step", "candidate_existing_id", "notes"]
LOG_COLS = ["event_id", "request_id", "event_time", "actor", "actor_role", "action", "comments"]


def _read(path, cols):
    if path.exists():
        return pd.read_csv(path, dtype=str).fillna("")
    return pd.DataFrame(columns=cols)


def load_requests():
    team = _read(RAW / "mdm_requests.csv", REQ_COLS).assign(source="Team history")
    new = _read(DATA / "new_requests.csv", REQ_COLS).assign(source="Created in demo")
    df = pd.concat([team, new], ignore_index=True)
    # A demo update to a team request overrides the team row
    return df.drop_duplicates("request_id", keep="last")


def load_logs():
    return pd.concat([_read(RAW / "approval_logs.csv", LOG_COLS),
                      _read(DATA / "new_approval_logs.csv", LOG_COLS)], ignore_index=True)


def _append_log(request_id, actor, role, action, comments=""):
    logs = _read(DATA / "new_approval_logs.csv", LOG_COLS)
    event_id = f"D{len(logs) + 1:04d}"
    row = {"event_id": event_id, "request_id": request_id,
           "event_time": datetime.now().isoformat(timespec="minutes"),
           "actor": actor, "actor_role": role, "action": action, "comments": comments}
    pd.concat([logs, pd.DataFrame([row])], ignore_index=True).to_csv(DATA / "new_approval_logs.csv", index=False)


def _save_request(row):
    new = _read(DATA / "new_requests.csv", REQ_COLS)
    new = new[new["request_id"] != row["request_id"]]
    pd.concat([new, pd.DataFrame([row])[REQ_COLS]], ignore_index=True).to_csv(DATA / "new_requests.csv", index=False)


def approval_steps(domain, values):
    """Approval steps for a request. Same routing as the approvals module:
    only rows that require review, matching entity / country ('ALL' matches any)."""
    matrix = load_approval_matrix()
    rows = matrix[matrix["request_type"] == domain].copy()
    if "requires_review" in rows.columns:
        rows = rows[rows["requires_review"].isin(["Yes", ""])]
    request_keys = {"entity": values.get("entity") or values.get("business_entity", ""),
                    "country": values.get("country", "")}
    for col, value in request_keys.items():
        if col in rows.columns and value:
            rows = rows[rows[col].isin(["ALL", "", value])]
    if "condition" in rows.columns:
        rows = rows[[condition_met(c, values) for c in rows["condition"]]]
    rows["step_order"] = rows["step_order"].astype(int)
    return rows.sort_values("step_order").to_dict("records")


def submit_request(domain, values, rules, requestor, override_reason="", candidate=""):
    reqs = load_requests()
    numbers = [int(r[1:]) for r in reqs["request_id"] if r[1:].isdigit()]
    request_id = f"R{max(numbers, default=0) + 1:03d}"

    sensitive = set(rules[(rules["domain"] == domain) & rules["sensitive"]]["field"])
    vault = _read(DATA / "finance_vault.csv", ["request_id", "field", "value"])
    secret = [{"request_id": request_id, "field": k, "value": str(values[k])}
              for k in sensitive if str(values.get(k, "")).strip()]
    if secret:
        pd.concat([vault, pd.DataFrame(secret)], ignore_index=True).to_csv(DATA / "finance_vault.csv", index=False)

    if not str(values.get("country", "")).strip():
        # Item / cost center forms have no country field: use the requestor's country
        users = load_users()
        match = users[users["display_name"] == requestor]
        if not match.empty:
            values = {**values, "country": match.iloc[0]["country"]}
    steps = approval_steps(domain, values)
    notes = f"Duplicate override: {override_reason}" if override_reason else ""
    row = {"request_id": request_id, "submitted_at": datetime.now().isoformat(timespec="minutes"),
           "request_type": domain, "record_name": values.get(NAME_FIELD[domain], ""),
           "requestor": requestor, "country": values.get("country", ""),
           "entity": values.get("business_entity", values.get("entity", "")),
           "status": "Pending approval",
           "current_step": " + ".join(s["approver_role"] for s in steps
                                      if int(s["step_order"]) == int(steps[0]["step_order"])) if steps else "MDM Analyst",
           "candidate_existing_id": candidate, "notes": notes}
    _save_request(row)
    public = {k: v for k, v in values.items() if k not in sensitive and str(v).strip()}
    payloads = _read(DATA / "new_payloads.csv", ["request_id", "payload"])
    payloads = pd.concat([payloads, pd.DataFrame([{"request_id": request_id, "payload": json.dumps(public)}])],
                         ignore_index=True)
    payloads.to_csv(DATA / "new_payloads.csv", index=False)
    _append_log(request_id, requestor, "Requestor", "Submitted", "Form complete; duplicate check run")
    first = [s["approver_role"] for s in steps if int(s["step_order"]) == int(steps[0]["step_order"])] if steps else []
    for role in first:   # same audit row the approvals module writes for later steps
        _append_log(request_id, "system", role, "Routed", "Approval card sent in Teams and Outlook")
    return request_id


COUNTRY_CODES = {"Singapore": "SG", "Malaysia": "MY", "Thailand": "TH", "Indonesia": "ID", "Vietnam": "VN"}
ID_PREFIX = {"Customer": "C", "Item": "I", "Vendor": "V", "Cost Center": "CC"}
SAP_OBJECT = {"Customer": "BusinessPartners", "Item": "Items", "Vendor": "BusinessPartners",
              "Cost Center": "ProfitCenters"}


def create_master_record(request_id, domain):
    """SAP handoff (mock): add the approved record to the master data with the same
    columns as the team file, and to a mock SAP snapshot. Returns the new code."""
    payloads = _read(DATA / "new_payloads.csv", ["request_id", "payload"])
    match = payloads[payloads["request_id"] == request_id]
    if match.empty:
        return ""
    values = json.loads(match.iloc[-1]["payload"])
    file, rename = MASTER_SPEC[domain]
    master = load_master_raw(domain)
    id_col = next(c for c, v in rename.items() if v == "code")
    prefix = ID_PREFIX[domain]
    nums = [int(x[len(prefix):]) for x in master[id_col] if x[len(prefix):].isdigit()]
    width = max((len(x) - len(prefix) for x in master[id_col]), default=3)
    code = f"{prefix}{max(nums, default=0) + 1:0{width}d}"
    row = {c: values.get(c, "") for c in master.columns}
    row[id_col] = code
    defaults = {"active_status": "Active", "status": "Active", "canonical_customer_id": code,
                "country_code": COUNTRY_CODES.get(values.get("country", ""), ""),
                "entity": values.get("entity", values.get("business_entity", ""))}
    for k, v in defaults.items():
        if k in row and not row[k]:
            row[k] = v
    new_path = DATA / f"new_{file}"
    pd.concat([_read(new_path, list(master.columns)), pd.DataFrame([row])], ignore_index=True).to_csv(new_path, index=False)
    snap_path = DATA / "new_sapb1_mock_master_snapshot.csv"
    snap_cols = ["master_type", "sap_object", "mock_sap_code", "source_record_id", "source_system", "sync_status"]
    snap = pd.concat([_read(snap_path, snap_cols), pd.DataFrame([{
        "master_type": domain, "sap_object": SAP_OBJECT[domain], "mock_sap_code": code,
        "source_record_id": request_id, "source_system": "MDM REQUEST FORM (DEMO)",
        "sync_status": "Created via mock handoff"}])], ignore_index=True)
    snap.to_csv(snap_path, index=False)
    return code


def _parse_steps(value):
    """'Finance review' / 'Business Unit Head + Finance' -> ['Finance'] / ['Business Unit Head', 'Finance']."""
    return [x.replace(" review", "").strip() for x in str(value or "").split("+") if x.strip()]


def _approval_state(row):
    """Return (steps, approved_roles, waiting_roles) for a request.
    Steps with the same step_order are approved in parallel; the next step_order
    starts only when every role in the current one has approved."""
    steps = approval_steps(row["request_type"], {"entity": row.get("entity", ""),
                                                  "country": row.get("country", "")})
    roles = [s["approver_role"] for s in steps]
    logs = load_logs()
    logs = logs[logs["request_id"] == row["request_id"]]
    approved = set(logs[logs["action"].str.startswith("Approved")]["actor_role"]) & set(roles)
    status = row.get("status", "")
    if status in ("Completed", "Approved - SAP pending"):
        return steps, set(roles), [], logs
    # Team history has no per-role approvals: trust current_step and treat earlier steps as done
    named = [r for r in _parse_steps(row.get("current_step")) if r in roles]
    if named:
        first = min(int(s["step_order"]) for s in steps if s["approver_role"] in named)
        approved |= {s["approver_role"] for s in steps if int(s["step_order"]) < first}
    waiting = []
    if status == "Pending approval":
        for order in sorted({int(s["step_order"]) for s in steps}):
            group = [s["approver_role"] for s in steps if int(s["step_order"]) == order]
            left = [r for r in group if r not in approved]
            if left:
                waiting = left
                break
    return steps, approved, waiting, logs


def waiting_roles(row):
    return _approval_state(row)[2]


def current_role(row, roles=None):
    """First role a request is waiting on (kept for older callers)."""
    w = waiting_roles(row)
    return w[0] if w else None


def request_progress(row):
    """Steps for a request with their status, rebuilt from the approval matrix and logs."""
    steps, approved, waiting, logs = _approval_state(row)
    status = row["status"]
    out, flagged = [], False
    for s in steps:
        role = s["approver_role"]
        if role in approved:
            st = "Approved"
        elif not flagged and status == "Rejected":
            st, flagged = "Rejected", True
        elif not flagged and status == "Returned for correction":
            st, flagged = "Returned to requestor", True
        elif role in waiting:
            st = "Waiting"
        else:
            st = "Pending"
        out.append({"step": s["step_order"], "approver": role, "sla_hours": s.get("sla_hours", ""), "status": st})
    done = sum(x["status"] == "Approved" for x in out)
    return done, len(out), out, logs


def demo_approve(request_id, users, role=None):
    """Demo helper: one waiting approver approves (parallel steps need every role);
    once all steps are done the MDM analyst hands the record off to SAP B1 (mock)."""
    row = load_requests().set_index("request_id").loc[request_id].to_dict()
    row["request_id"] = request_id
    if row["status"] == "Approved - SAP pending":
        code = create_master_record(request_id, row["request_type"])
        if not code:   # team history request: no form payload, so only a mock code
            code = f"{ID_PREFIX[row['request_type']]}-MOCK-{request_id[1:]}"
        _append_log(request_id, "MDM Team", "MDM Analyst", "SAP handoff complete", f"Mock SAP code {code}")
        row.update(status="Completed", current_step="Finalized", notes=(row["notes"] + f" Mock SAP code {code}").strip())
        _save_request(row)
        return
    waiting = waiting_roles(row)
    if not waiting:
        return
    role = role if role in waiting else waiting[0]
    match = users[users["role"] == role]
    actor = match.iloc[0]["display_name"] if not match.empty else role
    _append_log(request_id, actor, role, "Approved", "Approved in Teams (demo)")
    still = waiting_roles(row)
    if still:
        row.update(status="Pending approval", current_step=" + ".join(still))
    else:
        row.update(status="Approved - SAP pending", current_step="SAP handoff")
    _save_request(row)


def reset_demo():
    olds = ["new_requests.csv", "new_approval_logs.csv", "new_payloads.csv", "new_sapb1_mock_master_snapshot.csv"]
    for f in olds + [f"new_{spec[0]}" for spec in MASTER_SPEC.values()]:
        p = DATA / f
        if p.exists():
            p.unlink()
    pd.DataFrame(columns=["request_id", "field", "value"]).to_csv(DATA / "finance_vault.csv", index=False)
    # Final-review history kept by the Master Data Records page (mock SAP handoffs)
    handoff_db = RAW.parent / "processed" / "mock_sap_handoffs.sqlite3"
    if handoff_db.exists():
        handoff_db.unlink()

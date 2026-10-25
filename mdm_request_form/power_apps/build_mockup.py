"""Build power_apps/MDM_Request_Form_Mockup.html from the team data package.

Embeds data/raw CSVs and request_form/config/field_rules.csv into one self-contained
HTML file (no internet needed). Re-run after the data or field rules change:
    python power_apps/build_mockup.py
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent
RAW = next(p / "data" / "raw" for p in [ROOT, *ROOT.parents] if (p / "data" / "raw" / "customers.csv").exists())


def records(name):
    return pd.read_csv(RAW / name, dtype=str).fillna("").to_dict("records")


def field_rules():
    df = pd.read_csv(ROOT / "request_form" / "config" / "field_rules.csv", dtype=str).fillna("")
    out = []
    for r in df.to_dict("records"):
        opts = r["options"].strip()
        if opts.startswith("@"):
            file, col = opts[1:].split(".", 1)
            vals = pd.read_csv(RAW / f"{file}.csv", dtype=str)[col].dropna().str.strip()
            options = sorted(v for v in vals.unique() if v)
        else:
            options = [o for o in opts.split("|") if o]
        out.append({"domain": r["domain"], "field": r["field"], "label": r["label"], "type": r["type"],
                    "options": options, "required": r["required"].upper() == "TRUE",
                    "required_if": r["required_if"], "sensitive": r["sensitive"].upper() == "TRUE",
                    "help": r["help"]})
    return out


def history(rules, n=8):
    """Latest team requests from mdm_requests.csv, with step index and audit log."""
    reqs = pd.read_csv(RAW / "mdm_requests.csv", dtype=str).fillna("")
    logs = pd.read_csv(RAW / "approval_logs.csv", dtype=str).fillna("")
    out = []
    for r in reqs.tail(n).to_dict("records"):
        route = [x["approver_role"] for x in sorted(
            (x for x in rules if x["request_type"] == r["request_type"]), key=lambda x: x["step_order"])]
        current = r["current_step"].replace(" review", "")
        if r["status"] in ("Completed", "Approved - SAP pending"):
            step = len(route)
        elif r["status"] == "Pending approval":
            step = route.index(current) if current in route else 0
        else:
            step = 0
        log = logs[logs["request_id"] == r["request_id"]]
        out.append({"id": r["request_id"], "type": r["request_type"], "name": r["record_name"],
                    "requestor": r["requestor"], "entity": r["entity"], "country": r["country"],
                    "submitted": r["submitted_at"].replace("T", " "), "status": r["status"], "step": step,
                    "values": {}, "secret": {}, "note": r["notes"],
                    "log": [[e["event_time"].replace("T", " "), e["actor"], e["actor_role"], e["action"]]
                            for e in log.to_dict("records")]})
    return out


def main():
    rules = records("approval_rules.csv")
    for r in rules:
        r["step_order"] = int(r["step_order"])
    data = {
        "customers": records("customers.csv"), "items": records("items.csv"),
        "vendors": records("vendors.csv"), "cost_centers": records("cost_centers.csv"),
        "users": [u for u in records("users_and_roles.csv") if u["active"] == "Yes"],
        "rules": rules, "fields": field_rules(), "history": history(rules),
    }
    match_js = (HERE / "src" / "match.js").read_text(encoding="utf-8")
    match_js = match_js.replace('if (typeof module !== "undefined") module.exports', "// module.exports")
    page = (HERE / "src" / "template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = page.replace("/*__DATA__*/", "const DATA = " + payload + ";").replace("/*__MATCH__*/", match_js)
    out = HERE / "MDM_Request_Form_Mockup.html"
    out.write_text(page, encoding="utf-8")
    print("Wrote", out, f"({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

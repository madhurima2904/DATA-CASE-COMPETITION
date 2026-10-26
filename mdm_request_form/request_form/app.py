"""Lives Group - Smart MDM Request Form (prototype).

Run from this folder:  streamlit run app.py
Uses the team's synthetic data package in ../data/raw. Demo only.
"""
import importlib
from datetime import date

import pandas as pd
import streamlit as st

import mdm
import theme

importlib.reload(mdm)   # pick up edits to mdm.py without restarting the app
importlib.reload(theme)

st.set_page_config(page_title="MDM Requests", layout="wide", initial_sidebar_state="collapsed")


@st.cache_resource
def get_model():
    return mdm.train_classifier()


users = mdm.load_users()

# ---------- Teams / Power Apps shell ----------
st.markdown(theme.CSS, unsafe_allow_html=True)
labels = [f"{r.display_name} - {r.role}" for r in users.itertuples()]
current = st.session_state.get("who", labels[0])
initials = "".join(w[0] for w in current.split(" - ")[0].split())[:2]
st.markdown(theme.chrome_html(initials), unsafe_allow_html=True)

nav, who_col, reset_col = st.columns([6, 2.2, 1], vertical_alignment="bottom")
with nav, st.container(key="tabnav"):
    page = st.radio("Go to", ["New request", "Request tracker", "Inbox triage", "Admin: form rules"],
                    horizontal=True, label_visibility="collapsed")
with who_col:
    who = st.selectbox("Signed in as", labels, key="who")
with reset_col:
    if st.button("Reset demo", width="stretch", help="Clear requests created in this demo"):
        mdm.reset_demo()
        st.rerun()
me = users.iloc[labels.index(who)]


# ---------- page: new request ----------
def render_field(rule, required):
    label = rule["label"] + (" *" if required else "")
    key = f"f_{rule['domain']}_{rule['field']}"
    help_text = rule["help"] or None
    if rule["sensitive"]:
        label += "  (Finance only)"
    t = rule["type"]
    if t == "select":
        return st.selectbox(label, [""] + mdm.field_options(rule), key=key, help=help_text)
    if t == "number":
        return st.number_input(label, min_value=0, step=1, key=key, help=help_text)
    if t == "date":
        return st.date_input(label, value=date.today(), key=key, help=help_text).isoformat()
    if rule["sensitive"]:
        return st.text_input(label, key=key, type="password", help=help_text)
    return st.text_input(label, key=key, help=help_text)


def page_new_request():
    st.title("New master data request")
    st.caption("One form for every request type. Fields and approvers come from rules the MDM team maintains.")

    rules = mdm.load_field_rules()
    domain = st.segmented_control("What do you need?", mdm.DOMAINS, default="Customer", key="domain") or "Customer"
    domain_rules = rules[rules["domain"] == domain]

    values = {}
    left, right = st.columns([3, 2], gap="large")
    with left:
        current = {r["field"]: st.session_state.get(f"f_{domain}_{r['field']}", "")
                   for _, r in domain_rules.iterrows()}
        cols = st.columns(2)
        for i, (_, rule) in enumerate(domain_rules.iterrows()):
            with cols[i % 2]:
                values[rule["field"]] = render_field(rule, mdm.is_required(rule, current))

    with right:
        st.subheader("Live checks")
        name = values.get(mdm.NAME_FIELD[domain], "")
        reg = values.get("registration_no", "")
        dupes = mdm.find_duplicates(domain, name, reg, values.get("country", ""))
        top_level, candidate = "ok", ""
        if name or reg:
            if dupes.empty:
                st.success("No similar records found in SAP B1.")
            else:
                top_level = mdm.duplicate_level(dupes.iloc[0]["score"])
                candidate = dupes.iloc[0]["code"] if top_level != "ok" else ""
                msg = "Possible duplicate found" if top_level != "ok" else "Similar records exist"
                (st.error if top_level == "block" else st.warning)(f"{msg} - please check before submitting:")
                show = dupes[["code", "name", "entity", "country", "score", "reason"]].rename(
                    columns={"score": "match %"})
                st.dataframe(show, hide_index=True, width="stretch")
        else:
            st.info("Start typing a name to check for existing records.")

        problems = mdm.validate(domain, values, rules)
        if problems:
            st.warning("Missing or invalid:\n\n" + "\n".join(f"- {p}" for p in problems))
        else:
            st.success("All required fields complete.")

        st.markdown("**Approval route:**")
        for s in mdm.approval_steps(domain, values):
            st.markdown(f"{s['step_order']}. {s['approver_role']} - reminder after {s['sla_hours']} h")

        override, reason = False, ""
        if top_level == "block":
            override = st.checkbox("I confirmed this is NOT the same record")
            reason = st.text_input("Reason (shown to the MDM team)") if override else ""
            override = override and bool(reason.strip())

        can_submit = not problems and (top_level != "block" or override)
        if st.button("Submit request", type="primary", disabled=not can_submit, width="stretch"):
            rid = mdm.submit_request(domain, values, rules, me["display_name"], reason, candidate)
            st.success(f"Submitted as **{rid}**. The first approver has been notified in Teams.")
            st.balloons()


# ---------- page: request tracker ----------
STATUS_BADGE = {
    "Completed": st.success, "Approved - SAP pending": st.info, "Pending approval": st.warning,
    "Returned for correction": st.warning, "Rejected": st.error,
}


def page_tracker():
    st.title("Request tracker")
    st.caption("Requestors see exactly where a request is; approvers see what is waiting on them.")
    df = mdm.load_requests()

    view = st.segmented_control("View", ["My requests", "Waiting on me", "All requests"],
                                default="My requests", key="view") or "My requests"
    roles = [s["approver_role"] for s in mdm.load_approval_matrix().to_dict("records")]
    if view == "My requests":
        df = df[df["requestor"] == me["display_name"]]
    elif view == "Waiting on me":
        df = df[[me["role"] in mdm.waiting_roles(r) for r in df.to_dict("records")]]

    c1, c2, c3 = st.columns(3)
    types = c1.multiselect("Type", mdm.DOMAINS)
    statuses = c2.multiselect("Status", sorted(df["status"].unique()))
    search = c3.text_input("Search ID or name")
    if types:
        df = df[df["request_type"].isin(types)]
    if statuses:
        df = df[df["status"].isin(statuses)]
    if search:
        mask = df["request_id"].str.contains(search, case=False) | df["record_name"].str.contains(search, case=False)
        df = df[mask]

    counts = df["status"].value_counts()
    m = st.columns(5)
    for i, s in enumerate(["Pending approval", "Returned for correction", "Approved - SAP pending", "Completed", "Rejected"]):
        m[i].metric(s, int(counts.get(s, 0)))

    if df.empty:
        st.info("No requests match. Submit one from 'New request', or switch the view.")
        return

    for _, row in df.iloc[::-1].head(15).iterrows():
        done, total, steps, logs = mdm.request_progress(row)
        with st.container(border=True):
            a, b = st.columns([3, 1])
            a.markdown(f"**{row['request_id']} - {row['request_type']}: {row['record_name']}**  \n"
                       f"{row['entity']} - {row['country']} - by {row['requestor']} - "
                       f"submitted {row['submitted_at'].replace('T', ' ')} - *{row['source']}*")
            STATUS_BADGE.get(row["status"], st.info)(f"{row['status']} ({done}/{total})")
            if row["notes"]:
                a.caption(row["notes"])
            st.progress(done / total if total else 1.0)
            st.dataframe(pd.DataFrame(steps), hide_index=True, width="stretch")
            with st.expander("Audit trail"):
                trail = logs[["event_time", "actor", "actor_role", "action", "comments"]].copy()
                trail["event_time"] = trail["event_time"].str.replace("T", " ")
                st.dataframe(trail, hide_index=True, width="stretch")
            if row["status"] in ("Pending approval", "Approved - SAP pending"):
                label = ("Demo: MDM posts to SAP B1" if row["status"] == "Approved - SAP pending"
                         else "Demo: approve current step")
                if st.button(label, key=f"adv_{row['request_id']}"):
                    mdm.demo_approve(row["request_id"], users, me["role"])
                    st.rerun()
    if len(df) > 15:
        st.caption(f"Showing the latest 15 of {len(df)} requests - use the filters to narrow down.")


# ---------- page: inbox triage ----------
def page_triage():
    st.title("Inbox triage")
    st.caption("Separates actionable purchase orders from enquiries, follow-ups and MDM setup requests, "
               "so only real orders feed confirmed demand.")
    model, acc = get_model()

    with st.container(border=True):
        st.subheader("Try a message")
        org = st.text_input("From (organisation)", value="Penang Heart Centre")
        text = st.text_area("Message", value="Hi team, please process PO56002 for 30 units of B - Lab Consumable 2.")
        if st.button("Classify", type="primary"):
            r = mdm.classify(model, text, org)
            c1, c2 = st.columns(2)
            c1.metric("Label", r["label"])
            c2.metric("Confidence", f"{r['confidence']:.0%}")
            st.write(f"**Route to:** {r['route']}")
            if r["note"]:
                st.warning(r["note"])
            if r["needs_review"]:
                st.info("Low confidence - a person confirms this label.")

    st.subheader("Demo inbox")
    inbox = pd.read_csv(mdm.DATA / "inbox_demo.csv")
    results = [mdm.classify(model, t, o) for o, t in zip(inbox["sender_org"], inbox["text"])]
    inbox["label"] = [r["label"] for r in results]
    inbox["confidence"] = [f"{r['confidence']:.0%}" for r in results]
    inbox["route"] = [r["route"] for r in results]
    inbox["note"] = [r["note"] for r in results]
    st.dataframe(inbox, hide_index=True, width="stretch")

    with st.expander("How the model works"):
        st.markdown(
            f"- TF-IDF text features + logistic regression, trained on labelled example messages.\n"
            f"- Accuracy on held-out messages: **{acc:.0%}** (synthetic templates, so real-world accuracy will be lower).\n"
            f"- An order from an organisation not found in SAP B1 is re-labelled **MDM setup**, "
            f"so the account is created before the order is booked.\n"
            f"- Predictions below 60% confidence go to a person to confirm.\n"
            f"- Matches the team data rule: only `order_status = Confirmed` purchase orders count as demand; "
            f"enquiries and MDM setup requests are tracked separately."
        )


# ---------- page: admin ----------
def page_admin():
    st.title("Admin: form rules")
    st.caption("The MDM team edits these tables directly. Changes apply to the form immediately - no IT, no code.")

    tab1, tab2, tab3 = st.tabs(["Fields", "Approval routing", "Duplicate review"])
    with tab1:
        rules = mdm.load_field_rules()
        dom = st.selectbox("Request type", mdm.DOMAINS, key="admin_dom")
        view = rules[rules["domain"] == dom].reset_index(drop=True)
        edited = st.data_editor(
            view, num_rows="dynamic", width="stretch", hide_index=True,
            column_config={
                "domain": st.column_config.TextColumn(disabled=True),
                "type": st.column_config.SelectboxColumn(options=["text", "select", "number", "email", "date"]),
                "required": st.column_config.CheckboxColumn(),
                "sensitive": st.column_config.CheckboxColumn(),
                "required_if": st.column_config.TextColumn(help="e.g. category=Diagnostic reagent;product_group=Product C"),
            },
            key=f"editor_{dom}",
        )
        if st.button("Save field rules", type="primary"):
            edited["domain"] = dom
            others = rules[rules["domain"] != dom]
            mdm.save_field_rules(pd.concat([others, edited], ignore_index=True))
            st.success("Saved. Open 'New request' to see the change.")

    with tab2:
        matrix = mdm.load_approval_matrix()
        edited_m = st.data_editor(matrix, num_rows="dynamic", width="stretch", hide_index=True,
                                  key="matrix_editor")
        st.caption("Example: add a step for a new business unit or a new regulatory check. "
                   "Condition syntax: field=value|value;other=value (empty = always).")
        if st.button("Save approval routing", type="primary"):
            mdm.save_approval_matrix(edited_m)
            st.success("Saved.")

    with tab3:
        dom2 = st.selectbox("Check master data for", ["Customer", "Item", "Vendor"], key="dup_dom")
        pairs = mdm.find_cross_entity_duplicates(dom2)
        st.write(f"Found **{len(pairs)}** likely duplicate pairs across SPD / QTS / QTG:")
        st.dataframe(pairs.drop(columns=["_a", "_b"]), hide_index=True, width="stretch")
        if dom2 == "Customer":
            ev = mdm.evaluate_customer_dedup()
            st.markdown(
                f"**Check against the seeded answer key** (canonical_customer_id): "
                f"{ev['correct']} of {ev['seeded']} seeded duplicates found, "
                f"{ev['false_alarms']} false alarms (precision {ev['precision']:.0%}, recall {ev['recall']:.0%})."
            )
        st.caption("Suggested merges are reviewed by the MDM analyst - nothing is merged automatically.")


PAGES = {
    "New request": page_new_request,
    "Request tracker": page_tracker,
    "Inbox triage": page_triage,
    "Admin: form rules": page_admin,
}
PAGES[page]()

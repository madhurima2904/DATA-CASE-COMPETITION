import os
import pandas as pd
import streamlit as st
from approvals import *

st.set_page_config(page_title="LivesFlow Approvals", layout="wide")

# Show a pop-up message after an action (survives the page refresh)
if "flash" in st.session_state:
    st.toast(st.session_state.pop("flash"))

# ---------- Who is signed in ----------
users = load(os.path.join(HERE, "data/raw/users_and_roles.csv"))
users = users[users["active"] == "Yes"]
approvers = users[users["role"] != "Requestor"].reset_index(drop=True)

labels = approvers["display_name"] + " · " + approvers["role"] + " (" + approvers["entity"] + ")"
choice = st.sidebar.selectbox("Signed in as", labels)
me = approvers[labels == choice].iloc[0]
st.sidebar.caption("Switch person to see each approver's view, as they would in Teams.")


def is_for_me(me, req, current):
    if me["role"] not in set(current["approver_role"]):
        return False
    same_role = users[users["role"] == me["role"]]
    if (same_role["entity"] == req["entity"]).any():
        return me["entity"] == req["entity"]
    return True


def decide(rid, action, comment):
    add_log(rid, me["display_name"], me["role"], action, comment)
    status, step = update_request(rid)
    st.session_state["flash"] = f"{rid}: {action} → {status} ({step})"
    st.rerun()


# ---------- Find my requests ----------
reqs = load_requests()
pending = reqs[reqs["status"] == "Pending approval"]
mine = []
for _, req in pending.iterrows():
    steps, current = progress(req["request_id"])
    if is_for_me(me, req, current):
        mine.append((req, steps))

tab1, tab2, tab3, tab4 = st.tabs(
    ["Waiting on me", "Overdue & reminders", "Audit trail", "Admin: approval rules"])

# ---------- Tab 1: Waiting on me ----------
with tab1:
    st.title("Waiting on me")
    st.caption(f"{me['display_name']} · {me['role']} · {me['entity']}")

    if not mine:
        st.success("Nothing is waiting on you.")

    for req, steps in mine:
        rid = req["request_id"]
        with st.container(border=True):
            st.markdown(f"### {rid} · {req['request_type']}: {req['record_name']}")
            st.caption(f"{req['entity']} · {req['country']} · requested by "
                       f"{req['requestor']} · submitted {req['submitted_at']}")
            st.dataframe(steps[["step_order", "approver_role", "sla_hours", "done"]],
                         hide_index=True)

            with st.expander("Request details"):
                details = masked(req.to_dict(), me["role"])
                st.dataframe(pd.DataFrame(details.items(), columns=["field", "value"]),
                             hide_index=True)

            comment = st.text_input("Comment", key=f"c_{rid}")
            a, b, c = st.columns(3)
            if a.button("Approve", key=f"a_{rid}", type="primary"):
                decide(rid, "Approved", comment or "Approved")
            if b.button("Request changes", key=f"b_{rid}"):
                if not comment:
                    st.error("Please say what needs changing.")
                else:
                    decide(rid, "Changes requested", comment)
            if c.button("Reject", key=f"r_{rid}"):
                if not comment:
                    st.error("Please give a reason for rejecting.")
                else:
                    decide(rid, "Rejected", comment)

# ---------- Tab 2: Overdue & reminders ----------
with tab2:
    st.title("Overdue & reminders")
    st.caption("Approvals waiting longer than their SLA. Past 2x SLA they are escalated.")
    od = overdue_list()

    m1, m2, m3 = st.columns(3)
    m1.metric("Pending approval", int((load_requests()["status"] == "Pending approval").sum()))
    m2.metric("Overdue", len(od))
    m3.metric("Escalated", int(od["escalate"].sum()) if not od.empty else 0)

    if od.empty:
        st.success("Nothing is overdue.")
    else:
        st.dataframe(od, hide_index=True)
        if st.button("Send reminders", type="primary"):
            n = send_reminders()
            st.session_state["flash"] = f"Reminders sent for {n} requests."
            st.rerun()

# ---------- Tab 3: Audit trail ----------
with tab3:
    st.title("Audit trail")
    st.caption("Every action on a request, in order. Rows are only ever added, never edited.")
    rid = st.selectbox("Request", load_requests()["request_id"])
    st.dataframe(load_logs().query("request_id == @rid"), hide_index=True)

# ---------- Tab 4: Admin ----------
with tab4:
    st.title("Admin: approval rules")
    st.caption("Change who approves what, for any business unit or country. "
               "No code and no IT. Every old version is kept.")
    rules = load(RULES)

    if me["role"] != "MDM Analyst":
        st.info("Only the MDM team can edit rules. Sign in as Priya Shah to edit.")
        st.dataframe(rules, hide_index=True)
    else:
        edited = st.data_editor(rules, num_rows="dynamic", hide_index=True,
                                key="rules_editor")
        if st.button("Save rules", type="primary"):
            save_rules(edited, me["display_name"])
            st.session_state["flash"] = "Rules saved. Requests use them straight away."
            st.rerun()

    st.subheader("Rule change history")
    st.dataframe(load(LOGS, LOG_COLS).query("request_id == 'RULES'"), hide_index=True)

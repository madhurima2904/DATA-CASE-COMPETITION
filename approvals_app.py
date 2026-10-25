import streamlit as st
from approvals import *

st.set_page_config(page_title="LivesFlow Approvals", layout="wide")

# ---------- Who is signed in ----------
users = load("data/raw/users_and_roles.csv")
users = users[users["active"] == "Yes"]
approvers = users[users["role"] != "Requestor"].reset_index(drop=True)

labels = approvers["display_name"] + " · " + approvers["role"] + " (" + approvers["entity"] + ")"
choice = st.sidebar.selectbox("Signed in as", labels)
me = approvers[labels == choice].iloc[0]


# ---------- Is this request for me? ----------
def is_for_me(me, req, current):
    # 1. My role must be one of the approvers needed right now
    if me["role"] not in set(current["approver_role"]):
        return False
    # 2. If someone with my role belongs to this request's entity,
    #    only they get it (e.g. QTG requests go to the QTG BU Head)
    same_role = users[users["role"] == me["role"]]
    if (same_role["entity"] == req["entity"]).any():
        return me["entity"] == req["entity"]
    # 3. Otherwise anyone with my role can approve it
    return True


# ---------- Find my requests ----------
reqs = load(REQUESTS)
pending = reqs[reqs["status"] == "Pending approval"]

mine = []
for _, req in pending.iterrows():
    steps, current = progress(req["request_id"])
    if is_for_me(me, req, current):
        mine.append((req, steps))


# ---------- Show them ----------
tab1, tab2, tab3 = st.tabs(["Waiting on me", "Overdue & reminders", "Audit trail"])
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

            comment = st.text_input("Comment", key=f"c_{rid}")
            a, b, c = st.columns(3)

            if a.button("Approve", key=f"a_{rid}", type="primary"):
                add_log(rid, me["display_name"], me["role"], "Approved", comment or "Approved")
                update_request(rid)
                st.rerun()

            if b.button("Request changes", key=f"b_{rid}"):
                if not comment:
                    st.error("Please say what needs changing.")
                else:
                    add_log(rid, me["display_name"], me["role"], "Changes requested", comment)
                    update_request(rid)
                    st.rerun()

            if c.button("Reject", key=f"r_{rid}"):
                if not comment:
                    st.error("Please give a reason for rejecting.")
                else:
                    add_log(rid, me["display_name"], me["role"], "Rejected", comment)
                    update_request(rid)
                    st.rerun()
                    
with tab2:
    st.title("Overdue & reminders")
    st.caption("Approvals waiting longer than their SLA. Past 2x SLA they are escalated.")
    od = overdue_list()
    if od.empty:
        st.success("Nothing is overdue.")
    else:
        st.dataframe(od, hide_index=True)
        if st.button("Send reminders", type="primary"):
            n = send_reminders()
            st.success(f"Reminders sent for {n} requests.")

with tab3:
    st.title("Audit trail")
    st.caption("Every action on a request, in order. Rows are only ever added, never edited.")
    rid = st.selectbox("Request", load(REQUESTS)["request_id"])
    trail = load(LOGS).query("request_id == @rid")
    st.dataframe(trail, hide_index=True)
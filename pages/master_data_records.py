
from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher
from html import escape
import json
import re
import sqlite3

import pandas as pd
import streamlit as st


# ============================================================
# LIVESFLOW — MASTER DATA MANAGEMENT
# ============================================================
# Connected to:
# 1. The original team request and approval CSV files
# 2. Your friend's Streamlit request/approval prototype
#
# Only "Approved - SAP pending" requests enter the queue.
#
# SAP Business One is SIMULATED, not connected to a live SAP.
# ============================================================


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

FORM = ROOT / "mdm_request_form" / "request_form"
FORM_DATA = FORM / "data"

DB = PROCESSED / "mock_sap_handoffs.sqlite3"

REQUEST_COLS = [
    "request_id",
    "submitted_at",
    "request_type",
    "record_name",
    "requestor",
    "country",
    "entity",
    "status",
    "current_step",
    "candidate_existing_id",
    "notes",
]

LOG_COLS = [
    "event_id",
    "request_id",
    "event_time",
    "actor",
    "actor_role",
    "action",
    "comments",
]

MASTER_FILES = {
    "Customer": ("customers.csv", "customer_id", "customer_name"),
    "Item": ("items.csv", "item_id", "item_name"),
    "Vendor": ("vendors.csv", "vendor_id", "vendor_name"),
    "Cost Center": (
        "cost_centers.csv",
        "cost_center_id",
        "cost_center_name",
    ),
}

PREFIX = {
    "Customer": "C",
    "Item": "I",
    "Vendor": "V",
    "Cost Center": "CC",
}


# ============================================================
# DESIGN
# ============================================================

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background: #f5f7fb !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"] {
        background: #14243b !important;
    }

    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3 {
        color: #253249 !important;
    }

    [data-testid="stMain"] p,
    [data-testid="stMain"] label {
        color: #344158;
    }

    [data-testid="stMetric"] {
        background: transparent !important;
        border: 1px solid #dce4ef !important;
        border-radius: 13px !important;
        padding: 16px !important;
        box-shadow: none !important;
    }

    [data-testid="stMetricLabel"] p {
        color: #68788f !important;
        font-size: 13px !important;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        color: #253249 !important;
        font-size: 28px !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-color: #dce4ef !important;
        border-radius: 13px !important;
    }

    [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid #dce4ef;
    }

    button[data-baseweb="tab"] {
        background: transparent !important;
    }

    [data-testid="stTabs"]
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #386fe5 !important;
    }

    [data-testid="stTabs"]
    [data-baseweb="tab-highlight"] {
        background: #386fe5 !important;
    }

    [data-baseweb="select"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: rgba(255,255,255,0.45) !important;
        color: #253249 !important;
        border-radius: 9px !important;
    }

    .lf-table-wrap {
        width: 100%;
        overflow-x: auto;
        background: transparent;
        border: 1px solid #dce4ef;
        border-radius: 11px;
        margin: 12px 0 20px;
    }

    .lf-table {
        width: 100%;
        border-collapse: collapse;
        background: transparent !important;
        font-size: 13px;
    }

    .lf-table thead,
    .lf-table tbody,
    .lf-table tr,
    .lf-table th,
    .lf-table td {
        background: transparent !important;
    }

    .lf-table th {
        text-align: left;
        color: #66758c;
        font-weight: 650;
        padding: 13px;
        border-bottom: 1px solid #dce4ef;
        white-space: nowrap;
    }

    .lf-table td {
        padding: 12px 13px;
        color: #253249;
        border-bottom: 1px solid #e2e8f1;
    }

    .lf-table tr:last-child td {
        border-bottom: none;
    }

    .lf-section {
        color: #253249;
        font-weight: 700;
        font-size: 17px;
        margin: 18px 0 6px;
    }

    .lf-subtitle {
        font-size: 13px;
        color: #718096;
        margin-bottom: 12px;
    }

    [data-testid="stBaseButton-primary"] {
        background: #386fe5 !important;
        border: none !important;
        color: white !important;
        border-radius: 9px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize(value):
    value = clean(value).casefold()
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    return " ".join(value.split())


def read_csv(path, columns=None):
    if not path.exists():
        return pd.DataFrame(columns=columns or [])

    df = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
    )

    for col in columns or []:
        if col not in df.columns:
            df[col] = ""

    return df


def heading(title, description=""):
    st.markdown(
        f'<div class="lf-section">{escape(title)}</div>',
        unsafe_allow_html=True,
    )
    if description:
        st.markdown(
            f'<div class="lf-subtitle">{escape(description)}</div>',
            unsafe_allow_html=True,
        )


def show_table(df, limit=150):
    if df.empty:
        st.info("No records found.")
        return

    df = df.head(limit).fillna("")

    th = "".join(
        f"<th>{escape(str(c))}</th>"
        for c in df.columns
    )

    rows = []
    for record in df.itertuples(index=False, name=None):
        td = "".join(
            f"<td>{escape(str(value))}</td>"
            for value in record
        )
        rows.append(f"<tr>{td}</tr>")

    st.markdown(
        '<div class="lf-table-wrap">'
        '<table class="lf-table">'
        f"<thead><tr>{th}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>",
        unsafe_allow_html=True,
    )


def details_table(pairs):
    return pd.DataFrame(
        pairs,
        columns=["Field", "Details"],
    )


def timestamp():
    return datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")


# ============================================================
# CONNECTED REQUEST AND APPROVAL DATA
# ============================================================

def load_requests():
    """
    Combine team history and newly submitted form requests.
    The latest demo copy overrides the original request.
    This follows your friend's mdm.py storage approach.
    """

    team = read_csv(
        RAW / "mdm_requests.csv",
        REQUEST_COLS,
    )
    demo = read_csv(
        FORM_DATA / "new_requests.csv",
        REQUEST_COLS,
    )

    team["source"] = "Team History"
    demo["source"] = "Request Form"

    combined = pd.concat(
        [team, demo],
        ignore_index=True,
    )

    return combined.drop_duplicates(
        "request_id",
        keep="last",
    ).reset_index(drop=True)


def load_approval_logs():
    team = read_csv(
        RAW / "approval_logs.csv",
        LOG_COLS,
    )
    demo = read_csv(
        FORM_DATA / "new_approval_logs.csv",
        LOG_COLS,
    )

    return pd.concat(
        [team, demo],
        ignore_index=True,
    )


def load_payloads():
    payloads = read_csv(
        FORM_DATA / "new_payloads.csv",
        ["request_id", "payload"],
    )

    return payloads.drop_duplicates(
        "request_id",
        keep="last",
    )


def request_payload(request_id, payloads):
    rows = payloads[
        payloads["request_id"] == request_id
    ]

    if rows.empty:
        return {}

    try:
        result = json.loads(
            rows.iloc[-1]["payload"]
        )
        return result if isinstance(result, dict) else {}
    except (ValueError, TypeError):
        return {}


# ============================================================
# DATABASE — PRESERVE EXISTING HANDOFF HISTORY
# ============================================================

def db_connection():
    PROCESSED.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(
        DB,
        timeout=20,
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS handoffs (
            request_id TEXT PRIMARY KEY,
            master_type TEXT NOT NULL,
            record_name TEXT NOT NULL,
            mock_sap_code TEXT NOT NULL UNIQUE,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            reviewed_by TEXT NOT NULL,
            review_note TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            response_json TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS resolutions (
            request_id TEXT PRIMARY KEY,
            record_name TEXT NOT NULL,
            master_type TEXT NOT NULL,
            decision TEXT NOT NULL,
            existing_code TEXT,
            reviewed_by TEXT NOT NULL,
            review_note TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    return conn


def load_handoffs():
    with db_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM handoffs ORDER BY created_at DESC",
            conn,
        )


def load_resolutions():
    with db_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM resolutions ORDER BY created_at DESC",
            conn,
        )


# ============================================================
# SYNC RESULT BACK TO THE REQUEST FORM
# ============================================================

def sync_request_status(request_id, status, current_step, note):
    """
    Update the demo request only.

    Original data/raw files are never modified.
    """

    path = FORM_DATA / "new_requests.csv"
    demo = read_csv(path, REQUEST_COLS)

    mask = demo["request_id"] == request_id

    if not mask.any():
        return False

    demo.loc[mask, "status"] = status
    demo.loc[mask, "current_step"] = current_step

    old_note = clean(
        demo.loc[mask, "notes"].iloc[-1]
    )

    demo.loc[mask, "notes"] = (
        f"{old_note} | {note}".strip(" |")
    )

    demo.to_csv(path, index=False)
    return True


def log_final_action(request_id, reviewer, action, comment):
    """
    Append a final action only for requests that exist
    in the demo Request Form data.
    """

    demo = read_csv(
        FORM_DATA / "new_requests.csv",
        REQUEST_COLS,
    )

    if request_id not in set(demo["request_id"]):
        return

    path = FORM_DATA / "new_approval_logs.csv"
    logs = read_csv(path, LOG_COLS)

    duplicate_event = logs[
        (logs["request_id"] == request_id)
        & (logs["action"] == action)
    ]

    if not duplicate_event.empty:
        return

    event = {
        "event_id": (
            "MDM-"
            + request_id
            + "-"
            + datetime.now(timezone.utc).strftime(
                "%Y%m%d%H%M%S%f"
            )
        ),
        "request_id": request_id,
        "event_time": timestamp(),
        "actor": reviewer,
        "actor_role": "MDM Analyst",
        "action": action,
        "comments": comment,
    }

    logs = pd.concat(
        [logs, pd.DataFrame([event])],
        ignore_index=True,
    )

    logs.to_csv(path, index=False)


# ============================================================
# VALIDATION
# ============================================================

def validate_request(record, payload):
    fields = {
        "Request ID": "request_id",
        "Record Type": "request_type",
        "Record Name": "record_name",
        "Country": "country",
        "Business Entity": "entity",
    }

    results = []

    for label, column in fields.items():
        value = clean(record.get(column, ""))

        results.append({
            "Check": label,
            "Result": "Complete" if value else "Missing",
        })

    supported = (
        clean(record.get("request_type"))
        in MASTER_FILES
    )

    results.append({
        "Check": "Supported Record Type",
        "Result": (
            "Complete" if supported else "Unsupported"
        ),
    })

    checks = pd.DataFrame(results)

    return (
        checks["Result"].eq("Complete").all(),
        checks,
    )


# ============================================================
# AUTOMATIC DUPLICATE DETECTION
# ============================================================

def find_duplicates(record, handoffs):
    kind = clean(record.get("request_type"))

    if kind not in MASTER_FILES:
        return pd.DataFrame()

    filename, id_col, name_col = MASTER_FILES[kind]

    original = read_csv(RAW / filename)
    new_master = read_csv(
        FORM_DATA / f"new_{filename}"
    )

    masters = pd.concat(
        [original, new_master],
        ignore_index=True,
    )

    target = normalize(
        record.get("record_name")
    )

    matches = []

    if name_col in masters.columns and target:
        for _, existing in masters.iterrows():
            existing_name = clean(
                existing.get(name_col)
            )

            if not existing_name:
                continue

            score = SequenceMatcher(
                None,
                target,
                normalize(existing_name),
            ).ratio()

            if score >= 0.80:
                matches.append({
                    "Source": "Master Data",
                    "Existing Code": clean(
                        existing.get(id_col)
                    ),
                    "Existing Name": existing_name,
                    "Match": (
                        "Exact name" if score == 1
                        else "Similar name"
                    ),
                    "Similarity": f"{score * 100:.0f}%",
                })

    if not handoffs.empty and target:
        previous = handoffs[
            handoffs["master_type"] == kind
        ]

        for _, existing in previous.iterrows():
            score = SequenceMatcher(
                None,
                target,
                normalize(existing["record_name"]),
            ).ratio()

            if score >= 0.80:
                matches.append({
                    "Source": "Mock Handoff Log",
                    "Existing Code": existing["mock_sap_code"],
                    "Existing Name": existing["record_name"],
                    "Match": "Previously processed",
                    "Similarity": f"{score * 100:.0f}%",
                })

    flagged = clean(
        record.get("candidate_existing_id")
    )

    if flagged:
        matches.append({
            "Source": "Request Form",
            "Existing Code": flagged,
            "Existing Name": "Flagged existing record",
            "Match": "Review required",
            "Similarity": "—",
        })

    if not matches:
        return pd.DataFrame()

    return pd.DataFrame(
        matches
    ).drop_duplicates()


# ============================================================
# FINAL HANDOFF AND REVIEW DECISIONS
# ============================================================

def save_handoff(record, reviewer, note, duplicate_override):
    request_id = clean(record["request_id"])
    kind = clean(record["request_type"])

    mock_code = (
        f"MOCK-{PREFIX[kind]}-{request_id}"
    )

    payload = {
        "requestId": request_id,
        "recordType": kind,
        "recordName": clean(record["record_name"]),
        "reviewedBy": reviewer,
        "duplicateOverride": duplicate_override,
    }

    response = {
        "simulation": True,
        "status": "SIMULATED_SUCCESS",
        "mockSapCode": mock_code,
    }

    try:
        with db_connection() as conn:
            conn.execute(
                """
                INSERT INTO handoffs (
                    request_id,
                    master_type,
                    record_name,
                    mock_sap_code,
                    state,
                    created_at,
                    reviewed_by,
                    review_note,
                    payload_json,
                    response_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    kind,
                    clean(record["record_name"]),
                    mock_code,
                    "Simulated handoff complete",
                    timestamp(),
                    reviewer,
                    note,
                    json.dumps(payload),
                    json.dumps(response),
                ),
            )
    except sqlite3.IntegrityError:
        return False

    changed = sync_request_status(
        request_id,
        "Completed",
        "Finalized",
        f"Mock SAP reference: {mock_code}",
    )

    if changed:
        log_final_action(
            request_id,
            reviewer,
            "SAP handoff complete",
            f"Mock SAP reference: {mock_code}",
        )

    return True


def save_resolution(record, decision, existing_code, reviewer, note):
    request_id = clean(record["request_id"])

    try:
        with db_connection() as conn:
            conn.execute(
                """
                INSERT INTO resolutions (
                    request_id,
                    record_name,
                    master_type,
                    decision,
                    existing_code,
                    reviewed_by,
                    review_note,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    clean(record["record_name"]),
                    clean(record["request_type"]),
                    decision,
                    existing_code,
                    reviewer,
                    note,
                    timestamp(),
                ),
            )
    except sqlite3.IntegrityError:
        return False

    if decision == "Use Existing Record":
        status = "Completed"
        step = "Finalized"
        action = "Resolved using existing record"
    else:
        status = "Returned for correction"
        step = "Requestor"
        action = "Returned for correction"

    changed = sync_request_status(
        request_id,
        status,
        step,
        note,
    )

    if changed:
        log_final_action(
            request_id,
            reviewer,
            action,
            note,
        )

    return True


# ============================================================
# LOAD ALL CONNECTED DATA
# ============================================================

requests = load_requests()
logs = load_approval_logs()
payloads = load_payloads()

handoffs = load_handoffs()
resolutions = load_resolutions()

approved = requests[
    requests["status"].map(
        lambda x: clean(x).casefold()
    ) == "approved - sap pending"
].copy()

processed = set(
    handoffs["request_id"].astype(str)
)

processed.update(
    resolutions["request_id"].astype(str)
)

queue = approved[
    ~approved["request_id"].isin(processed)
].copy()


# ============================================================
# PAGE HEADER
# ============================================================

st.title("Master Data Management")

st.caption(
    "Final validation of approved master data requests "
    "before simulated SAP Business One handoff."
)

if not FORM.exists():
    st.warning(
        "The request form folder was not found at "
        f"{FORM}. Team history will still be available."
    )

if FORM.exists() and not (FORM_DATA / "new_requests.csv").exists():
    st.info(
        "The Request Form is connected, but no new requests "
        "have been saved yet."
    )

with st.expander("Connected Data Sources"):
    st.write("Request Form data:")
    st.code(str(FORM_DATA / "new_requests.csv"))

    st.write("Approval history:")
    st.code(str(FORM_DATA / "new_approval_logs.csv"))

    st.caption(
        "Requests enter this queue after their status "
        "becomes Approved - SAP pending."
    )


# ============================================================
# KPI CARDS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("Approved Requests", len(approved))
c2.metric("Pending Final Review", len(queue))
c3.metric("Completed Mock Handoffs", len(handoffs))
c4.metric("Review Decisions", len(resolutions))

st.write("")


# ============================================================
# MAIN TABS
# ============================================================

tab_queue, tab_directory, tab_history = st.tabs([
    "SAP Handoff Queue",
    "Master Data Directory",
    "Handoff Log",
])


# ============================================================
# TAB 1 — APPROVED REQUESTS
# ============================================================

with tab_queue:
    heading(
        "Ready for SAP Review",
        "Approved requests that require final MDM validation.",
    )

    if queue.empty:
        st.info(
            "There are no requests waiting for final review. "
            "Submit and approve a new request through the "
            "Request Form prototype."
        )

    else:
        filter1, filter2 = st.columns(2)

        with filter1:
            selected_type = st.selectbox(
                "Record Type",
                ["All"] + sorted(
                    queue["request_type"].unique().tolist()
                ),
            )

        with filter2:
            selected_source = st.selectbox(
                "Request Source",
                ["All", "Team History", "Request Form"],
            )

        filtered = queue.copy()

        if selected_type != "All":
            filtered = filtered[
                filtered["request_type"] == selected_type
            ]

        if selected_source != "All":
            filtered = filtered[
                filtered["source"] == selected_source
            ]

        if filtered.empty:
            st.info("No requests match these filters.")

        else:
            display_cols = [
                "request_id",
                "request_type",
                "record_name",
                "country",
                "entity",
                "source",
            ]

            show_table(
                filtered[display_cols].rename(
                    columns={
                        "request_id": "Request ID",
                        "request_type": "Record Type",
                        "record_name": "Record Name",
                        "country": "Country",
                        "entity": "Business Entity",
                        "source": "Source",
                    }
                )
            )

            selected_id = st.selectbox(
                "Select Request",
                filtered["request_id"].tolist(),
                format_func=lambda rid: (
                    f"{rid} — "
                    + filtered.loc[
                        filtered["request_id"] == rid,
                        "record_name",
                    ].iloc[0]
                ),
            )

            record = filtered[
                filtered["request_id"] == selected_id
            ].iloc[0]

            payload = request_payload(
                selected_id,
                payloads,
            )

            with st.container(border=True):
                heading("Request Details")

                show_table(
                    details_table([
                        ("Request ID", selected_id),
                        ("Record Type", record["request_type"]),
                        ("Record Name", record["record_name"]),
                        ("Country", record["country"]),
                        ("Business Entity", record["entity"]),
                        ("Submitted By", record["requestor"]),
                        ("Status", record["status"]),
                        ("Source", record["source"]),
                    ])
                )

                if payload:
                    with st.expander("Additional Request Information"):
                        show_table(
                            pd.DataFrame([
                                {
                                    "Field": str(k).replace(
                                        "_", " "
                                    ).title(),
                                    "Value": str(v),
                                }
                                for k, v in payload.items()
                            ])
                        )

                heading("Approval History")

                request_logs = logs[
                    logs["request_id"] == selected_id
                ].copy()

                if request_logs.empty:
                    st.warning(
                        "No approval events found for this request."
                    )
                else:
                    show_table(
                        request_logs[
                            [
                                "event_time",
                                "actor",
                                "actor_role",
                                "action",
                                "comments",
                            ]
                        ].rename(
                            columns={
                                "event_time": "Date & Time",
                                "actor": "Performed By",
                                "actor_role": "Role",
                                "action": "Action",
                                "comments": "Comments",
                            }
                        )
                    )

                heading(
                    "Automatic Validation",
                    "Check the required master data fields.",
                )

                valid, validation_results = validate_request(
                    record,
                    payload,
                )

                show_table(validation_results)

                if valid:
                    st.success(
                        "All basic required fields are complete."
                    )
                else:
                    st.error(
                        "Some required fields are missing. "
                        "The mock handoff cannot proceed."
                    )

                heading(
                    "Automatic Duplicate Check",
                    "Search existing master data and previous mock handoffs.",
                )

                duplicates = find_duplicates(
                    record,
                    handoffs,
                )

                if duplicates.empty:
                    st.success(
                        "No potential duplicates detected "
                        "in the available records."
                    )
                else:
                    st.warning(
                        f"{len(duplicates)} possible match(es) found. "
                        "Please review before continuing."
                    )

                    show_table(duplicates)

                heading(
                    "Final Review",
                    "Confirm the master data before simulated SAP handoff.",
                )

                if duplicates.empty:
                    decisions = [
                        "Complete Mock Handoff",
                        "Send Back for Review",
                    ]
                else:
                    decisions = [
                        "Confirm Different Record and Complete Handoff",
                        "Use Existing Record",
                        "Send Back for Review",
                    ]

                with st.form(
                    f"review_form_{selected_id}"
                ):
                    decision = st.radio(
                        "Review Decision",
                        decisions,
                    )

                    existing_code = ""

                    if decision == "Use Existing Record":
                        existing_code = st.selectbox(
                            "Select Existing Record",
                            duplicates[
                                "Existing Code"
                            ].astype(str).tolist(),
                        )

                    reviewer = st.text_input(
                        "Reviewed By",
                        placeholder="e.g. MDM Team",
                    )

                    notes = st.text_area(
                        "Review Notes",
                        placeholder=(
                            "Explain the validation result "
                            "and your review decision."
                        ),
                    )

                    confirmed = st.checkbox(
                        "I have checked the request details, "
                        "approval history and duplicate results."
                    )

                    submitted = st.form_submit_button(
                        "Save Review Decision",
                        type="primary",
                    )

                if submitted:
                    if not reviewer.strip():
                        st.error(
                            "Please enter the reviewer name."
                        )

                    elif not notes.strip():
                        st.error(
                            "Please enter review notes."
                        )

                    elif not confirmed:
                        st.error(
                            "Please confirm that the review is complete."
                        )

                    elif decision == "Send Back for Review":
                        success = save_resolution(
                            record,
                            "Send Back for Review",
                            "",
                            reviewer.strip(),
                            notes.strip(),
                        )

                        if success:
                            st.rerun()
                        else:
                            st.warning(
                                "This request was already processed."
                            )

                    elif decision == "Use Existing Record":
                        success = save_resolution(
                            record,
                            "Use Existing Record",
                            existing_code,
                            reviewer.strip(),
                            notes.strip(),
                        )

                        if success:
                            st.rerun()
                        else:
                            st.warning(
                                "This request was already processed."
                            )

                    elif not valid:
                        st.error(
                            "The request has missing information. "
                            "Please return it for correction."
                        )

                    else:
                        success = save_handoff(
                            record,
                            reviewer.strip(),
                            notes.strip(),
                            not duplicates.empty,
                        )

                        if success:
                            st.rerun()
                        else:
                            st.warning(
                                "This request was already processed."
                            )


# ============================================================
# TAB 2 — MASTER DATA DIRECTORY
# ============================================================

with tab_directory:
    heading(
        "Master Data Directory",
        "Browse the existing master records used for duplicate screening.",
    )

    master_type = st.selectbox(
        "Record Type",
        list(MASTER_FILES.keys()),
        key="master_type_directory",
    )

    filename, _, _ = MASTER_FILES[master_type]

    original = read_csv(
        RAW / filename
    )

    demo = read_csv(
        FORM_DATA / f"new_{filename}"
    )

    if not original.empty:
        original["Source"] = "Team Master Data"

    if not demo.empty:
        demo["Source"] = "Request Form Demo"

    directory = pd.concat(
        [original, demo],
        ignore_index=True,
    )

    search = st.text_input(
        "Search Master Data",
        placeholder="Search name, code or other fields",
    )

    if search.strip() and not directory.empty:
        mask = directory.astype(str).apply(
            lambda col: col.str.contains(
                search.strip(),
                case=False,
                regex=False,
            )
        ).any(axis=1)

        directory = directory[mask]

    show_table(directory)

    st.caption(
        "Original master data is read-only. "
        "Simulated handoffs are stored separately."
    )


# ============================================================
# TAB 3 — HANDOFF LOG
# ============================================================

with tab_history:
    heading(
        "Handoff Log",
        "Review completed mock handoffs and final decisions.",
    )

    history_tab, review_tab = st.tabs([
        "Completed Handoffs",
        "Review Decisions",
    ])

    with history_tab:
        if handoffs.empty:
            st.info("No mock handoffs have been completed.")

        else:
            show_table(
                handoffs[
                    [
                        "request_id",
                        "master_type",
                        "record_name",
                        "mock_sap_code",
                        "created_at",
                        "reviewed_by",
                    ]
                ].rename(
                    columns={
                        "request_id": "Request ID",
                        "master_type": "Record Type",
                        "record_name": "Record Name",
                        "mock_sap_code": "Mock SAP Reference",
                        "created_at": "Completed At (UTC)",
                        "reviewed_by": "Reviewed By",
                    }
                )
            )

            selected_log = st.selectbox(
                "View Handoff Details",
                handoffs["request_id"].tolist(),
            )

            selected = handoffs[
                handoffs["request_id"] == selected_log
            ].iloc[0]

            with st.container(border=True):
                heading("SAP Handoff Summary")

                st.success(
                    "Mock handoff completed successfully. "
                    "No real SAP record was created."
                )

                show_table(
                    details_table([
                        ("Request ID", selected["request_id"]),
                        ("Record Name", selected["record_name"]),
                        ("Record Type", selected["master_type"]),
                        (
                            "Mock SAP Reference",
                            selected["mock_sap_code"],
                        ),
                        ("Status", selected["state"]),
                        ("Reviewed By", selected["reviewed_by"]),
                        ("Review Notes", selected["review_note"]),
                        (
                            "Completed At (UTC)",
                            selected["created_at"],
                        ),
                    ])
                )

            st.download_button(
                "Download Handoff Log",
                handoffs.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name="livesflow_handoff_log.csv",
                mime="text/csv",
            )

    with review_tab:
        if resolutions.empty:
            st.info("No final review decisions recorded.")

        else:
            show_table(
                resolutions.rename(
                    columns={
                        "request_id": "Request ID",
                        "record_name": "Record Name",
                        "master_type": "Record Type",
                        "decision": "Decision",
                        "existing_code": "Existing Record",
                        "reviewed_by": "Reviewed By",
                        "review_note": "Review Notes",
                        "created_at": "Reviewed At (UTC)",
                    }
                )
            )


# ============================================================
# FOOTER
# ============================================================

st.write("")
st.divider()

st.caption(
    "LivesFlow | Connected Request and Approval Prototype | "
    "Simulated SAP Business One Handoff"
)

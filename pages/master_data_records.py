
"""
LivesFlow — Master Data Management

Connected workflows:
    Request Form
        -> Approval Management
        -> Master Data Records
        -> Simulated SAP Business One

Data sources:
    data/raw/mdm_requests.csv
    data/raw/approval_logs.csv

    mdm_request_form/request_form/data/new_requests.csv
    mdm_request_form/request_form/data/new_approval_logs.csv
    mdm_request_form/request_form/data/new_payloads.csv

    data/demo/mdm_requests.csv
    data/demo/approval_logs.csv

Final review history:
    data/processed/mock_sap_handoffs.sqlite3

Important:
    - Original data/raw CSV files are read-only.
    - SAP handoffs are simulations.
    - The app does not connect to a real SAP system.
    - Keep this page registered in your main app.py.
"""

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
# PATHS AND CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

RAW = ROOT / "data" / "raw"
DEMO = ROOT / "data" / "demo"

FORM_DATA = (
    ROOT
    / "mdm_request_form"
    / "request_form"
    / "data"
)

PROCESSED = ROOT / "data" / "processed"
DATABASE = PROCESSED / "mock_sap_handoffs.sqlite3"

REQUEST_COLUMNS = [
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

LOG_COLUMNS = [
    "event_id",
    "request_id",
    "event_time",
    "actor",
    "actor_role",
    "action",
    "comments",
]

MASTER_CONFIG = {
    "Customer": {
        "file": "customers.csv",
        "id": "customer_id",
        "name": "customer_name",
        "prefix": "C",
    },
    "Item": {
        "file": "items.csv",
        "id": "item_id",
        "name": "item_name",
        "prefix": "I",
    },
    "Vendor": {
        "file": "vendors.csv",
        "id": "vendor_id",
        "name": "vendor_name",
        "prefix": "V",
    },
    "Cost Center": {
        "file": "cost_centers.csv",
        "id": "cost_center_id",
        "name": "cost_center_name",
        "prefix": "CC",
    },
}

APPROVED_STATUS = "Approved - SAP pending"
COMPLETED_STATUS = "Completed"
RETURNED_STATUS = "Returned for correction"

REQUEST_SOURCES = {
    "Team History": RAW / "mdm_requests.csv",
    "Request Form": FORM_DATA / "new_requests.csv",
    "Approval Management": DEMO / "mdm_requests.csv",
}

LOG_SOURCES = {
    "Team History": RAW / "approval_logs.csv",
    "Request Form": FORM_DATA / "new_approval_logs.csv",
    "Approval Management": DEMO / "approval_logs.csv",
}


# ============================================================
# PAGE STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* Main page */

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

    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3 {
        color: #253249 !important;
    }

    [data-testid="stMain"] p,
    [data-testid="stMain"] label {
        color: #344158;
    }

    /* Do not add sidebar logos here.
       The main app.py controls LivesFlow branding. */

    /* Metrics */

    [data-testid="stMetric"] {
        background: transparent !important;
        border: 1px solid #dce4ef !important;
        border-radius: 13px !important;
        padding: 15px !important;
        box-shadow: none !important;
    }

    [data-testid="stMetricLabel"] p {
        color: #66758c !important;
        font-size: 13px !important;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        color: #253249 !important;
        font-size: 27px !important;
    }

    /* Containers */

    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-color: #dce4ef !important;
        border-radius: 13px !important;
    }

    /* Tabs */

    [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid #dce4ef !important;
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

    /* Inputs */

    [data-baseweb="select"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: rgba(255, 255, 255, 0.45) !important;
        color: #253249 !important;
        border-color: #dce4ef !important;
        border-radius: 9px !important;
    }

    /* Transparent tables */

    .lf-table-wrap {
        width: 100%;
        overflow-x: auto;
        background: transparent !important;
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
        color: #253249;
        padding: 12px 13px;
        border-bottom: 1px solid #e2e8f1;
    }

    .lf-table tr:last-child td {
        border-bottom: none;
    }

    .lf-table tr:hover td {
        background: rgba(56, 111, 229, 0.04) !important;
    }

    /* Sections */

    .lf-section {
        color: #253249;
        font-weight: 700;
        font-size: 17px;
        margin: 20px 0 6px;
    }

    .lf-subtitle {
        color: #718096;
        font-size: 13px;
        margin-bottom: 12px;
    }

    /* Primary buttons */

    [data-testid="stBaseButton-primary"] {
        background: #386fe5 !important;
        border: none !important;
        color: #ffffff !important;
        border-radius: 9px !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def normalize(value):
    value = clean(value).casefold()
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    return " ".join(value.split())


def now():
    return datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")


def read_csv(path, columns=None):
    if not path.exists():
        return pd.DataFrame(columns=columns or [])

    df = pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
    )

    for column in columns or []:
        if column not in df.columns:
            df[column] = ""

    return df


def section(title, subtitle=""):
    st.markdown(
        f'<div class="lf-section">{escape(title)}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(
            f'<div class="lf-subtitle">{escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def show_table(df, limit=150):
    if df.empty:
        st.info("No records found.")
        return

    view = df.head(limit).fillna("")

    headers = "".join(
        f"<th>{escape(str(column))}</th>"
        for column in view.columns
    )

    rows = []

    for record in view.itertuples(index=False, name=None):
        cells = "".join(
            f"<td>{escape(str(value))}</td>"
            for value in record
        )

        rows.append(f"<tr>{cells}</tr>")

    html = (
        '<div class="lf-table-wrap">'
        '<table class="lf-table">'
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )

    if len(df) > limit:
        st.caption(
            f"Showing the first {limit} of {len(df):,} records."
        )


def details_table(pairs):
    return pd.DataFrame(
        pairs,
        columns=["Field", "Details"],
    )


# ============================================================
# REQUEST DATA CONNECTION
# ============================================================

def load_all_requests():
    """
    Read request data from the three sources.

    Priority:
    1. Original team history
    2. Request Form
    3. Approval Management

    Approval Management has the highest priority because
    its request file contains approval-status updates.

    A source collision is flagged separately.
    """

    frames = []

    for source, path in REQUEST_SOURCES.items():
        df = read_csv(
            path,
            REQUEST_COLUMNS,
        )

        if df.empty:
            continue

        df = df.copy()
        df["source"] = source

        frames.append(df)

    if not frames:
        return pd.DataFrame(
            columns=REQUEST_COLUMNS + ["source"]
        )

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    combined = combined[
        combined["request_id"].astype(str).str.strip() != ""
    ].copy()

    combined = combined.drop_duplicates(
        subset="request_id",
        keep="last",
    )

    return combined.reset_index(drop=True)


def load_all_logs():
    frames = []

    for source, path in LOG_SOURCES.items():
        df = read_csv(
            path,
            LOG_COLUMNS,
        )

        if df.empty:
            continue

        df = df.copy()
        df["source"] = source

        frames.append(df)

    if not frames:
        return pd.DataFrame(
            columns=LOG_COLUMNS + ["source"]
        )

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    # Event IDs may be generated independently by
    # different prototypes, so do not deduplicate
    # using event_id alone.
    return combined.drop_duplicates(
        subset=[
            "request_id",
            "event_time",
            "actor",
            "actor_role",
            "action",
            "comments",
        ],
        keep="last",
    ).reset_index(drop=True)


def load_payloads():
    path = FORM_DATA / "new_payloads.csv"

    df = read_csv(
        path,
        ["request_id", "payload"],
    )

    return df.drop_duplicates(
        subset="request_id",
        keep="last",
    )


def get_payload(request_id, payloads):
    matched = payloads[
        payloads["request_id"] == request_id
    ]

    if matched.empty:
        return {}

    try:
        payload = json.loads(
            matched.iloc[-1]["payload"]
        )

        if isinstance(payload, dict):
            return payload

    except (ValueError, TypeError):
        pass

    return {}


def get_request_logs(logs, request_id):
    matched = logs[
        logs["request_id"] == request_id
    ].copy()

    if "event_time" in matched.columns:
        matched = matched.sort_values(
            "event_time",
            kind="stable",
        )

    return matched


def get_source_collisions():
    """
    Identify IDs stored in both demo systems.

    Matching IDs do not prove that they represent
    the same request, so display a warning.
    """

    form = read_csv(
        FORM_DATA / "new_requests.csv",
        REQUEST_COLUMNS,
    )

    approval = read_csv(
        DEMO / "mdm_requests.csv",
        REQUEST_COLUMNS,
    )

    if form.empty or approval.empty:
        return set()

    return set(form["request_id"]) & set(
        approval["request_id"]
    )


# ============================================================
# SQLITE — MOCK HANDOFF HISTORY
# ============================================================

def db_connection():
    PROCESSED.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(
        DATABASE,
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
            """
            SELECT *
            FROM handoffs
            ORDER BY created_at DESC
            """,
            conn,
        )


def load_resolutions():
    with db_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT *
            FROM resolutions
            ORDER BY created_at DESC
            """,
            conn,
        )


# ============================================================
# UPDATE THE CORRECT APPROVAL DATA
# ============================================================

def update_demo_request(
    path,
    request_id,
    status,
    step,
    message,
):
    """
    Update a request inside a demo CSV.

    Do not create new records in unrelated stores.
    """

    if not path.exists():
        return False

    df = read_csv(
        path,
        REQUEST_COLUMNS,
    )

    mask = df["request_id"] == request_id

    if not mask.any():
        return False

    df.loc[mask, "status"] = status
    df.loc[mask, "current_step"] = step

    old_notes = clean(
        df.loc[mask, "notes"].iloc[-1]
    )

    if message not in old_notes:
        new_notes = (
            f"{old_notes} | {message}"
            if old_notes else message
        )

        df.loc[mask, "notes"] = new_notes

    df.to_csv(
        path,
        index=False,
    )

    return True


def add_demo_log(
    path,
    request_id,
    reviewer,
    action,
    comments,
):
    """
    Append a final-review event to a demo approval log.

    The existing events are never changed.
    """

    df = read_csv(
        path,
        LOG_COLUMNS,
    )

    already_exists = df[
        (df["request_id"] == request_id)
        & (df["action"] == action)
    ]

    if not already_exists.empty:
        return

    event = {
        "event_id": (
            f"MDM-{request_id}-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        ),
        "request_id": request_id,
        "event_time": now(),
        "actor": reviewer,
        "actor_role": "MDM Analyst",
        "action": action,
        "comments": comments,
    }

    updated = pd.concat(
        [df, pd.DataFrame([event])],
        ignore_index=True,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    updated.to_csv(
        path,
        index=False,
    )


def sync_final_decision(
    record,
    status,
    step,
    reviewer,
    action,
    message,
):
    """
    Update the demo store that owns the request.

    If an ID appears in both demo stores, do not
    automatically write to both: the ID may have been
    generated independently by two separate prototypes.
    """

    request_id = clean(record["request_id"])
    source = clean(record["source"])

    if source == "Request Form":
        request_path = FORM_DATA / "new_requests.csv"
        log_path = FORM_DATA / "new_approval_logs.csv"

    elif source == "Approval Management":
        request_path = DEMO / "mdm_requests.csv"
        log_path = DEMO / "approval_logs.csv"

    else:
        # Original team history remains read-only.
        return True

    changed = update_demo_request(
        request_path,
        request_id,
        status,
        step,
        message,
    )

    if changed:
        add_demo_log(
            log_path,
            request_id,
            reviewer,
            action,
            message,
        )

    return changed


# ============================================================
# VALIDATION
# ============================================================

def validate_request(record):
    required = {
        "Request ID": "request_id",
        "Record Type": "request_type",
        "Record Name": "record_name",
        "Country": "country",
        "Business Entity": "entity",
    }

    results = []

    for label, column in required.items():
        value = clean(
            record.get(column, "")
        )

        results.append({
            "Validation": label,
            "Result": (
                "Complete" if value else "Missing"
            ),
        })

    record_type = clean(
        record.get("request_type", "")
    )

    results.append({
        "Validation": "Supported Record Type",
        "Result": (
            "Complete"
            if record_type in MASTER_CONFIG
            else "Unsupported"
        ),
    })

    result = pd.DataFrame(results)

    valid = result["Result"].eq(
        "Complete"
    ).all()

    return valid, result


# ============================================================
# AUTOMATIC DUPLICATE CHECK
# ============================================================

def find_duplicates(record, payload, handoffs):
    """
    Screen existing masters and completed mock handoffs.

    Also checks registration numbers when available.

    This is not a final legal-identity determination.
    """

    kind = clean(
        record.get("request_type", "")
    )

    if kind not in MASTER_CONFIG:
        return pd.DataFrame()

    config = MASTER_CONFIG[kind]

    master_file = config["file"]
    id_col = config["id"]
    name_col = config["name"]

    original = read_csv(
        RAW / master_file
    )

    form_master = read_csv(
        FORM_DATA / f"new_{master_file}"
    )

    masters = pd.concat(
        [original, form_master],
        ignore_index=True,
    )

    target_name = normalize(
        record.get("record_name", "")
    )

    target_registration = clean(
        payload.get(
            "registration_no",
            payload.get("registration_number", ""),
        )
    ).upper()

    candidates = []

    if name_col in masters.columns:
        for _, existing in masters.iterrows():
            existing_name = clean(
                existing.get(name_col, "")
            )

            if not existing_name:
                continue

            name_score = SequenceMatcher(
                None,
                target_name,
                normalize(existing_name),
            ).ratio() if target_name else 0

            existing_registration = clean(
                existing.get(
                    "registration_no",
                    existing.get("registration_number", ""),
                )
            ).upper()

            same_registration = (
                bool(target_registration)
                and bool(existing_registration)
                and target_registration == existing_registration
            )

            if same_registration or name_score >= 0.80:
                if same_registration:
                    reason = "Same registration number"
                    score_text = "Exact identifier"
                elif name_score == 1:
                    reason = "Exact name"
                    score_text = "100%"
                else:
                    reason = "Similar name"
                    score_text = f"{name_score * 100:.0f}%"

                candidates.append({
                    "Source": "Master Data Directory",
                    "Existing Code": clean(
                        existing.get(id_col, "")
                    ),
                    "Existing Name": existing_name,
                    "Reason": reason,
                    "Similarity": score_text,
                })

    if not handoffs.empty and target_name:
        previous = handoffs[
            handoffs["master_type"] == kind
        ]

        for _, existing in previous.iterrows():
            similarity = SequenceMatcher(
                None,
                target_name,
                normalize(
                    existing["record_name"]
                ),
            ).ratio()

            if similarity >= 0.80:
                candidates.append({
                    "Source": "Previous Mock Handoff",
                    "Existing Code": existing["mock_sap_code"],
                    "Existing Name": existing["record_name"],
                    "Reason": "Previously processed",
                    "Similarity": f"{similarity * 100:.0f}%",
                })

    flagged = clean(
        record.get("candidate_existing_id", "")
    )

    if flagged:
        candidates.append({
            "Source": "Request Submission",
            "Existing Code": flagged,
            "Existing Name": "Flagged existing record",
            "Reason": "Previously flagged",
            "Similarity": "—",
        })

    if not candidates:
        return pd.DataFrame(
            columns=[
                "Source",
                "Existing Code",
                "Existing Name",
                "Reason",
                "Similarity",
            ]
        )

    return pd.DataFrame(
        candidates
    ).drop_duplicates()


# ============================================================
# SAVE THE FINAL DECISION
# ============================================================

def save_handoff(
    record,
    reviewer,
    note,
    duplicate_override,
):
    request_id = clean(
        record["request_id"]
    )

    record_type = clean(
        record["request_type"]
    )

    prefix = MASTER_CONFIG[
        record_type
    ]["prefix"]

    mock_code = (
        f"MOCK-{prefix}-{request_id}"
    )

    request_payload = {
        "requestId": request_id,
        "recordType": record_type,
        "recordName": clean(record["record_name"]),
        "country": clean(record.get("country", "")),
        "entity": clean(record.get("entity", "")),
        "reviewedBy": reviewer,
        "duplicateOverride": duplicate_override,
    }

    simulated_response = {
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
                    record_type,
                    clean(record["record_name"]),
                    mock_code,
                    "Simulated handoff complete",
                    now(),
                    reviewer,
                    note,
                    json.dumps(request_payload),
                    json.dumps(simulated_response),
                ),
            )

    except sqlite3.IntegrityError:
        return False

    sync_final_decision(
        record=record,
        status=COMPLETED_STATUS,
        step="Finalized",
        reviewer=reviewer,
        action="SAP handoff complete",
        message=(
            f"Simulated SAP B1 handoff completed. "
            f"Mock reference: {mock_code}. {note}"
        ),
    )

    return True


def save_resolution(
    record,
    decision,
    existing_code,
    reviewer,
    note,
):
    request_id = clean(
        record["request_id"]
    )

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
                    now(),
                ),
            )

    except sqlite3.IntegrityError:
        return False

    if decision == "Use Existing Record":
        status = COMPLETED_STATUS
        step = "Finalized"
        action = "Resolved using existing record"

        message = (
            f"Existing record {existing_code} selected. "
            f"{note}"
        )

    else:
        status = RETURNED_STATUS
        step = "Correction requested"
        action = "Changes requested"
        message = note

    sync_final_decision(
        record=record,
        status=status,
        step=step,
        reviewer=reviewer,
        action=action,
        message=message,
    )

    return True


# ============================================================
# LOAD CONNECTED INFORMATION
# ============================================================

requests = load_all_requests()
approval_logs = load_all_logs()
payloads = load_payloads()

handoffs = load_handoffs()
resolutions = load_resolutions()

collisions = get_source_collisions()

if requests.empty:
    approved = requests.copy()
else:
    approved = requests[
        requests["status"].map(
            lambda value: clean(value).casefold()
        ) == APPROVED_STATUS.casefold()
    ].copy()

processed_ids = set(
    handoffs["request_id"].astype(str)
)

processed_ids.update(
    resolutions["request_id"].astype(str)
)

queue = approved[
    ~approved["request_id"].astype(str).isin(
        processed_ids
    )
].copy()


# ============================================================
# PAGE HEADER
# ============================================================

st.title("Master Data Management")

st.caption(
    "Final master data validation after approval, "
    "before simulated SAP Business One handoff."
)

st.caption(
    "Integration Status: Connected Demo Data | "
    "SAP B1 Simulation"
)

if collisions:
    st.warning(
        "Some request IDs appear in both the Request Form "
        "and Approval Management demo files. "
        "Approval Management takes priority for display. "
        "Verify that these IDs refer to the same requests "
        "before processing them."
    )

if not DEMO.exists():
    st.info(
        "Approval Management demo data has not been found. "
        "The page will still display any eligible requests "
        "from the available sources."
    )

# ============================================================
# KPI CARDS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Approved Requests",
    len(approved),
)

c2.metric(
    "Pending Final Review",
    len(queue),
)

c3.metric(
    "Mock Handoffs",
    len(handoffs),
)

c4.metric(
    "Review Decisions",
    len(resolutions),
)

st.write("")


# ============================================================
# MAIN TABS
# ============================================================

tab_queue, tab_directory, tab_log = st.tabs([
    "SAP Handoff Queue",
    "Master Data Directory",
    "Handoff Log",
])


# ============================================================
# TAB 1 — SAP HANDOFF QUEUE
# ============================================================

with tab_queue:

    section(
        "Ready for SAP Review",
        "Approved requests requiring final master data validation.",
    )

    if queue.empty:
        st.info(
            "There are no requests waiting for final review. "
            "Once a request is fully approved, it should "
            "appear here with the status "
            "'Approved - SAP pending'."
        )

    else:
        filter1, filter2 = st.columns(2)

        with filter1:
            selected_type = st.selectbox(
                "Record Type",
                ["All Types"]
                + sorted(
                    queue["request_type"]
                    .dropna()
                    .unique()
                    .tolist()
                ),
            )

        with filter2:
            selected_source = st.selectbox(
                "Request Source",
                [
                    "All Sources",
                    "Team History",
                    "Request Form",
                    "Approval Management",
                ],
            )

        filtered = queue.copy()

        if selected_type != "All Types":
            filtered = filtered[
                filtered["request_type"]
                == selected_type
            ]

        if selected_source != "All Sources":
            filtered = filtered[
                filtered["source"]
                == selected_source
            ]

        if filtered.empty:
            st.info(
                "No requests match these filters."
            )

        else:
            display_columns = [
                "request_id",
                "request_type",
                "record_name",
                "country",
                "entity",
                "source",
            ]

            show_table(
                filtered[
                    display_columns
                ].rename(
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
                filtered["request_id"]
                == selected_id
            ].iloc[0]

            payload = get_payload(
                selected_id,
                payloads,
            )

            with st.container(border=True):

                section(
                    "Request Details",
                    "Review the information submitted for this record.",
                )

                show_table(
                    details_table([
                        ("Request ID", selected_id),
                        (
                            "Record Type",
                            record["request_type"],
                        ),
                        (
                            "Record Name",
                            record["record_name"],
                        ),
                        (
                            "Country",
                            record["country"],
                        ),
                        (
                            "Business Entity",
                            record["entity"],
                        ),
                        (
                            "Submitted By",
                            record["requestor"],
                        ),
                        (
                            "Approval Status",
                            record["status"],
                        ),
                        (
                            "Data Source",
                            record["source"],
                        ),
                    ])
                )

                if payload:
                    with st.expander(
                        "Additional Submitted Information"
                    ):
                        extra = []

                        for key, value in payload.items():
                            extra.append({
                                "Field": key.replace(
                                    "_", " "
                                ).title(),
                                "Value": str(value),
                            })

                        show_table(
                            pd.DataFrame(extra)
                        )

                # --------------------------------------------
                # APPROVAL HISTORY
                # --------------------------------------------

                section(
                    "Approval History",
                    "Recorded actions from the connected approval systems.",
                )

                events = get_request_logs(
                    approval_logs,
                    selected_id,
                )

                if events.empty:
                    st.warning(
                        "No approval events were found "
                        "for this request."
                    )

                else:
                    event_columns = [
                        "event_time",
                        "actor",
                        "actor_role",
                        "action",
                        "comments",
                        "source",
                    ]

                    show_table(
                        events[
                            event_columns
                        ].rename(
                            columns={
                                "event_time": "Date & Time",
                                "actor": "Performed By",
                                "actor_role": "Role",
                                "action": "Action",
                                "comments": "Comments",
                                "source": "Source",
                            }
                        )
                    )

                # --------------------------------------------
                # AUTOMATIC VALIDATION
                # --------------------------------------------

                section(
                    "Automatic Validation",
                    "Check whether the required information is present.",
                )

                valid, validation_results = (
                    validate_request(record)
                )

                show_table(
                    validation_results
                )

                if valid:
                    st.success(
                        "All basic required fields are complete."
                    )
                else:
                    st.error(
                        "Some required information is missing. "
                        "The request cannot proceed to "
                        "the mock SAP handoff."
                    )

                # --------------------------------------------
                # DUPLICATE SCREENING
                # --------------------------------------------

                section(
                    "Automatic Duplicate Check",
                    "Screen this request against existing master data.",
                )

                duplicates = find_duplicates(
                    record,
                    payload,
                    handoffs,
                )

                if duplicates.empty:
                    st.success(
                        "No potential duplicates found "
                        "in the available master records."
                    )

                else:
                    st.warning(
                        f"{len(duplicates)} possible "
                        "match(es) detected. "
                        "Review the records before continuing."
                    )

                    show_table(duplicates)

                # --------------------------------------------
                # FINAL REVIEW
                # --------------------------------------------

                section(
                    "Final Review",
                    "Complete the MDM quality check and record your decision.",
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

                # Prevent ambiguous IDs from being processed
                # without first reconciling the sources.
                conflicting_id = selected_id in collisions

                if conflicting_id:
                    st.error(
                        "This request ID exists in both demo systems. "
                        "Reconcile the two records before performing "
                        "the final handoff."
                    )

                with st.form(
                    f"mdm_final_review_{selected_id}"
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
                            "Explain the validation results "
                            "and the reason for your decision."
                        ),
                    )

                    confirmed = st.checkbox(
                        "I have reviewed the request details, "
                        "approval history and duplicate results."
                    )

                    submitted = st.form_submit_button(
                        "Save Review Decision",
                        type="primary",
                        disabled=conflicting_id,
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
                            "Please confirm that you completed "
                            "the review."
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
                            "The request is missing required "
                            "information. Please send it "
                            "back for correction."
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

    section(
        "Master Data Directory",
        "Search existing customer, item, vendor and cost-centre data.",
    )

    master_type = st.selectbox(
        "Record Type",
        list(MASTER_CONFIG),
        key="master_directory_type",
    )

    master_file = (
        MASTER_CONFIG[master_type]["file"]
    )

    original_master = read_csv(
        RAW / master_file
    )

    new_master = read_csv(
        FORM_DATA / f"new_{master_file}"
    )

    if not original_master.empty:
        original_master["Source"] = (
            "Team Master Data"
        )

    if not new_master.empty:
        new_master["Source"] = (
            "Request Form Demo"
        )

    directory = pd.concat(
        [
            original_master,
            new_master,
        ],
        ignore_index=True,
    )

    search = st.text_input(
        "Search Master Records",
        placeholder="Search by name, code or other information",
    )

    if search.strip() and not directory.empty:

        matches = directory.astype(str).apply(
            lambda col: col.str.contains(
                search.strip(),
                case=False,
                regex=False,
            )
        ).any(axis=1)

        directory = directory[matches]

    show_table(directory)

    st.caption(
        "This directory is read-only. "
        "The SAP handoff page does not change "
        "the original team master CSV files."
    )


# ============================================================
# TAB 3 — HANDOFF LOG
# ============================================================

with tab_log:

    section(
        "Handoff Log",
        "Review completed simulated SAP handoffs and MDM decisions.",
    )

    handoff_tab, decision_tab = st.tabs([
        "Completed Handoffs",
        "Review Decisions",
    ])

    with handoff_tab:

        if handoffs.empty:
            st.info(
                "No simulated SAP handoffs "
                "have been recorded yet."
            )

        else:
            show_table(
                handoffs[
                    [
                        "request_id",
                        "master_type",
                        "record_name",
                        "mock_sap_code",
                        "state",
                        "created_at",
                        "reviewed_by",
                    ]
                ].rename(
                    columns={
                        "request_id": "Request ID",
                        "master_type": "Record Type",
                        "record_name": "Record Name",
                        "mock_sap_code": "Mock SAP Reference",
                        "state": "Status",
                        "created_at": "Completed At (UTC)",
                        "reviewed_by": "Reviewed By",
                    }
                )
            )

            selected_handoff = st.selectbox(
                "View Handoff",
                handoffs[
                    "request_id"
                ].tolist(),
            )

            selected = handoffs[
                handoffs["request_id"]
                == selected_handoff
            ].iloc[0]

            with st.container(border=True):

                section(
                    "SAP Handoff Summary"
                )

                st.success(
                    "Mock handoff completed successfully. "
                    "No live SAP Business One record was created."
                )

                show_table(
                    details_table([
                        (
                            "Request ID",
                            selected["request_id"],
                        ),
                        (
                            "Record Name",
                            selected["record_name"],
                        ),
                        (
                            "Record Type",
                            selected["master_type"],
                        ),
                        (
                            "Mock SAP Reference",
                            selected["mock_sap_code"],
                        ),
                        (
                            "Status",
                            selected["state"],
                        ),
                        (
                            "Reviewed By",
                            selected["reviewed_by"],
                        ),
                        (
                            "Review Notes",
                            selected["review_note"],
                        ),
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

    with decision_tab:

        if resolutions.empty:
            st.info(
                "No review decisions recorded yet."
            )

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
    "LivesFlow Competition Prototype | "
)


from pathlib import Path
import streamlit as st


# ============================================================
# LIVESFLOW — MAIN APPLICATION
# ============================================================

st.set_page_config(
    page_title="LivesFlow | Master Data & Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       MAIN DASHBOARD
    ====================================================== */

    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background-color: #f5f7fb !important;
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


    /* ======================================================
       NAVY SIDEBAR
    ====================================================== */

    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"] {
        background-color: #14243b !important;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #263b56 !important;
    }


    /* ======================================================
       LIVESFLOW LOGO AT THE TOP OF NAVIGATION
    ====================================================== */

    [data-testid="stSidebarNav"] {
        position: relative !important;
        padding-top: 118px !important;
    }

    /* "Lives" — white */

    [data-testid="stSidebarNav"]::before {
        content: "Lives";
        position: absolute;
        top: 26px;
        left: 28px;

        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;

        font-size: 31px;
        font-weight: 800;
        letter-spacing: -1.3px;
        line-height: 1.1;
        color: #f6f8fd !important;
        pointer-events: none;
    }

    /* "Flow" — pastel blue */

    [data-testid="stSidebarNav"]::after {
        content: "Flow";
        position: absolute;
        top: 26px;
        left: 104px;

        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;

        font-size: 31px;
        font-weight: 800;
        letter-spacing: -1.3px;
        line-height: 1.1;
        color: #77a9ff !important;
        pointer-events: none;
    }

    /* Subtitle */

    [data-testid="stSidebarNav"] > ul::before {
        content: "MASTER DATA & ANALYTICS";
        display: block;

        font-size: 10px;
        font-weight: 650;
        letter-spacing: 1.4px;
        color: #a9b8ce !important;

        padding: 0 14px;
        margin-top: -39px;
        margin-bottom: 48px;
    }


    /* ======================================================
       SIDEBAR NAVIGATION
    ====================================================== */

    [data-testid="stSidebarNav"] a {
        border-radius: 10px !important;
        margin: 4px 12px !important;
        transition: background-color 0.2s ease;
    }

    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a *,
    [data-testid="stSidebarNav"] a svg {
        color: #e8eef8 !important;
        fill: #e8eef8 !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        background-color: #263b57 !important;
    }

    [data-testid="stSidebarNav"]
    a[aria-current="page"],
    [data-testid="stSidebarNav"]
    a[aria-current="true"] {
        background-color: #304665 !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebarNav"]
    a[aria-current="page"] *,
    [data-testid="stSidebarNav"]
    a[aria-current="true"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
        font-weight: 650 !important;
    }


    /* ======================================================
       REMOVE DUPLICATE DECORATIVE SIDEBAR SECTIONS

       Hide old branding and page descriptions that are
       rendered below the navigation by individual pages.

       Do not hide functional inputs or filters.
    ====================================================== */

    [data-testid="stSidebar"]
    [data-testid="stMarkdownContainer"]:has(.livesflow-logo) {
        display: none !important;
    }

    [data-testid="stSidebar"]
    [data-testid="stMarkdownContainer"]:has(.livesflow-subtitle) {
        display: none !important;
    }

    /* Hide old sidebar logo markup from previous designs */

    [data-testid="stSidebar"]
    [data-testid="stMarkdownContainer"]:has(h2)
    {
        /* Other headings remain visible by default. */
    }

    /* Ensure sidebar text and functional controls are readable */

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] button {
        color: #e8eef8 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #30435e !important;
    }


    /* ======================================================
       MOBILE
    ====================================================== */

    @media (max-width: 768px) {

        [data-testid="stSidebarNav"] {
            padding-top: 108px !important;
        }

        [data-testid="stSidebarNav"]::before,
        [data-testid="stSidebarNav"]::after {
            font-size: 27px;
        }

        [data-testid="stSidebarNav"]::after {
            left: 94px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PAGE NAVIGATION
# ============================================================

pages = []


# Regional Analytics
regional_page = ROOT / "pages" / "regional_analytics.py"

if regional_page.exists():
    pages.append(
        st.Page(
            "pages/regional_analytics.py",
            title="Regional Analytics",
            icon=":material/monitoring:",
            default=True,
        )
    )


# Demand Exception Report
exception_page = ROOT / "pages" / "exception_dashboard.py"

if exception_page.exists():
    pages.append(
        st.Page(
            "pages/exception_dashboard.py",
            title="Demand Exception Report",
            icon=":material/query_stats:",
        )
    )


# Master Data Records
master_page = ROOT / "pages" / "master_data_records.py"

if master_page.exists():
    pages.append(
        st.Page(
            "pages/master_data_records.py",
            title="Master Data Records",
            icon=":material/database:",
        )
    )


# ============================================================
# START NAVIGATION
# ============================================================

if pages:
    navigation = st.navigation(
        pages,
        position="sidebar",
    )
    navigation.run()

else:
    st.error(
        "No dashboard pages found. "
        "Please check the pages folder."
    )

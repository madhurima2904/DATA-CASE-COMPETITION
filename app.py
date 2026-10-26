
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

    /* Main dashboard background */

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
       SIDEBAR BACKGROUND
    ====================================================== */

    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"] {
        background-color: #14243b !important;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #263b56 !important;
    }


    /* ======================================================
       LIVESFLOW BRANDING ABOVE NAVIGATION
    ====================================================== */

    [data-testid="stSidebarNav"] {
        position: relative !important;
        padding-top: 118px !important;
    }

    /* Lives — white */

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

    /* Flow — pastel blue */

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
       NAVIGATION LINKS
    ====================================================== */

    [data-testid="stSidebarNav"] a {
        border-radius: 10px !important;
        margin: 4px 12px !important;
        transition: background-color 0.2s ease;
    }

    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a span,
    [data-testid="stSidebarNav"] a p,
    [data-testid="stSidebarNav"] a div,
    [data-testid="stSidebarNav"] a svg {
        color: #e8eef8 !important;
        fill: #e8eef8 !important;
    }

    /* Hover */

    [data-testid="stSidebarNav"] a:hover {
        background-color: #263b57 !important;
    }

    /* Selected page */

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

    /* Sidebar text */

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] button {
        color: #e8eef8 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #30435e !important;
    }


    /* ======================================================
       NARROW SCREENS
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


# ------------------------------------------------------------
# 1. REGIONAL ANALYTICS
# ------------------------------------------------------------

if (ROOT / "pages" / "regional_analytics.py").exists():

    pages.append(
        st.Page(
            "pages/regional_analytics.py",
            title="Regional Analytics",
            icon=":material/monitoring:",
            default=True,
        )
    )


# ------------------------------------------------------------
# 2. DEMAND FORECASTING
# ------------------------------------------------------------

if (ROOT / "pages" / "demand_forecast.py").exists():

    pages.append(
        st.Page(
            "pages/demand_forecast.py",
            title="Demand Forecasting",
            icon=":material/trending_up:",
        )
    )


# ------------------------------------------------------------
# 3. DEMAND EXCEPTION REPORT
# ------------------------------------------------------------

if (ROOT / "pages" / "exception_dashboard.py").exists():

    pages.append(
        st.Page(
            "pages/exception_dashboard.py",
            title="Demand Exception Report",
            icon=":material/query_stats:",
        )
    )


# ------------------------------------------------------------
# 4. MASTER DATA RECORDS
# ------------------------------------------------------------

if (ROOT / "pages" / "master_data_records.py").exists():

    pages.append(
        st.Page(
            "pages/master_data_records.py",
            title="Master Data Records",
            icon=":material/database:",
        )
    )


# ============================================================
# START DASHBOARD
# ============================================================

if pages:

    navigation = st.navigation(
        pages,
        position="sidebar",
    )

    navigation.run()

else:

    st.error(
        "No dashboard pages were found. "
        "Please check your pages folder."
    )


from pathlib import Path
import streamlit as st


# ============================================================
# LIVESFLOW — MAIN DASHBOARD
# ============================================================

st.set_page_config(
    page_title="LivesFlow | Master Data & Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent


# ============================================================
# GLOBAL STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* --------------------------------------------------------
       MAIN APPLICATION
    -------------------------------------------------------- */

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


    /* --------------------------------------------------------
       NAVY SIDEBAR
    -------------------------------------------------------- */

    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"] {
        background-color: #14243b !important;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #263b56 !important;
    }


    /* --------------------------------------------------------
       LIVESFLOW LOGO ABOVE NAVIGATION
       
       The navigation is rendered by Streamlit before normal
       sidebar elements. We display the branding in the
       navigation's top area instead.
    -------------------------------------------------------- */

    [data-testid="stSidebarNav"] {
        position: relative !important;
        padding-top: 118px !important;
    }

    /* White Lives + blue Flow through two separate layers */

    [data-testid="stSidebarNav"]::before {
        content: "Lives";
        position: absolute;
        top: 27px;
        left: 28px;

        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;

        font-size: 32px;
        font-weight: 800;
        letter-spacing: -1.3px;
        line-height: 1.1;
        color: #f6f8fd !important;
    }

    [data-testid="stSidebarNav"]::after {
        content: "Flow";
        position: absolute;
        top: 27px;
        left: 105px;

        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;

        font-size: 32px;
        font-weight: 800;
        letter-spacing: -1.3px;
        line-height: 1.1;
        color: #77a9ff !important;
    }

    /* Subtitle placed underneath the logo */

    [data-testid="stSidebarNav"] > ul::before {
        content: "MASTER DATA & ANALYTICS";
        display: block;

        color: #a9b8ce !important;
        font-size: 10px;
        font-weight: 650;
        letter-spacing: 1.7px;

        margin-top: -44px;
        margin-left: 28px;
        margin-bottom: 45px;
    }


    /* --------------------------------------------------------
       SIDEBAR NAVIGATION ITEMS
    -------------------------------------------------------- */

    [data-testid="stSidebarNav"] a {
        border-radius: 10px !important;
        margin: 4px 14px !important;
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

    /* Material icons */

    [data-testid="stSidebarNav"] a
    .material-symbols-rounded,
    [data-testid="stSidebarNav"] a
    .material-icons {
        color: #e8eef8 !important;
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

    /* Hover state */

    [data-testid="stSidebarNav"] a:hover {
        background-color: #263b57 !important;
    }

    /* General sidebar text */

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] button {
        color: #e8eef8 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #30435e !important;
    }


    /* --------------------------------------------------------
       MOBILE / NARROW SIDEBAR
    -------------------------------------------------------- */

    @media (max-width: 768px) {

        [data-testid="stSidebarNav"] {
            padding-top: 105px !important;
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
if (ROOT / "pages" / "regional_analytics.py").exists():

    pages.append(
        st.Page(
            "pages/regional_analytics.py",
            title="Regional Analytics",
            icon=":material/monitoring:",
            default=True,
        )
    )


# Demand Exception Report
if (ROOT / "pages" / "exception_dashboard.py").exists():

    pages.append(
        st.Page(
            "pages/exception_dashboard.py",
            title="Demand Exception Report",
            icon=":material/query_stats:",
        )
    )


# Master Data Records
if (ROOT / "pages" / "master_data_records.py").exists():

    pages.append(
        st.Page(
            "pages/master_data_records.py",
            title="Master Data Records",
            icon=":material/database:",
        )
    )


# ============================================================
# RUN DASHBOARD
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


from pathlib import Path
import streamlit as st

# =====================================================
# LIVESFLOW — MAIN APPLICATION
# =====================================================

st.set_page_config(
    page_title="LivesFlow | Operations Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent

# =====================================================
# PAGE NAVIGATION
# =====================================================

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

# =====================================================
# RUN APPLICATION
# =====================================================

if pages:
    navigation = st.navigation(pages)
    navigation.run()
else:
    st.error("No dashboard pages found in the pages folder.")

import streamlit as st

st.set_page_config(
    page_title='LivesFlow | Regional Analytics',
    layout='wide',
    initial_sidebar_state='expanded',
)

page = st.navigation([
    st.Page('pages/regional_analytics.py', title='Regional Analytics', icon=':material/monitoring:', default=True)
])
page.run()
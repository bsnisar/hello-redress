import streamlit as st

pages = {
    "Search" : [
        st.Page("s_search_cons.py", title="Search with magic"),
    ]
}

pg = st.navigation(pages)
pg.run()
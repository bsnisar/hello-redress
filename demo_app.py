import streamlit as st

pages = {
    "Search" : [
        st.Page("s_search.py", title="Semantic Search"),
        st.Page("s_search_cons.py", title="Search with magic"),
        st.Page("v_search.py", title="Visual search"),
    ]
}

pg = st.navigation(pages)
pg.run()
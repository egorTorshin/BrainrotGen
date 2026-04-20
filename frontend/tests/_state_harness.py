import streamlit as st
from state import init_state, current_page
init_state()
st.write(current_page())
st.session_state['page'] = 'generate'
st.write(current_page())

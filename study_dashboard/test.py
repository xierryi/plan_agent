import streamlit as st

# 初始化
if 'input_value' not in st.session_state:
    st.session_state.input_value = "1"

if

# 选择框变化时触发
option = st.text_input(
        "显示内容", 
        value=st.session_state.nput_value,
        disabled=True,
        key="isplay_input"
    )

if option != st.session_state.input_value:
    st.session_state.input_value = option
    st.rerun()

# 显示内容
input_placeholder = st.empty()
with input_placeholder.container():
    st.text_input(
        "显示内容", 
        value=st.session_state.input_value,
        disabled=True,
        key="display_input"
    )
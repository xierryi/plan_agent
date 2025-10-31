import streamlit as st

# 初始化
if 'main_value' not in st.session_state:
    st.session_state.main_value = "1"

st.title("双向更新演示")

# 方法1：通过表单和按钮更新
with st.form("update_form"):
    new_value = st.text_input("输入新值", value=st.session_state.main_value)
    update_btn = st.form_submit_button("通过按钮更新")
    
    st.write(f"表单中的当前值: {new_value}")

    if update_btn:
        st.session_state.main_value = new_value
        st.success("通过按钮更新成功！")
        st.rerun()

# 方法2：直接在主输入框中编辑
current_value = st.text_input(
    "主输入框（可直接编辑）", 
    value=st.session_state.main_value,
)

# 检测主输入框的变化并更新 session state
if current_value != st.session_state.main_value:
    st.session_state.main_value = current_value
    st.success("通过直接输入更新成功！")
    st.rerun()

# 显示当前状态
st.write(f"当前值: {st.session_state.main_value}")
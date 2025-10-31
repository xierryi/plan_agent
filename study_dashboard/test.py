import streamlit as st

# 初始化
if 'tasks' not in st.session_state:
    st.session_state.tasks = {}

st.title("双向更新演示")

# 回调函数 - 需要接收参数
def update_from_input(source_idx, target_idx):
    """从源输入框更新目标输入框"""
    source_key = f"form_input{source_idx}"
    target_key = f"form_input{target_idx}"
    
    # 更新目标输入框的值
    st.session_state[target_key] = st.session_state[source_key]
    st.session_state.tasks[target_key] = st.session_state[source_key]
    
    st.success(f"从输入框{source_idx}更新输入框{target_idx}成功！")

# 两个输入框都放在表单内
with st.form("main_form"):
    st.markdown("### 表单内的双向输入框")
    
    col1, col2 = st.columns(2)
    
    i = 1
    with col1:
        # 输入框1
        st.text_input(
            "输入框1", 
            value=st.session_state.tasks.get(f"form_input{i}", ""),
            key=f"form_input{i}"
        )
        # 输入框1的更新按钮 - 使用 lambda 传递参数
        st.form_submit_button(
            "通过输入框1更新", 
            on_click=lambda: update_from_input(1, 2)
        )

    i = 2
    with col2:
        # 输入框2
        st.text_input(
            "输入框2", 
            value=st.session_state.tasks.get(f"form_input{i}", ""),
            key=f"form_input{i}"
        )
        # 输入框2的更新按钮
        st.form_submit_button(
            "通过输入框2更新", 
            on_click=lambda: update_from_input(2, 1)
        )
    
    # 显示当前状态
    st.markdown("### 当前状态")
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        st.metric("输入框1", st.session_state.get("form_input1", "未设置"))
    
    with col_status2:
        st.metric("输入框2", st.session_state.get("form_input2", "未设置"))

# 显示 tasks 字典状态
st.markdown("### Tasks 字典状态")
st.write(st.session_state.tasks)
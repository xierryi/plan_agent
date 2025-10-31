import streamlit as st

# 初始化
if 'main_value' not in st.session_state:
    st.session_state.main_value = "1"
if 'form_input1' not in st.session_state:
    st.session_state.form_input1 = st.session_state.main_value
if 'form_input2' not in st.session_state:
    st.session_state.form_input2 = st.session_state.main_value

st.title("双向更新演示")

# 回调函数
def update_from_input1():
    """从输入框1更新所有值"""
    st.session_state.main_value = st.session_state.form_input1
    st.session_state.form_input2 = st.session_state.form_input1
    st.success("输入框1更新成功！")

def update_from_input2():
    """从输入框2更新所有值"""
    st.session_state.main_value = st.session_state.form_input2
    st.session_state.form_input1 = st.session_state.form_input2
    st.success("输入框2更新成功！")

def sync_all_values():
    """同步所有值到当前主值"""
    st.session_state.form_input1 = st.session_state.main_value
    st.session_state.form_input2 = st.session_state.main_value
    st.success("手动同步完成！")

# 两个输入框都放在表单内
with st.form("main_form"):
    st.markdown("### 表单内的双向输入框")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 输入框1
        st.text_input(
            "输入框1", 
            value=st.session_state.form_input1, 
            key="form_input1"
        )
        # 输入框1的更新按钮
        update_btn1 = st.form_submit_button(
            "通过输入框1更新", 
            on_click=update_from_input1
        )
    
    with col2:
        # 输入框2
        st.text_input(
            "输入框2", 
            value=st.session_state.form_input2, 
            key="form_input2"
        )
        # 输入框2的更新按钮
        update_btn2 = st.form_submit_button(
            "通过输入框2更新", 
            on_click=update_from_input2
        )
    
    # 通用同步按钮
    st.markdown("---")
    sync_btn = st.form_submit_button(
        "🔄 同步所有输入框", 
        on_click=sync_all_values
    )
    
    # 显示当前状态
    st.markdown("### 当前状态")
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        st.metric("主值", st.session_state.main_value)
    
    with col_status2:
        st.metric("输入框1", st.session_state.form_input1)
    
    with col_status3:
        st.metric("输入框2", st.session_state.form_input2)

# 表单外的控制面板
st.markdown("---")
with st.expander("控制面板"):
    col_control1, col_control2, col_control3 = st.columns(3)
    
    with col_control1:
        if st.button("🔄 从输入框1同步"):
            update_from_input1()
            st.rerun()
    
    with col_control2:
        if st.button("🔄 从输入框2同步"):
            update_from_input2()
            st.rerun()
    
    with col_control3:
        if st.button("🗑️ 重置所有"):
            st.session_state.main_value = "1"
            st.session_state.form_input1 = "1"
            st.session_state.form_input2 = "1"
            st.success("已重置！")
            st.rerun()
    
    # 实时检测和同步（备用机制）
    if (st.session_state.form_input1 != st.session_state.main_value and 
        st.session_state.form_input1 != ""):
        st.info("检测到输入框1变化，正在同步...")
        update_from_input1()
        st.rerun()
    
    if (st.session_state.form_input2 != st.session_state.main_value and 
        st.session_state.form_input2 != ""):
        st.info("检测到输入框2变化，正在同步...")
        update_from_input2()
        st.rerun()

# 调试信息
with st.expander("调试信息"):
    st.json({
        "main_value": st.session_state.main_value,
        "form_input1": st.session_state.form_input1,
        "form_input2": st.session_state.form_input2,
        "所有值一致": (
            st.session_state.main_value == st.session_state.form_input1 == st.session_state.form_input2
        )
    })
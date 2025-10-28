import streamlit as st
try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import json
    import time
    import numpy as np
    from data_manager import StudyDataManager
    from study_agent import StudyAgent
    from github_state_manager import github_state_manager
except ImportError as e:
    st.error(f"导入错误: {e}")
    st.info("请确保 requirements.txt 包含所有必要的依赖包")
    st.stop()
# 在导入部分修改
try:
    from github_manager import GitHubDataManager
    data_manager = GitHubDataManager()
except ImportError:
    from data_manager import StudyDataManager
    data_manager = StudyDataManager()

# 移除原有的 @st.cache_resource 装饰器

def check_time_conflicts(planned_tasks, date):
    """检查任务时间是否重叠"""
    conflicts = []
    time_ranges = []
    
    for task in planned_tasks:
        if 'planned_start_time' in task and 'planned_end_time' in task:
            try:
                start_time = datetime.strptime(task['planned_start_time'], '%H:%M').time()
                end_time = datetime.strptime(task['planned_end_time'], '%H:%M').time()
                
                start_dt = datetime.combine(date, start_time)
                end_dt = datetime.combine(date, end_time)
                
                # 处理跨天情况
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)
                
                time_ranges.append({
                    'task_name': task['task_name'],
                    'start': start_dt,
                    'end': end_dt
                })
            except ValueError:
                continue
    
    # 检查时间重叠
    for i in range(len(time_ranges)):
        for j in range(i + 1, len(time_ranges)):
            range1 = time_ranges[i]
            range2 = time_ranges[j]
            
            # 检查两个时间段是否重叠
            if (range1['start'] < range2['end'] and range1['end'] > range2['start']):
                conflict_msg = f"「{range1['task_name']}」和「{range2['task_name']}」时间重叠"
                conflicts.append(conflict_msg)
    
    return conflicts

def calculate_duration(start_time, end_time):
    """计算两个时间之间的时长（分钟）"""
    if start_time and end_time:
        duration = (end_time - start_time).total_seconds() / 60
        return max(0, int(duration))
    return 0

# 页面设置
st.set_page_config(
    page_title="学习分析仪表板",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"  # 手机端默认收起侧边栏
)

st.set_page_config(
    page_title="学习分析系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"  # 手机端默认收起侧边栏
)

# 添加移动端检测和优化
def is_mobile():
    """检测是否为移动设备"""
    user_agent = st.query_params.get("user_agent", "")
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad']
    return any(keyword in user_agent.lower() for keyword in mobile_keywords)

if is_mobile():
    st.markdown("""
    <style>
    .main > div {
        padding: 0rem 1rem;
    }
    .sidebar .sidebar-content {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化管理器
@st.cache_resource
def get_agent():
    return StudyAgent()

agent = get_agent()

# 侧边栏导航
st.sidebar.title("📚 学习分析系统")
page = st.sidebar.selectbox("导航", ["今日记录", "数据看板", "智能分析", "历史数据", "GitHub设置"])

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 数据同步")

if hasattr(data_manager, 'get_sync_status'):
    sync_status = data_manager.get_sync_status()
    
    if sync_status['connected']:
        st.sidebar.success("✅ GitHub 已连接")
        st.sidebar.write(f"仓库: `{sync_status['repo_info']}`")
        st.sidebar.write(f"记录数: {sync_status['data_count']}")
        
        if sync_status['last_sync']:
            from datetime import datetime
            last_sync = datetime.fromisoformat(sync_status['last_sync'])
            st.sidebar.write(f"最后同步: {last_sync.strftime('%m-%d %H:%M')}")
        
        if st.sidebar.button("🔄 强制同步"):
            if data_manager.force_sync():
                st.sidebar.success("同步成功!")
                st.rerun()
    else:
        st.sidebar.warning("⚠️ 使用本地存储")
        st.sidebar.info("配置 GitHub Token 启用云端同步")

# 主题颜色
primary_color = "#1f77b4"

# 在页面开始处初始化状态管理器
github_state_manager.init_session_state()

def check_and_restore_state():
    """检查并恢复状态"""
    today = datetime.now().date().isoformat()
    
    # 如果 session_state 中没有数据，尝试从 GitHub 恢复
    if not st.session_state.get('planned_tasks') and not st.session_state.get('tasks_confirmed'):
        st.sidebar.info("🔄 正在尝试恢复状态...")
        if github_state_manager.load_from_github(today):
            st.sidebar.success("✅ 状态恢复成功！")
            st.rerun()  # 重新渲染页面以显示恢复的数据
        else:
            st.sidebar.info("🆕 开始新的一天")

# 调用状态恢复检查
check_and_restore_state()

# 在侧边栏添加状态管理面板
def create_state_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 智能状态管理")
    
    state_info = github_state_manager.get_state_info()
    
    # 显示状态信息
    if state_info['last_save']:
        st.sidebar.info(f"💾 最后保存: {state_info['last_save'].strftime('%H:%M:%S')}")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        status = "✅ 今天" if state_info['is_today'] else "⚠️ 过往"
        st.metric("状态", status)
    with col2:
        st.metric("任务", state_info['planned_task_count'])
    
    # 智能保存模式说明
    st.sidebar.caption("🔍 智能保存模式：只在数据变化时保存")
    
    # 手动恢复按钮
    if st.sidebar.button("🔄 恢复状态"):
        today = datetime.now().date().isoformat()
        if github_state_manager.load_from_github(today):
            st.sidebar.success("状态恢复成功!")
            st.rerun()
        else:
            st.sidebar.error("状态恢复失败!")
    
    # 手动保存按钮（用于特殊情况）
    if st.sidebar.button("💾 手动保存"):
        if github_state_manager.manual_save_state():
            st.sidebar.success("手动保存成功!")
        else:
            st.sidebar.error("手动保存失败!")
    
    # 状态日期提醒
    if not state_info['is_today']:
        st.sidebar.warning(f"⚠️ 显示 {state_info['state_date']} 的状态")
        if st.sidebar.button("🆕 开始今天"):
            github_state_manager.clear_current_state()
            st.rerun()
    
    # 在侧边栏底部添加调试信息
    with st.sidebar.expander("🔧 调试信息"):
        # 保存模式信息
        st.write("💡 保存模式: 智能保存")
        st.write("📊 最小保存间隔: 10秒")
        st.write("🔍 变化检测: 启用")
        
        state_info = github_state_manager.get_state_info()
        st.write("GitHub 连接:", "✅ 已连接" if state_info['github_connected'] else "❌ 未连接")
        st.write("状态日期:", state_info['state_date'])
        st.write("计划任务数:", state_info['planned_task_count'])
        st.write("任务确认:", state_info['tasks_confirmed'])
        st.write("今日状态:", state_info['is_today'])
        
        # 调试模式开关
        debug_mode = st.checkbox("调试模式", value=st.session_state.get('debug_mode', False))
        st.session_state.debug_mode = debug_mode
        
        # 显示保存的状态文件内容（调试用）
        if st.button("查看保存的状态"):
            today = datetime.now().date().isoformat()
            all_states = github_state_manager._load_all_states_from_github()
            if today in all_states:
                st.json(all_states[today])
            else:
                st.info("今天没有保存的状态")

# 在页面中调用
create_state_sidebar()

# 页面1: 今日记录
if page == "今日记录":
    st.title("📝 今日学习记录")

    with st.form("daily_record"):
        col1, col2, col3 = st.columns(3)
        with col1:
            current_date_value = st.session_state.get('current_date', datetime.now().date())
            current_date = st.date_input("日期", value=current_date_value, key="date_input")
            # 日期变化时保存
            if current_date != st.session_state.get('current_date'):
                st.session_state.current_date = current_date
                github_state_manager.auto_save_state(force=True)
                
        with col2:
            current_weather_value = st.session_state.get('current_weather', "晴")
            weather_options = ["晴", "多云", "雨", "阴", "雪"]
            current_weather_index = weather_options.index(current_weather_value) if current_weather_value in weather_options else 0
            
            current_weather = st.selectbox("天气", weather_options, index=current_weather_index, key="weather_input")
            if current_weather != st.session_state.get('current_weather'):
                st.session_state.current_weather = current_weather
                # 天气变化时不立即保存，等待其他操作
            
        with col3:
            current_energy_level_value = st.session_state.get('current_energy_level', 7)
            current_energy_level = st.slider("精力水平", 1, 10, value=current_energy_level_value, key="energy_input")
            if current_energy_level != st.session_state.get('current_energy_level'):
                st.session_state.current_energy_level = current_energy_level
                # 精力水平变化时不立即保存，等待其他操作
        
        st.subheader("今日计划任务")
        planned_tasks = []

        with st.expander("添加计划任务", expanded=st.session_state.get('expander_expanded', True)):
            # 动态调整任务数量
            current_task_count = max(3, len(st.session_state.get('planned_tasks', [])))
            task_count = st.number_input("任务数量", min_value=1, max_value=10, value=current_task_count)
            
            for i in range(task_count):
                st.markdown(f"**任务 {i+1}**")
                
                # 单行布局
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
                
                # 从保存的数据中获取默认值
                saved_task = st.session_state.get('planned_tasks', [])[i] if i < len(st.session_state.get('planned_tasks', [])) else {}
                
                with col1:
                    task_name = st.text_input(
                        "任务名称", 
                        value=saved_task.get('task_name', ''),
                        key=f"task_name_{i}",
                        placeholder="如：群论复习",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    subject_options = ["math", "physics", "econ", "cs", "other"]
                    subject_default = saved_task.get('subject', 'math')
                    subject_index = subject_options.index(subject_default) if subject_default in subject_options else 0
                    
                    subject = st.selectbox(
                        "学科", 
                        subject_options,
                        index=subject_index,
                        key=f"subject_{i}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    difficulty_default = saved_task.get('difficulty', 3)
                    difficulty_index = difficulty_default - 1 if 1 <= difficulty_default <= 5 else 2
                    
                    difficulty = st.selectbox(
                        "难度", 
                        [1, 2, 3, 4, 5], 
                        index=difficulty_index,
                        key=f"difficulty_{i}",
                        label_visibility="collapsed"
                    )
                
                with col4:
                    # 从缓存或保存数据获取开始时间
                    start_cache_key = f"start_{i}"
                    time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    if start_cache_key in time_inputs_cache:
                        default_start = time_inputs_cache[start_cache_key]
                    elif 'planned_start_time' in saved_task:
                        default_start = datetime.strptime(saved_task['planned_start_time'], '%H:%M').time()
                    else:
                        default_start = datetime.now().time().replace(hour=9, minute=0)
                    
                    start_time = st.time_input(
                        "开始时间", 
                        value=default_start,
                        key=f"start_{i}",
                        step=300,
                        label_visibility="collapsed"
                    )
                    # 缓存时间值
                    st.session_state.time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    st.session_state.time_inputs_cache[start_cache_key] = start_time
                
                with col5:
                    # 从缓存或保存数据获取结束时间
                    end_cache_key = f"end_{i}"
                    time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    if end_cache_key in time_inputs_cache:
                        default_end = time_inputs_cache[end_cache_key]
                    elif 'planned_end_time' in saved_task:
                        default_end = datetime.strptime(saved_task['planned_end_time'], '%H:%M').time()
                    else:
                        default_end = datetime.now().time().replace(hour=10, minute=0)
                    
                    end_time = st.time_input(
                        "结束时间", 
                        value=default_end,
                        key=f"end_{i}",
                        step=300,
                        label_visibility="collapsed"
                    )
                    st.session_state.time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    st.session_state.time_inputs_cache[end_cache_key] = end_time
                    
                    if end_time <= start_time:
                        st.error("❌ 结束时间必须在开始时间之后")
                        github_state_manager.auto_save_state(force=True)
                        time.sleep(0.5)
                        st.rerun()

                with col6:
                    # 显示时长
                    start_dt = datetime.combine(current_date, start_time)
                    end_dt = datetime.combine(current_date, end_time)
                    calculated_duration = calculate_duration(start_dt, end_dt)
                    st.markdown(f"#### {calculated_duration}分钟")

                with col7:
                    st.write("")
                
                # 标签说明
                col_labels = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
                with col_labels[0]:
                    st.caption("任务名称")
                with col_labels[1]:
                    st.caption("学科")
                with col_labels[2]:
                    st.caption("难度")
                with col_labels[3]:
                    st.caption("开始时间")
                with col_labels[4]:
                    st.caption("结束时间")
                with col_labels[5]:
                    st.caption("计划时长")
                with col_labels[6]:
                    st.caption("")

                # 实时保存任务数据（只在有任务名称时保存）
                if task_name.strip():
                    start_dt = datetime.combine(current_date, start_time)
                    end_dt = datetime.combine(current_date, end_time)
                    calculated_duration = calculate_duration(start_dt, end_dt)

                    task_data = {
                        "task_id": i+1,
                        "task_name": task_name,
                        "subject": subject,
                        "planned_duration": calculated_duration,
                        "planned_focus_duration": int(calculated_duration * 0.8),
                        "difficulty": difficulty,
                        "planned_start_time": start_time.strftime('%H:%M'),
                        "planned_end_time": end_time.strftime('%H:%M')
                    }
                    
                    # 更新或添加任务数据
                    planned_tasks = st.session_state.get('planned_tasks', [])
                    if i < len(planned_tasks):
                        planned_tasks[i] = task_data
                    else:
                        planned_tasks.append(task_data)
                    st.session_state.planned_tasks = planned_tasks
                    
                    # 智能保存：只在有实际任务内容时保存
                    github_state_manager.auto_save_state()
                
                st.markdown("---")

            # 计划任务确认逻辑
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.session_state.get('tasks_confirmed', False):
                    st.success("✅ 计划任务已确认，不可再修改")
                    disabled_btn = st.form_submit_button(
                        "✅ 计划任务已确认",
                        disabled=True,
                        use_container_width=True
                    )
                elif st.session_state.get('show_final_confirmation', False):
                    st.warning("⚠️ 请最终确认计划任务")
                    
                    confirm_col1, confirm_col2, confirm_col3 = st.columns([1, 1, 1])
                    with confirm_col1:
                        cancel_confirm = st.form_submit_button(
                            "❌ 取消",
                            type="secondary",
                            use_container_width=True
                        )
                        if cancel_confirm:
                            st.session_state.show_final_confirmation = False
                            github_state_manager.auto_save_state(force=True)
                            st.rerun()
                            
                    with confirm_col2:
                        final_confirm = st.form_submit_button(
                            "🔒 最终确认",
                            type="primary",
                            use_container_width=True
                        )
                        if final_confirm:
                            st.session_state.tasks_confirmed = True
                            st.session_state.show_final_confirmation = False
                            st.session_state.expander_expanded = False
                            github_state_manager.auto_save_state(force=True)  # 关键操作，强制保存
                            st.success(f"✅ 已确认 {len(st.session_state.planned_tasks)} 个计划任务！")
                            st.rerun()
                else:
                    submit_planned_tasks = st.form_submit_button(
                        "✅ 确认计划任务",
                        type="primary",
                        use_container_width=True
                    )
                    
                    if submit_planned_tasks:
                        planned_tasks = st.session_state.get('planned_tasks', [])
                        if planned_tasks:
                            time_conflicts = check_time_conflicts(planned_tasks, current_date)
                            if time_conflicts:
                                st.error("❌ 存在时间冲突的任务，请调整：")
                                for conflict in time_conflicts:
                                    st.error(f"- {conflict}")
                            else:
                                st.session_state.show_final_confirmation = True
                                github_state_manager.auto_save_state(force=True)  # 关键操作，强制保存
                                st.rerun()
                        else:
                            st.warning("⚠️ 请至少填写一个任务名称")

        # 显示今日时间线概览
        if st.session_state.get('planned_tasks') and st.session_state.get('tasks_confirmed'):
            st.subheader("📅 今日计划时间线")
            
            # 创建时间线数据
            timeline_data = []
            planned_tasks = st.session_state.get('planned_tasks', [])
            for task in planned_tasks:
                start_dt = datetime.combine(current_date, datetime.strptime(task['planned_start_time'], '%H:%M').time())
                end_dt = datetime.combine(current_date, datetime.strptime(task['planned_end_time'], '%H:%M').time())
                
                timeline_data.append({
                    'Task': task['task_name'],
                    'Start': start_dt,
                    'Finish': end_dt,
                    'Duration': f"{task['planned_duration']}分钟",
                    'Subject': task['subject'],
                    'Difficulty': task['difficulty']
                })

            # 按照开始时间排序
            timeline_data.sort(key=lambda x: x['Start'])
            
            # 显示时间线表格
            if timeline_data:
                df_timeline = pd.DataFrame(timeline_data)
                df_display = df_timeline[['Task', 'Subject', 'Start', 'Finish', 'Duration', 'Difficulty']].copy()
                df_display['Start'] = df_display['Start'].dt.strftime('%H:%M')
                df_display['Finish'] = df_display['Finish'].dt.strftime('%H:%M')
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    column_config={
                        "Task": "任务名称",
                        "Subject": "学科",
                        "Start": "开始时间",
                        "Finish": "结束时间",
                        "Duration": "时长",
                        "Difficulty": "难度"
                    }
                )
                
                # 显示总时长统计
                total_planned = sum(task['planned_duration'] for task in planned_tasks)
                st.info(f"📊 今日总计划学习时间: {total_planned}分钟 ({total_planned/60:.1f}小时)")
        
        # 实际执行情况
        if st.session_state.get('planned_tasks') and st.session_state.get('tasks_confirmed'):
            st.subheader("实际执行情况")
            
            # 按照开始时间排序
            planned_tasks = st.session_state.get('planned_tasks', [])
            sorted_tasks = sorted(planned_tasks, key=lambda x: datetime.strptime(x['planned_start_time'], '%H:%M'))

            for i, task in enumerate(sorted_tasks):
                # 从保存数据中获取实际执行信息
                actual_execution = st.session_state.get('actual_execution', [])
                saved_actual = actual_execution[i] if i < len(actual_execution) else {}
                
                # 执行情况输入 - 使用紧凑布局
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
                
                with col1:
                    st.markdown(f"##### {task['task_name']}")

                with col2:
                    # 获取实际开始时间
                    actual_start_cache_key = f"actual_start_{i}"
                    time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    if actual_start_cache_key in time_inputs_cache:
                        default_actual_start = time_inputs_cache[actual_start_cache_key]
                    elif 'actual_start_time' in saved_actual:
                        default_actual_start = datetime.strptime(saved_actual['actual_start_time'], '%H:%M').time()
                    else:
                        default_actual_start = datetime.strptime(task['planned_start_time'], '%H:%M').time()
                    
                    actual_start_time = st.time_input(
                        "实际开始时间",
                        value=default_actual_start,
                        key=f"actual_start_{i}",
                        step=300,
                        label_visibility="collapsed"
                    )
                    st.session_state.time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    st.session_state.time_inputs_cache[actual_start_cache_key] = actual_start_time
                
                with col3:
                    # 获取实际结束时间
                    actual_end_cache_key = f"actual_end_{i}"
                    time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    if actual_end_cache_key in time_inputs_cache:
                        default_actual_end = time_inputs_cache[actual_end_cache_key]
                    elif 'actual_end_time' in saved_actual:
                        default_actual_end = datetime.strptime(saved_actual['actual_end_time'], '%H:%M').time()
                    else:
                        default_actual_end = datetime.strptime(task['planned_end_time'], '%H:%M').time()
                    
                    actual_end_time = st.time_input(
                        "实际结束时间",
                        value=default_actual_end,
                        key=f"actual_end_{i}",
                        step=300,
                        label_visibility="collapsed"
                    )
                    st.session_state.time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    st.session_state.time_inputs_cache[actual_end_cache_key] = actual_end_time
                    
                    if actual_end_time <= actual_start_time:
                        st.error("❌ 实际结束时间必须在实际开始时间之后")
                        github_state_manager.auto_save_state(force=True)
                        time.sleep(0.5)
                        st.rerun()

                with col4:
                    # 计算实际时长
                    start_dt = datetime.combine(current_date, actual_start_time)
                    end_dt = datetime.combine(current_date, actual_end_time)
                    actual_duration = calculate_duration(start_dt, end_dt)
                    
                    st.markdown(f"##### {actual_duration}分钟")

                with col5:
                    # 获取精力水平
                    energy_cache_key = f"energy_{i}"
                    time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    if energy_cache_key in time_inputs_cache:
                        default_energy = time_inputs_cache[energy_cache_key]
                    elif 'post_energy' in saved_actual:
                        default_energy = saved_actual['post_energy']
                    else:
                        default_energy = 7
                        
                    task_energy = st.select_slider(
                        "结束后精力", 
                        options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                        value=default_energy,
                        key=f"energy_input_{i}",
                        label_visibility="collapsed"
                    )
                    st.session_state.time_inputs_cache = st.session_state.get('time_inputs_cache', {})
                    st.session_state.time_inputs_cache[energy_cache_key] = task_energy
                
                # 标签说明
                col_labels = st.columns([2, 2, 2, 2, 2])
                with col_labels[0]:
                    st.caption("任务名称")
                with col_labels[1]:
                    st.caption("实际开始时间")
                with col_labels[2]:
                    st.caption("实际结束时间")
                with col_labels[3]:
                    st.caption("实际学习时长")
                with col_labels[4]:
                    st.caption("结束后精力")

                # 保存实际执行数据
                if start_dt < end_dt:                    
                    actual_data = {
                        "task_id": task['task_id'],
                        "actual_start_time": actual_start_time.strftime('%H:%M'),
                        "actual_end_time": actual_end_time.strftime('%H:%M'),
                        "actual_duration": actual_duration,
                        "actual_focus_duration": int(actual_duration * 0.8),
                        "post_energy": task_energy,
                        "completed": True
                    }
                    
                    # 更新或添加实际执行数据
                    actual_execution = st.session_state.get('actual_execution', [])
                    if i < len(actual_execution):
                        actual_execution[i] = actual_data
                    else:
                        actual_execution.append(actual_data)
                    st.session_state.actual_execution = actual_execution
                    
                    # 智能保存：有实际执行数据时保存
                    github_state_manager.auto_save_state()
                else:
                    st.warning("⚠️ 请调整时间以确保结束时间在开始时间之后")

                st.markdown("---")
            
            # 反思框
            current_reflection_value = st.session_state.get('current_reflection', "")
            current_reflection = st.text_area(
                "今日反思", 
                value=current_reflection_value,
                placeholder="今天的收获和改进点...", 
                key="reflection_input"
            )
            # 反思内容变化时智能保存（有内容才保存）
            if (current_reflection != st.session_state.get('current_reflection') and 
                current_reflection.strip()):
                st.session_state.current_reflection = current_reflection
                github_state_manager.auto_save_state()
            
            # 最终提交按钮
            if st.session_state.get('tasks_saved', False):
                st.success("✅ 今日记录已保存，不可再修改")
                disabled_btn = st.form_submit_button("✅ 今日记录已保存", disabled=True)
            else:
                submitted = st.form_submit_button("💾 保存今日记录")
                if submitted:
                    st.session_state.tasks_saved = True
                    github_state_manager.auto_save_state(force=True)  # 最终提交，强制保存
                    
                    # 保存到数据管理器
                    try:
                        success = data_manager.add_daily_record(
                            current_date.strftime("%Y-%m-%d"),
                            current_weather,
                            current_energy_level,
                            sorted_tasks,
                            st.session_state.get('actual_execution', []),
                            {
                                "planned_total_time": sum(t['planned_duration'] for t in st.session_state.get('planned_tasks', [])),
                                "actual_total_time": sum(t['actual_duration'] for t in st.session_state.get('actual_execution', [])) if st.session_state.get('actual_execution') else 0,
                                "planned_focus_time": sum(t['planned_focus_duration'] for t in st.session_state.get('planned_tasks', [])),
                                "actual_focus_time": sum(t['actual_focus_duration'] for t in st.session_state.get('actual_execution', [])) if st.session_state.get('actual_execution') else 0,
                                "completion_rate": len(st.session_state.get('actual_execution', [])) / len(st.session_state.get('planned_tasks', [])) if st.session_state.get('planned_tasks') else 0,
                                "reflection": current_reflection
                            }
                        )
                        
                        if success:
                            st.balloons()
                            st.success("🎉 今日记录保存成功！")
                        else:
                            st.error("❌ 保存失败，请检查数据格式")
                            
                    except Exception as e:
                        st.error(f"❌ 保存过程中发生错误: {str(e)}")
                    
                    st.rerun()

        else:
            if not st.session_state.get('planned_tasks'):
                st.info("👆 请在上方添加和确认今日的计划任务")
            elif not st.session_state.get('tasks_confirmed'):
                st.info("👆 请先确认今日的计划任务")
                            

elif page == "数据看板":
    st.title("📊 学习数据看板")
    
    data = data_manager.get_recent_data(30)
    if not data:
        st.info("暂无数据，请先记录今日学习情况")
        st.stop()
    
    # 指标卡片
    recent_metrics = [data_manager.calculate_daily_metrics(day) for day in data[-7:]]
    if recent_metrics:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_completion = pd.DataFrame(recent_metrics)['completion_rate'].mean()
            st.metric("平均完成率", f"{avg_completion:.1%}")
        with col2:
            avg_efficiency = pd.DataFrame(recent_metrics)['focus_efficiency'].mean()
            st.metric("平均专注效率", f"{avg_efficiency:.1%}")
        with col3:
            total_focus = pd.DataFrame(recent_metrics)['total_focus_time'].sum() / 60
            st.metric("总专注时间", f"{total_focus:.1f}小时")
        with col4:
            avg_accuracy = pd.DataFrame(recent_metrics)['planning_accuracy'].mean()
            st.metric("计划准确性", f"{avg_accuracy:.1%}")
    
    # 趋势图表
    col1, col2 = st.columns(2)
    
    with col1:
        df_metrics = pd.DataFrame([data_manager.calculate_daily_metrics(day) for day in data])
        if not df_metrics.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_metrics['date'], y=df_metrics['completion_rate'], 
                                   name='完成率', line=dict(color=primary_color)))
            fig.add_trace(go.Scatter(x=df_metrics['date'], y=df_metrics['focus_efficiency'], 
                                   name='专注效率', line=dict(color='#ff7f0e')))
            fig.update_layout(title="学习效率趋势", xaxis_title="日期", yaxis_title="比率")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        subject_stats = data_manager.get_subject_stats(data)
        if subject_stats:
            df_subject = pd.DataFrame([
                {'subject': sub, '实际时间': stats['actual_time']/60, '计划时间': stats['planned_time']/60}
                for sub, stats in subject_stats.items()
            ])
            fig = px.bar(df_subject, x='subject', y=['计划时间', '实际时间'], 
                        title="各学科时间分配", barmode='group')
            st.plotly_chart(fig, use_container_width=True)

# 页面3: 智能分析
elif page == "智能分析":
    st.title("🤖 智能分析助手")
    
    data = data_manager.get_recent_data(14)
    if len(data) < 3:
        st.warning("请至少积累3天的数据以获得有意义的分析")
        st.stop()
    
    tab1, tab2 = st.tabs(["周度分析", "明日建议"])
    
    with tab1:
        st.subheader("📈 本周学习分析")
        if st.button("生成分析报告"):
            with st.spinner("AI正在分析您的学习数据..."):
                analysis = agent.analyze_weekly_trends(data)
                st.markdown("### 分析结果")
                st.markdown(analysis)
    
    with tab2:
        st.subheader("📅 明日计划建议")
        if st.button("获取明日建议"):
            with st.spinner("AI正在为您规划..."):
                suggestion = agent.generate_tomorrow_plan(data)
                st.markdown("### 个性化建议")
                st.markdown(suggestion)

# 页面4: 历史数据
elif page == "历史数据":
    st.title("📋 历史记录浏览")
    
    data = data_manager.load_all_data()
    if not data:
        st.info("暂无历史数据")
        st.stop()
    
    # 日期筛选
    dates = sorted([d['date'] for d in data], reverse=True)
    selected_date = st.selectbox("选择日期查看详情", dates)
    
    selected_data = next((d for d in data if d['date'] == selected_date), None)
    if selected_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 基本信息")
            st.write(f"**日期**: {selected_data['date']}")
            st.write(f"**天气**: {selected_data['weather']}")
            st.write(f"**精力水平**: {selected_data['energy_level']}/10")
            
            st.subheader("📋 计划任务")
            for task in selected_data['planned_tasks']:
                if 'planned_start_time' in task and 'planned_end_time' in task:
                    st.write(f"- {task['task_name']} ({task['subject']}): {task['planned_start_time']} - {task['planned_end_time']} ({task['planned_duration']}分钟)")
                else:
                    st.write(f"- {task['task_name']} ({task['subject']}): {task['planned_duration']}分钟")
        
        with col2:
            st.subheader("✅ 执行情况")
            summary = selected_data['daily_summary']
            st.metric("完成率", f"{summary['completion_rate']:.1%}")
            st.metric("计划时间", f"{summary['planned_total_time']}分钟")
            st.metric("实际时间", f"{summary['actual_total_time']}分钟")
            
            st.subheader("💭 当日反思")
            st.info(summary.get('reflection', '暂无反思记录'))
# 添加 GitHub 设置页面
elif page == "GitHub设置":
    st.title("⚙️ GitHub 数据存储设置")
    
    st.markdown("""
    ## 📚 使用 GitHub 作为数据库
    
    将你的学习数据存储在 GitHub 仓库中，实现：
    - 🔄 **多设备同步** - 在任何地方访问你的数据
    - 💾 **版本控制** - 自动记录所有更改历史
    - 🆓 **完全免费** - 使用 GitHub 的免费额度
    - 🔒 **数据安全** - 你的数据受 GitHub 保护
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛠️ 配置步骤")
        
        st.markdown("""
        1. **创建 GitHub Personal Token**
           - 访问 [GitHub Settings → Tokens](https://github.com/settings/tokens)
           - 点击 "Generate new token"
           - 选择 "repo" 权限
           - 复制生成的 token
        
        2. **配置 Streamlit Secrets**
           - 在 Streamlit Cloud 点击 "Manage app"
           - 进入 "Settings" → "Secrets"
           - 添加以下配置：
        """)
        
        st.code("""GITHUB_TOKEN=ghp_你的token
GITHUB_OWNER=你的用户名
GITHUB_REPO=仓库名""", language="ini")
    
    with col2:
        st.subheader("🔍 当前状态")
        
        if hasattr(data_manager, 'get_sync_status'):
            status = data_manager.get_sync_status()
            
            if status['connected']:
                st.success("✅ GitHub 连接正常")
                st.metric("数据记录", status['data_count'])
                st.metric("仓库", status['repo_info'])
                
                if status['last_sync']:
                    from datetime import datetime
                    last_sync = datetime.fromisoformat(status['last_sync'])
                    st.write(f"最后同步: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 数据操作
                st.subheader("📊 数据操作")
                
                all_data = data_manager.load_all_data()
                if all_data:
                    # 导出数据
                    json_data = json.dumps(all_data, ensure_ascii=False, indent=2)
                    st.download_button(
                        "💾 导出完整数据",
                        data=json_data,
                        file_name=f"study_data_backup_{datetime.now().strftime('%Y%m%d')}.json",
                        help="下载完整的 JSON 数据备份"
                    )
                    
                    # 查看数据文件
                    if st.button("🔍 查看 GitHub 数据文件"):
                        repo_url = f"https://github.com/{status['repo_info']}/blob/main/study_data.json"
                        st.markdown(f"[📁 在 GitHub 中查看数据文件]({repo_url})")
                
            else:
                st.warning("⚠️ 未连接 GitHub")
                st.info("请按照左侧步骤配置 GitHub Token")
        
        st.subheader("🔄 手动同步")
        if st.button("强制同步到 GitHub"):
            with st.spinner("同步中..."):
                if data_manager.force_sync():
                    st.success("✅ 同步成功!")
                    st.rerun()
                else:
                    st.error("❌ 同步失败")

# 运行说明
st.sidebar.markdown("---")
st.sidebar.info("""
**使用指南:**
1. **今日记录**: 填写每日学习和计划
2. **数据看板**: 查看学习趋势和统计
3. **智能分析**: 获取AI建议和洞察
4. **历史数据**: 浏览过往记录
""")

if __name__ == "__main__":
    pass
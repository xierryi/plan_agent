import streamlit as st
try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, timedelta, time
    import json
    import time as time_module
    import numpy as np
    from data_manager import StudyDataManager
    from study_agent import StudyAgent
    import hashlib
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

MAX_TASK_COUNT = 12

def handle_date_change(selected_date):
    """处理日期变更 - 更新所有控件状态"""
    current_date = st.session_state.get('current_date', datetime.now().date())
    
    # 如果日期没有变化，直接返回
    if selected_date == current_date:
        return
    
    # 保存当前日期的状态（如果有变化）
    if github_state_manager._get_state_hash() != github_state_manager.last_state_hash:
        github_state_manager.auto_save_state(force=True)
    
    # 更新当前日期
    st.session_state.current_date = selected_date
    
    # 调用状态管理器的日期变更处理
    github_state_manager._handle_plan_date_change(selected_date.isoformat())
    
    # 强制更新所有表单组件状态
    update_all_form_components()
    
    # 强制重新运行以应用新状态
    st.rerun()

def update_all_form_components():
    """更新所有表单组件的状态 - 确保切换日期后表单显示正确数据"""
    planned_tasks = st.session_state.get('planned_tasks', [])
    
    # 更新所有任务相关的表单组件状态
    for i, task in enumerate(planned_tasks):
        # 任务名称
        task_name_key = f"task_name_{i}"
        st.session_state[task_name_key] = task.get('task_name', '')
        
        # 学科
        subject_key = f"subject_{i}"
        st.session_state[subject_key] = task.get('subject', 'math')
        
        # 难度
        difficulty_key = f"difficulty_{i}"
        st.session_state[difficulty_key] = task.get('difficulty', 3)
        
        # 开始时间
        start_key = f"start_{i}"
        start_time = task.get('planned_start_time', time(9+i, 0))
        if isinstance(start_time, str):
            start_time = parse_time(start_time)
        st.session_state[start_key] = start_time
        
        # 结束时间
        end_key = f"end_{i}"
        end_time = task.get('planned_end_time', time(10+i, 0))
        if isinstance(end_time, str):
            end_time = parse_time(end_time)
        st.session_state[end_key] = end_time
        
        # 实际开始时间
        actual_start_key = f"actual_start_{i}"
        actual_execution = st.session_state.get('actual_execution', [])
        actual_start_time = actual_execution[i].get('actual_start_time', start_time) if i < len(actual_execution) else start_time
        if isinstance(actual_start_time, str):
            actual_start_time = parse_time(actual_start_time)
        st.session_state[actual_start_key] = actual_start_time
        
        # 实际结束时间
        actual_end_key = f"actual_end_{i}"
        actual_end_time = actual_execution[i].get('actual_end_time', end_time) if i < len(actual_execution) else end_time
        if isinstance(actual_end_time, str):
            actual_end_time = parse_time(actual_end_time)
        st.session_state[actual_end_key] = actual_end_time
        
        # 精力水平
        energy_key = f"energy_input_{i}"
        actual_energy = actual_execution[i].get('post_energy', 7) if i < len(actual_execution) else 7
        st.session_state[energy_key] = actual_energy

def process_all_task_data(task_count, current_date):
    """处理所有任务数据并更新到 session_state"""
    planned_tasks = []
    valid_task_count = 0
    
    for i in range(task_count):
        task_name = st.session_state.get(f"task_name_{i}", "").strip()
        subject = st.session_state.get(f"subject_{i}", "math")
        difficulty = st.session_state.get(f"difficulty_{i}", 3)
        start_time = st.session_state.get(f"start_{i}", time(9+i, 0))
        end_time = st.session_state.get(f"end_{i}", time(10+i, 0))
        
        # 计算时长
        start_dt = datetime.combine(current_date, start_time)
        end_dt = datetime.combine(current_date, end_time)
        calculated_duration = calculate_duration(start_dt, end_dt)
        
        if task_name:  # 只保存有任务名称的任务
            task_data = {
                "task_id": valid_task_count + 1,
                "task_name": task_name,
                "subject": subject,
                "planned_duration": calculated_duration,
                "planned_focus_duration": int(calculated_duration * 0.8),
                "difficulty": difficulty,
                "planned_start_time": start_time,
                "planned_end_time": end_time
            }
            planned_tasks.append(task_data)
            valid_task_count += 1
    
    return planned_tasks

def update_task_data_in_realtime(i, current_date):
    """实时更新单个任务数据"""
    task_name = st.session_state.get(f"task_name_{i}", "").strip()
    subject = st.session_state.get(f"subject_{i}", "math")
    difficulty = st.session_state.get(f"difficulty_{i}", 3)
    start_time = st.session_state.get(f"start_{i}", time(9+i, 0))
    end_time = st.session_state.get(f"end_{i}", time(10+i, 0))
    
    if task_name:
        # 计算时长
        start_dt = datetime.combine(current_date, start_time)
        end_dt = datetime.combine(current_date, end_time)
        calculated_duration = calculate_duration(start_dt, end_dt)
        
        task_data = {
            "task_id": i + 1,
            "task_name": task_name,
            "subject": subject,
            "planned_duration": calculated_duration,
            "planned_focus_duration": int(calculated_duration * 0.8),
            "difficulty": difficulty,
            "planned_start_time": start_time,
            "planned_end_time": end_time
        }
        
        # 更新或添加任务数据
        planned_tasks = st.session_state.get('planned_tasks', [])
        while len(planned_tasks) <= i:
            planned_tasks.append({})
        planned_tasks[i] = task_data
        st.session_state.planned_tasks = planned_tasks
        
        # 智能保存
        github_state_manager.auto_save_state()

def update_actual_execution_data(i, task, current_date):
    """更新实际执行数据"""
    actual_start_time = st.session_state.get(f"actual_start_{i}")
    actual_end_time = st.session_state.get(f"actual_end_{i}")
    task_energy = st.session_state.get(f"energy_input_{i}", 7)
    
    # 验证时间
    if actual_end_time <= actual_start_time:
        return False  # 时间无效，不保存
    
    # 计算时长
    start_dt = datetime.combine(current_date, actual_start_time)
    end_dt = datetime.combine(current_date, actual_end_time)
    actual_duration = calculate_duration(start_dt, end_dt)
    
    actual_data = {
        "task_id": task['task_id'],
        "actual_start_time": actual_start_time,
        "actual_end_time": actual_end_time,
        "actual_duration": actual_duration,
        "actual_focus_duration": int(actual_duration * 0.8),
        "post_energy": task_energy,
        "completed": True
    }
    
    # 更新实际执行数据
    actual_execution = st.session_state.get('actual_execution', [])
    if i < len(actual_execution):
        actual_execution[i] = actual_data
    else:
        actual_execution.append(actual_data)
    st.session_state.actual_execution = actual_execution
    
    # 智能保存
    github_state_manager.auto_save_state()
    return True

def parse_time(time_value):
    """通用时间解析函数"""
    try:
        # 如果已经是 time 对象，直接返回
        if hasattr(time_value, 'hour') and hasattr(time_value, 'minute'):
            return time_value
        # 如果是字符串，尝试解析
        elif isinstance(time_value, str):
            return datetime.strptime(time_value, '%H:%M').time()
        else:
            return datetime.strptime("09:00", '%H:%M').time()
    except (ValueError, TypeError):
        return datetime.strptime("09:00", '%H:%M').time()

def check_time_conflicts(planned_tasks, date):
    """检查任务时间是否重叠"""
    conflicts = []
    time_ranges = []
    
    for task in planned_tasks:
        if 'planned_start_time' in task and 'planned_end_time' in task:
            try:
                # 直接使用 parse_time，不需要手动转换
                start_time = parse_time(task['planned_start_time'])
                end_time = parse_time(task['planned_end_time'])
                
                start_dt = datetime.combine(date, start_time)
                end_dt = datetime.combine(date, end_time)
                
                # 处理跨天情况（比如23:00到01:00）
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
                
                time_ranges.append({
                    'task_name': task['task_name'],
                    'start': start_dt,
                    'end': end_dt
                })
                
            except Exception as e:
                # 如果时间解析失败，跳过这个任务
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

# 初始化 AI Agent（带数据管理器）
@st.cache_resource
def get_agent(_data_manager):
    """创建带数据管理器的 Agent"""
    return StudyAgent(_data_manager)

agent = get_agent(data_manager)

# 初始化当前日期
if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.now().date()

# 初始化状态管理器
github_state_manager.init_session_state()

# 确保表单组件状态正确
if st.session_state.get('planned_tasks'):
    update_all_form_components()

# 侧边栏导航
st.sidebar.title("📚 学习分析系统")
page = st.sidebar.selectbox("导航", ["今日记录", "AI 助手", "数据看板", "智能分析", "历史数据", "GitHub设置"])

# 计划管理侧边栏
def create_plan_management_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 计划管理")
    
    state_info = github_state_manager.get_state_info()
    current_date = st.session_state.get('current_date', datetime.now().date())
    
    # 显示当前状态
    if state_info['date_status'] == 'today':
        st.sidebar.success("📅 今天")
        st.sidebar.write(f"计划任务: {state_info['planned_task_count']}个")
    elif state_info['date_status'] == 'future':
        st.sidebar.warning(f"📅 未来计划")
        st.sidebar.write(f"日期: {current_date}")
        st.sidebar.write(f"计划任务: {state_info['planned_task_count']}个")
    else:
        st.sidebar.info(f"📅 过往记录")
        st.sidebar.write(f"日期: {current_date}")
        st.sidebar.write(f"计划任务: {state_info['planned_task_count']}个")
    
    # 切换到今天的按钮
    if state_info['date_status'] != 'today':
        if st.sidebar.button("🔄 切换到今天"):
            today_date = datetime.now().date()
            st.session_state.current_date = today_date
            github_state_manager._handle_plan_date_change(today_date.isoformat())
            update_all_form_components()
            st.rerun()
    
    # 清除当前日期的计划（只在有计划时显示）
    if state_info['has_planned_tasks']:
        if st.sidebar.button("🗑️ 清除当前计划", type="secondary"):
            github_state_manager.clear_current_state()
            update_all_form_components()
            st.sidebar.success("计划已清除")
            st.rerun()

# 在页面中调用
create_plan_management_sidebar()

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

def handle_page_refresh():
    """处理页面刷新，确保状态正确恢复"""
    current_plan_date = st.session_state.get('current_date', datetime.now().date())
    plan_date_iso = current_plan_date.isoformat()
    
    # 如果关键状态不存在，尝试从 GitHub 恢复
    critical_states = ['planned_tasks', 'tasks_confirmed', 'current_date']
    states_missing = any(state not in st.session_state for state in critical_states)
    
    if states_missing:
        st.sidebar.info("🔄 检测到页面刷新，恢复状态中...")
        if github_state_manager.load_from_github(plan_date_iso):
            update_all_form_components()
            st.sidebar.success(f"✅ {current_plan_date} 状态恢复成功")
            st.rerun()
        else:
            if current_plan_date == datetime.now().date():
                st.sidebar.info("📝 开始新的学习记录")
            elif current_plan_date > datetime.now().date():
                st.sidebar.info(f"📝 开始 {current_plan_date} 的未来计划")
            else:
                st.sidebar.info(f"📝 开始 {current_plan_date} 的记录")

# 调用刷新处理
handle_page_refresh()

def check_and_restore_state():
    """检查并恢复状态 - 基于计划日期"""
    current_plan_date = st.session_state.get('current_date', datetime.now().date())
    plan_date_iso = current_plan_date.isoformat()
    
    # 如果 session_state 中没有数据，尝试从 GitHub 恢复
    if not st.session_state.get('planned_tasks') and not st.session_state.get('tasks_confirmed'):
        st.sidebar.info("🔄 正在尝试恢复状态...")
        if github_state_manager.load_from_github(plan_date_iso):
            update_all_form_components()
            st.sidebar.success(f"✅ {current_plan_date} 的状态恢复成功！")
        else:
            # 调用日期变更处理来初始化状态
            github_state_manager._handle_plan_date_change(plan_date_iso)
            update_all_form_components()

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
        if state_info['date_status'] == 'today':
            status = "✅ 今天"
        elif state_info['date_status'] == 'future':
            status = "🔮 未来"
        else:
            status = "📚 过往"
        st.metric("状态", status)
    with col2:
        st.metric("任务", state_info['planned_task_count'])
    
    # 智能保存模式说明
    st.sidebar.caption("🔍 智能保存模式：只在数据变化时保存")
    
    # 手动恢复按钮
    if st.sidebar.button("🔄 恢复状态"):
        current_plan_date = st.session_state.get('current_date', datetime.now().date())
        plan_date_iso = current_plan_date.isoformat()
        if github_state_manager.load_from_github(plan_date_iso):
            update_all_form_components()
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
    if state_info['date_status'] != 'today':
        current_date = st.session_state.get('current_date')
        if current_date:
            if state_info['date_status'] == 'future':
                st.sidebar.warning(f"📅 未来计划: {current_date}")
            else:
                st.sidebar.info(f"📅 过往记录: {current_date}")
        
        if st.sidebar.button("🆕 切换到今天"):
            today_date = datetime.now().date()
            st.session_state.current_date = today_date
            github_state_manager._handle_plan_date_change(today_date.isoformat())
            update_all_form_components()
            st.rerun()
    
    # 在侧边栏底部添加调试信息
    with st.sidebar.expander("🔧 调试信息"):
        state_info = github_state_manager.get_state_info()
        st.write("GitHub 连接:", "✅ 已连接" if state_info['github_connected'] else "❌ 未连接")
        st.write("计划日期:", state_info['plan_date'])
        st.write("计划任务数:", state_info['planned_task_count'])
        st.write("任务确认:", state_info['tasks_confirmed'])
        st.write("日期状态:", state_info['date_status'])
        st.write("距今天数:", state_info['days_from_today'])
        st.write("空状态检查:", "✅ 是" if github_state_manager._is_empty_state() else "❌ 否")
        
        # 显示保存的状态文件内容（调试用）
        if st.button("查看GitHub保存的状态"):
            current_plan_date = st.session_state.get('current_date', datetime.now().date())
            plan_date_iso = current_plan_date.isoformat()
            all_states = github_state_manager._load_all_states_from_github()
            if plan_date_iso in all_states:
                st.json(all_states[plan_date_iso])
                # 显示状态哈希对比
                current_hash = github_state_manager._get_state_hash()
                saved_data = all_states[plan_date_iso]
                saved_hash = hashlib.md5(json.dumps(saved_data, sort_keys=True).encode()).hexdigest()
                st.write("当前状态哈希:", current_hash[:8])
                st.write("保存状态哈希:", saved_hash[:8])
                st.write("状态一致:", current_hash == saved_hash)
            else:
                st.info(f"{plan_date_iso} 没有保存的状态")

# 在页面中调用
create_state_sidebar()

st.markdown("""
    <style>
    /* 减少所有元素的外边距 */
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
    
    /* 减少标题间距 */
    h1, h2, h3 {
        margin-bottom: 0.25rem !important;
        padding-top: 0.25rem !important;
    }
    
    /* 减少Streamlit组件间距 */
    .stTextInput, .stSelectbox, .stNumberInput, .stTimeInput, .stDateInput, .stSlider {
        margin-bottom: 0.25rem !important;
    }
    
    /* 减少按钮间距 */
    .stButton {
        margin-bottom: 0.25rem !important;
    }
    
    /* 减少列间距 */
    .row-widget.stColumns {
        gap: 0.25rem !important;
    }
    
    /* 减少展开器内边距 */
    .streamlit-expanderHeader {
        padding: 0.25rem 0.5rem !important;
    }
    
    /* 减少表格间距 */
    .stDataFrame {
        margin: 0.25rem 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 页面1: 今日记录
if page == "今日记录":
    current_date = st.session_state.get('current_date')
    today = datetime.now().date()
    
    state_info = github_state_manager.get_state_info()
    
    if state_info['date_status'] == 'today':
        st.markdown(f"##### 📝 今日学习记录")
    elif state_info['date_status'] == 'future':
        st.markdown(f"##### 📝 {current_date} 未来计划")
    else:
        st.markdown(f"##### 📝 {current_date} 学习记录")

    
    # === 基本信息区域 - 响应式3列布局 ===
    st.markdown(f"###### 📅 基本信息")

    info_cols = st.columns(4)
    with info_cols[0]:
        selected_date = st.date_input("日期", value=current_date)

        # 显示日期状态
        if selected_date == today:
            st.success("📅 今天")
        elif selected_date > today:
            st.warning("📅 未来计划")
        else:
            st.info("📅 过往记录")

    with info_cols[1]:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)  # 垂直对齐调整
        date_change_button = st.button("📅 切换日期")
        if date_change_button:
            handle_date_change(selected_date)
            
    with info_cols[2]:
        current_weather_value = st.session_state.get('current_weather', "晴")
        weather_options = ["晴", "多云", "雨", "阴", "雪"]
        current_weather_index = weather_options.index(current_weather_value) if current_weather_value in weather_options else 0
        
        current_weather = st.selectbox("天气", weather_options, index=current_weather_index, key="weather_input")
        if current_weather != st.session_state.get('current_weather'):
            st.session_state.current_weather = current_weather
            
    with info_cols[3]:
        current_energy_level_value = st.session_state.get('current_energy_level', 7)
        current_energy_level = st.slider("精力水平", 1, 10, value=current_energy_level_value, key="energy_input")
        if current_energy_level != st.session_state.get('current_energy_level'):
            st.session_state.current_energy_level = current_energy_level
    
    # === 计划任务区域 - 响应式设计 ===
    st.markdown(f"###### 📋 计划任务")
    planned_tasks = []

    with st.expander("添加计划任务", expanded=st.session_state.get('expander_expanded', True)):
        # 动态调整任务数量
        current_task_count = len(st.session_state.get('planned_tasks', []))
        if current_task_count == 0:
            current_task_count = 2  # 默认值

        task_count = st.number_input("任务数量", min_value=1, max_value=MAX_TASK_COUNT, value=current_task_count)

        # 如果任务数量变化，调整 planned_tasks 数组
        planned_tasks = st.session_state.get('planned_tasks', [])
        if task_count != len(planned_tasks):
            if task_count > len(planned_tasks):
                # 添加新任务
                for i in range(len(planned_tasks), task_count):
                    # 计算默认时间（基于最后一个任务）
                    last_task = planned_tasks[-1] if planned_tasks else None
                    if last_task and 'planned_end_time' in last_task:
                        last_end_time = parse_time(last_task['planned_end_time'])
                        start_hour = last_end_time.hour
                        start_minute = last_end_time.minute
                    else:
                        start_hour = 9 + i
                        start_minute = 0
                    
                    new_task = {
                        'task_id': i + 1,
                        'task_name': '',
                        'subject': 'math',
                        'difficulty': 3,
                        'planned_start_time': time(start_hour, start_minute),
                        'planned_end_time': time(start_hour + 1, start_minute),
                        'planned_duration': 60,
                        'planned_focus_duration': 48
                    }
                    planned_tasks.append(new_task)
            else:
                # 删除多余任务
                planned_tasks = planned_tasks[:task_count]
            
            st.session_state.planned_tasks = planned_tasks
            github_state_manager.auto_save_state()
            update_all_form_components()
            st.rerun()
        
        for i in range(task_count):
            st.markdown(f"###### 任务 {i+1}")
            
            # 从当前日期的缓存数据中获取默认值
            saved_task = {}
            if i < len(st.session_state.get('planned_tasks', [])):
                saved_task = st.session_state.planned_tasks[i]
            
            # 任务名称 - 使用 on_change 回调实时更新
            task_name = st.text_input(
                "任务名称", 
                value=st.session_state.get(f"task_name_{i}", saved_task.get('task_name', '')),
                key=f"task_name_{i}",
                placeholder="输入任务名称",
                on_change=lambda i=i: update_task_data_in_realtime(i, current_date)
            )
            
            # 学科和难度
            col1, col2 = st.columns(2)
            with col1:
                subject_options = ["math", "physics", "econ", "cs", "other"]
                subject_default = st.session_state.get(f"subject_{i}", saved_task.get('subject', 'math'))
                subject_index = subject_options.index(subject_default) if subject_default in subject_options else 0
                
                subject = st.selectbox(
                    "学科", 
                    subject_options,
                    index=subject_index,
                    key=f"subject_{i}",
                    on_change=lambda i=i: update_task_data_in_realtime(i, current_date)
                )
            
            with col2:
                difficulty_default = st.session_state.get(f"difficulty_{i}", saved_task.get('difficulty', 3))
                difficulty_index = difficulty_default - 1 if 1 <= difficulty_default <= 5 else 2
                
                difficulty = st.selectbox(
                    "难度", 
                    [1, 2, 3, 4, 5], 
                    index=difficulty_index,
                    key=f"difficulty_{i}",
                    on_change=lambda i=i: update_task_data_in_realtime(i, current_date)
                )
            
            # 时间设置
            time_cols = st.columns(2)
            with time_cols[0]:
                start_time_value = st.session_state.get(f"start_{i}", saved_task.get('planned_start_time', time(9+i, 0)))
                if isinstance(start_time_value, str):
                    start_time_value = parse_time(start_time_value)
                
                start_time = st.time_input(
                    "开始时间", 
                    value=start_time_value,
                    key=f"start_{i}",
                    step=300,
                    on_change=lambda i=i: update_task_data_in_realtime(i, current_date)
                )
            
            with time_cols[1]:
                end_time_value = st.session_state.get(f"end_{i}", saved_task.get('planned_end_time', time(10+i, 0)))
                if isinstance(end_time_value, str):
                    end_time_value = parse_time(end_time_value)
                
                end_time = st.time_input(
                    "结束时间", 
                    value=end_time_value,
                    key=f"end_{i}",
                    step=300,
                    on_change=lambda i=i: update_task_data_in_realtime(i, current_date)
                )

            # 显示时长
            start_dt = datetime.combine(current_date, start_time)
            end_dt = datetime.combine(current_date, end_time)
            calculated_duration = calculate_duration(start_dt, end_dt)
            st.info(f"计划时长: {calculated_duration}分钟")

        # 计划任务确认逻辑 - 响应式按钮布局
        st.markdown(f"###### 确认计划")
        if st.session_state.get('tasks_confirmed', False):
            st.success("✅ 计划任务已确认，不可再修改")
            st.button("✅ 计划任务已确认", disabled=True, use_container_width=True)
        elif st.session_state.get('show_final_confirmation', False):
            st.warning("⚠️ 请最终确认计划任务")
            
            confirm_cols = st.columns(2)
            with confirm_cols[0]:
                cancel_confirm = st.button(
                    "❌ 取消",
                    type="secondary",
                    use_container_width=True
                )
                if cancel_confirm:
                    st.session_state.show_final_confirmation = False
                    st.rerun()
                    
            with confirm_cols[1]:
                final_confirm = st.button(
                    "🔒 最终确认",
                    type="primary",
                    use_container_width=True
                )
                if final_confirm:
                    planned_tasks = process_all_task_data(task_count, current_date)
                    if planned_tasks:
                        time_conflicts = check_time_conflicts(planned_tasks, current_date)
                        if time_conflicts:
                            st.error("❌ 存在时间冲突的任务，请调整：")
                            for conflict in time_conflicts:
                                st.error(f"- {conflict}")
                        else:
                            st.session_state.tasks_confirmed = True
                            st.session_state.show_final_confirmation = False
                            st.session_state.expander_expanded = False
                            github_state_manager.auto_save_state()
                            if current_date == today:
                                st.success(f"✅ 已确认 {len(planned_tasks)} 个今日计划任务！")
                            elif current_date > today:
                                st.success(f"✅ 已确认 {len(planned_tasks)} 个未来计划任务！")
                            else:
                                st.success(f"✅ 已确认 {len(planned_tasks)} 个计划任务！")
                            st.rerun()
                    else:
                        st.error("❌ 请至少填写一个有效的任务名称")
        else:
            submit_planned_tasks = st.button(
                "✅ 确认计划任务",
                type="primary",
                use_container_width=True
            )
            
            if submit_planned_tasks:
                planned_tasks = process_all_task_data(task_count, current_date)
                if planned_tasks:
                    time_conflicts = check_time_conflicts(planned_tasks, current_date)
                    if time_conflicts:
                        st.error("❌ 存在时间冲突的任务，请调整：")
                        for conflict in time_conflicts:
                            st.error(f"- {conflict}")
                    else:
                        st.session_state.show_final_confirmation = True
                        github_state_manager.auto_save_state()
                        st.rerun()
                else:
                    st.error("❌ 请至少填写一个有效的任务名称")

    # === 时间线概览 - 响应式表格 ===
    if st.session_state.get('planned_tasks') and st.session_state.get('tasks_confirmed'):
        st.markdown(f"##### 📅 今日计划时间线")
        
        # 创建时间线数据
        timeline_data = []
        planned_tasks = st.session_state.get('planned_tasks', [])
        for task in planned_tasks:
            # 确保任务有时间数据
            if 'planned_start_time' in task and 'planned_end_time' in task:
                try:
                    start_dt = datetime.combine(current_date, parse_time(task.get('planned_start_time')))
                    end_dt = datetime.combine(current_date, parse_time(task.get('planned_end_time')))
                    
                    timeline_data.append({
                        'Task': task['task_name'],
                        'Start': start_dt,
                        'Finish': end_dt,
                        'Duration': f"{task['planned_duration']}分钟",
                        'Subject': task['subject'],
                        'Difficulty': task['difficulty']
                    })
                except Exception as e:
                    # 如果时间解析失败，跳过这个任务
                    continue

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
    
    # === 实际执行情况 - 响应式设计 ===
    if st.session_state.get('planned_tasks') and st.session_state.get('tasks_confirmed'):
        st.markdown(f"##### ✅ 实际执行情况")
        # 按照开始时间排序
        planned_tasks = st.session_state.get('planned_tasks', [])
        sorted_tasks = sorted(planned_tasks, key=lambda x: parse_time(x['planned_start_time']))

        for i, task in enumerate(sorted_tasks):
            st.markdown(f"##### {task['task_name']}")
            
            # 从保存数据中获取实际执行信息
            actual_execution = st.session_state.get('actual_execution', [])
            saved_actual = actual_execution[i] if i < len(actual_execution) else {}
            
            # 时间输入 - 2列布局
            time_cols = st.columns(2)
            with time_cols[0]:
                # 从 session_state 获取实际开始时间 - 添加回调
                actual_start_time = st.time_input(
                    "实际开始时间",
                    value=st.session_state.get(f"actual_start_{i}", parse_time(saved_actual.get('actual_start_time', task['planned_start_time']))),
                    key=f"actual_start_{i}",
                    step=300,
                    on_change=lambda i=i, task=task: update_actual_execution_data(i, task, current_date)
                )
            
            with time_cols[1]:
                # 从 session_state 获取实际结束时间 - 添加回调
                actual_end_time = st.time_input(
                    "实际结束时间",
                    value=st.session_state.get(f"actual_end_{i}", parse_time(saved_actual.get('actual_end_time', task['planned_end_time']))),
                    key=f"actual_end_{i}",
                    step=300,
                    on_change=lambda i=i, task=task: update_actual_execution_data(i, task, current_date)
                )
                
                if actual_end_time <= actual_start_time:
                    st.error("❌ 实际结束时间必须在实际开始时间之后")
                    time_module.sleep(0.1)
                    st.rerun()

            # 精力水平和时长显示 - 2列布局
            info_cols = st.columns(2)
            with info_cols[0]:
                # 从 session_state 获取精力水平 - 添加回调
                task_energy = st.select_slider(
                    "结束后精力", 
                    options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                    value=st.session_state.get(f"energy_input_{i}", saved_actual.get('post_energy', 7)),
                    key=f"energy_input_{i}",
                    on_change=lambda i=i, task=task: update_actual_execution_data(i, task, current_date)
                )
            
            with info_cols[1]:
                # 计算实际时长
                start_dt = datetime.combine(current_date, actual_start_time)
                end_dt = datetime.combine(current_date, actual_end_time)
                actual_duration = calculate_duration(start_dt, end_dt)
                st.markdown(f"##### 实际学习时长: {actual_duration}分钟")

        # === 反思和操作区域 ===
        st.markdown(f"##### 📝 学习反思")

        # 暂存按钮
        st.button("💾 暂存当前进度", use_container_width=True)
        
        # 反思框
        current_reflection_value = st.session_state.get('current_reflection', "")
        current_reflection = st.text_area(
            "今日反思", 
            value=current_reflection_value,
            placeholder="今天的收获和改进点...", 
            key="reflection_input"
        )
        # 反思内容变化时智能保存
        if (current_reflection != st.session_state.get('current_reflection') and 
            current_reflection.strip()):
            st.session_state.current_reflection = current_reflection
            github_state_manager.auto_save_state()
        
        # 最终提交按钮
        st.markdown(f"##### 完成记录")
        if st.session_state.get('tasks_saved', False):
            st.success("✅ 今日记录已保存，不可再修改")
            st.button("✅ 今日记录已保存", disabled=True, use_container_width=True)
        else:
            submitted = st.button("💾 保存今日记录", use_container_width=True)
            if submitted:
                # 重新处理计划任务数据确保最新
                planned_tasks = process_all_task_data(task_count, current_date)
                st.session_state.planned_tasks = planned_tasks
                
                # 处理实际执行数据
                actual_execution_for_save = []
                for i, task in enumerate(sorted_tasks):
                    actual_start_time = st.session_state.get(f"actual_start_{i}", parse_time(task['planned_start_time']))
                    actual_end_time = st.session_state.get(f"actual_end_{i}", parse_time(task['planned_end_time']))
                    task_energy = st.session_state.get(f"energy_input_{i}", 7)
                    
                    start_dt = datetime.combine(current_date, actual_start_time)
                    end_dt = datetime.combine(current_date, actual_end_time)
                    actual_duration = calculate_duration(start_dt, end_dt)
                    
                    actual_data = {
                        "task_id": task['task_id'],
                        "actual_start_time": actual_start_time,
                        "actual_end_time": actual_end_time,
                        "actual_duration": actual_duration,
                        "actual_focus_duration": int(actual_duration * 0.8),
                        "post_energy": task_energy,
                        "completed": True
                    }
                    actual_execution_for_save.append(actual_data)
                
                st.session_state.actual_execution = actual_execution_for_save
                st.session_state.tasks_saved = True
                github_state_manager.auto_save_state()
                
                # 保存到数据管理器
                try:
                    # 确保数据格式正确
                    planned_tasks_for_save = []
                    for task in sorted_tasks:
                        task_copy = task.copy()
                        if 'planned_start_time' in task_copy:
                            task_copy['planned_start_time'] = parse_time(task_copy['planned_start_time']).strftime('%H:%M')
                        if 'planned_end_time' in task_copy:
                            task_copy['planned_end_time'] = parse_time(task_copy['planned_end_time']).strftime('%H:%M')
                        planned_tasks_for_save.append(task_copy)
                    
                    actual_execution_for_save_formatted = []
                    for execution in actual_execution_for_save:
                        exec_copy = execution.copy()
                        # 确保时间是字符串格式
                        if 'actual_start_time' in exec_copy:
                            exec_copy['actual_start_time'] = parse_time(exec_copy['actual_start_time']).strftime('%H:%M')
                        if 'actual_end_time' in exec_copy:
                            exec_copy['actual_end_time'] = parse_time(exec_copy['actual_end_time']).strftime('%H:%M')
                        actual_execution_for_save_formatted.append(exec_copy)
                    
                    success = data_manager.add_daily_record(
                        current_date.strftime("%Y-%m-%d"),
                        current_weather,
                        current_energy_level,
                        planned_tasks_for_save,
                        actual_execution_for_save_formatted,
                        {
                            "planned_total_time": sum(t['planned_duration'] for t in planned_tasks),
                            "actual_total_time": sum(t['actual_duration'] for t in actual_execution_for_save),
                            "planned_focus_time": sum(t['planned_focus_duration'] for t in planned_tasks),
                            "actual_focus_time": sum(t['actual_focus_duration'] for t in actual_execution_for_save),
                            "completion_rate": len(actual_execution_for_save) / len(planned_tasks) if planned_tasks else 0,
                            "reflection": current_reflection
                        }
                    )
                    
                    if success:
                        st.balloons()
                        state_info = github_state_manager.get_state_info()
                        if state_info['date_status'] == 'today':
                            st.success("🎉 今日记录保存成功！")
                        elif state_info['date_status'] == 'future':
                            st.success(f"🎉 {current_date} 的未来计划保存成功！")
                        else:
                            st.success(f"🎉 {current_date} 的记录保存成功！")
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

# ==================== AI 助手页面 ====================
elif page == "AI 助手":
    st.title("🤖 AI 学习助手")
    st.markdown("与 AI 助手对话，获取学习分析、建议和智能计划")
    
    # 初始化 Agent（带数据管理器）
    if 'study_agent' not in st.session_state:
        st.session_state.study_agent = StudyAgent(data_manager)
    else:
        # 确保数据管理器已设置
        st.session_state.study_agent.set_data_manager(data_manager)
    
    # 初始化对话历史显示
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # ==================== 一键生成计划功能 ====================
    st.markdown("### 🎯 一键生成今日计划")
    
    plan_cols = st.columns([2, 1, 1, 1])
    with plan_cols[0]:
        plan_hours = st.slider("计划学习时长（小时）", 1, 8, 4, key="ai_plan_hours")
    with plan_cols[1]:
        focus_options = {"无": None, "数学": "math", "物理": "physics", "经济": "econ", "计算机": "cs"}
        focus_label = st.selectbox("重点学科", list(focus_options.keys()), key="ai_focus_subject")
        focus_subject = focus_options[focus_label]
    with plan_cols[2]:
        plan_date_option = st.selectbox("计划日期", ["今天", "明天"], key="ai_plan_date")
    with plan_cols[3]:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        generate_and_apply = st.button("🚀 生成并应用", type="primary", use_container_width=True)
    
    if generate_and_apply:
        # 确定计划日期
        if plan_date_option == "今天":
            target_date = datetime.now().date()
        else:
            target_date = (datetime.now() + timedelta(days=1)).date()
        
        with st.spinner("🤖 AI 正在分析历史数据并生成最优计划..."):
            # 使用工具生成计划
            from tools import StudyTools
            tools = StudyTools(data_manager)
            plan_result = tools.generate_smart_plan(
                date=target_date.isoformat(),
                total_hours=plan_hours,
                focus_subject=focus_subject
            )
        
        if plan_result['success']:
            plan_data = plan_result['data']
            tasks = plan_data['tasks']
            
            # 转换为应用格式
            planned_tasks = []
            for i, task in enumerate(tasks):
                # 解析时间
                start_parts = task['start_time'].split(':')
                end_parts = task['end_time'].split(':')
                start_time_obj = time(int(start_parts[0]), int(start_parts[1]))
                end_time_obj = time(int(end_parts[0]), int(end_parts[1]))
                
                planned_tasks.append({
                    'task_id': i + 1,
                    'task_name': f"{task['subject_name']}学习",
                    'subject': task['subject'],
                    'difficulty': task.get('difficulty', 3),
                    'planned_start_time': start_time_obj,
                    'planned_end_time': end_time_obj,
                    'planned_duration': task['duration_minutes'],
                    'planned_focus_duration': int(task['duration_minutes'] * 0.8)
                })
            
            # 应用到 session state
            st.session_state.current_date = target_date
            st.session_state.planned_tasks = planned_tasks
            st.session_state.tasks_confirmed = False
            st.session_state.tasks_saved = False
            st.session_state.show_final_confirmation = False
            st.session_state.expander_expanded = True
            st.session_state.actual_execution = []
            
            # 更新表单组件状态
            for i, task in enumerate(planned_tasks):
                st.session_state[f"task_name_{i}"] = task['task_name']
                st.session_state[f"subject_{i}"] = task['subject']
                st.session_state[f"difficulty_{i}"] = task['difficulty']
                st.session_state[f"start_{i}"] = task['planned_start_time']
                st.session_state[f"end_{i}"] = task['planned_end_time']
            
            # 保存到 GitHub
            github_state_manager.auto_save_state(force=True)
            
            st.success(f"✅ 已生成 {len(tasks)} 个任务，总计 {plan_hours} 小时！")
            st.info("💡 请前往「今日记录」页面查看和确认计划")
            
            # 显示生成的计划预览
            with st.expander("📋 计划预览", expanded=True):
                for task in tasks:
                    st.markdown(f"- **{task['subject_name']}**: {task['start_time']} - {task['end_time']} ({task['duration_minutes']}分钟)")
                if plan_data.get('tips'):
                    st.markdown("**💡 提示：**")
                    for tip in plan_data['tips']:
                        st.markdown(f"- {tip}")
        else:
            st.error(f"生成失败: {plan_result['message']}")
    
    st.markdown("---")
    
    # 功能提示卡片
    with st.expander("💡 我能帮你做什么？", expanded=len(st.session_state.chat_messages) == 0):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📊 数据查询**
            - "我上周学了多少小时？"
            - "查看最近7天的学习记录"
            - "2025-01-03 我学了什么？"
            
            **📈 效率分析**
            - "分析我的学习模式"
            - "哪个学科效率最高？"
            - "我的完成率怎么样？"
            """)
        with col2:
            st.markdown("""
            **📅 智能规划**
            - "帮我规划明天的学习"
            - "生成一个3小时的学习计划"
            - "重点安排数学和物理"
            
            **💡 改进建议**
            - "给我一些学习建议"
            - "如何提高效率？"
            - "时间管理有什么问题？"
            """)
    
    # 快捷操作按钮
    st.markdown("##### ⚡ 快捷操作")
    quick_cols = st.columns(4)
    
    quick_prompts = [
        ("📊 周统计", "帮我看看这周的学习统计数据"),
        ("📈 效率分析", "分析一下我最近的学习效率和模式"),
        ("📅 生成计划", "基于我的历史数据，帮我规划明天的学习"),
        ("💡 给点建议", "根据我的学习数据，给我一些改进建议")
    ]
    
    for i, (label, prompt) in enumerate(quick_prompts):
        with quick_cols[i]:
            if st.button(label, use_container_width=True, key=f"quick_{i}"):
                st.session_state.pending_prompt = prompt
                st.rerun()
    
    st.markdown("---")
    
    # 显示对话历史
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message["content"])
    
    # 处理待处理的快捷提示
    if 'pending_prompt' in st.session_state:
        prompt = st.session_state.pending_prompt
        del st.session_state.pending_prompt
        
        # 添加用户消息
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # 获取 AI 回复
        with st.spinner("🤔 AI 正在思考..."):
            response = st.session_state.study_agent.chat(prompt)
        
        # 添加助手回复
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()
    
    # 用户输入
    user_input = st.chat_input("输入你的问题...", key="chat_input")
    
    if user_input:
        # 添加用户消息
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        
        # 显示用户消息
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        
        # 获取 AI 回复
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤔 AI 正在分析..."):
                response = st.session_state.study_agent.chat(user_input)
            st.markdown(response)
        
        # 保存助手回复
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    # 清空对话按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.chat_messages = []
            st.session_state.study_agent.clear_history()
            st.rerun()
    with col2:
        if st.button("🔄 重置 Agent", use_container_width=True):
            st.session_state.study_agent = StudyAgent(data_manager)
            st.session_state.chat_messages = []
            st.success("Agent 已重置")
            st.rerun()
    
    # 显示 Agent 信息
    with st.expander("🔧 Agent 信息"):
        st.markdown(f"""
        **模型**: `{st.session_state.study_agent.model_name}`
        
        **可用工具**:
        - `get_weekly_stats` - 获取学习统计
        - `get_subject_analysis` - 学科分析
        - `query_history` - 查询历史
        - `generate_smart_plan` - 生成计划
        - `analyze_learning_pattern` - 分析模式
        - `get_improvement_suggestions` - 改进建议
        
        **对话轮数**: {len(st.session_state.chat_messages) // 2}
        """)

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

    st.markdown("---")
    st.subheader("🗑️ 数据清理")
    
    # 显示数据统计
    stats = github_state_manager.get_data_stats()
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("状态数据", stats['state_count'])
    with col2:
        st.metric("学习记录", stats['study_data_count'])
    with col3:
        st.metric("旧状态数据", stats['old_states'])
    with col4:
        st.metric("旧学习记录", stats['old_study_data'])
    with col5:
        st.metric("缓存大小", f"{stats['cache_size']}B")
    
    # 清理选项
    st.markdown("#### 清理选项")
    
    tab1, tab2, tab3 = st.tabs(["清理旧数据", "清除缓存", "清除所有数据"])
    
    with tab1:
        st.markdown("**清理指定天数前的数据**")
        days_to_keep = st.slider("保留最近多少天的数据", 7, 365, 30, key="days_keep")
        if st.button("🧹 清理旧数据", key="clean_old", help=f"删除{days_to_keep}天前的数据"):
            if github_state_manager.cleanup_data(days_to_keep=days_to_keep):
                st.rerun()
    
    with tab2:
        st.markdown("**只清除缓存数据**")
        st.info("这将清除时间输入缓存和除今天外的所有状态数据")
        if st.button("🔄 清除缓存", key="clear_cache"):
            if github_state_manager.cleanup_data(clear_cache=True):
                st.rerun()
    
    with tab3:
        st.markdown("**清除所有数据（危险操作）**")
        st.warning("⚠️ 这将删除所有学习记录、状态数据和缓存，此操作不可恢复！")
        
        col1, col2 = st.columns(2)
        with col1:
            confirm1 = st.checkbox("我理解此操作会永久删除所有数据", key="confirm1")
        with col2:
            confirm2 = st.checkbox("我确认要执行此操作", key="confirm2")
        
        if confirm1 and confirm2:
            if st.button("🗑️ 确认删除所有数据", type="primary", key="delete_all"):
                if github_state_manager.cleanup_data(clear_all=True):
                    st.rerun()
        else:
            st.button("🗑️ 确认删除所有数据", disabled=True)
    
    st.info("💡 建议定期清理缓存和旧数据以保持应用性能")

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
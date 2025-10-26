import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
from data_manager import StudyDataManager
from study_agent import StudyAgent

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

# 页面设置
st.set_page_config(
    page_title="学习分析仪表板",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化管理器
@st.cache_resource
def get_data_manager():
    return StudyDataManager()

@st.cache_resource
def get_agent():
    return StudyAgent()

data_manager = get_data_manager()
agent = get_agent()

# 侧边栏导航
st.sidebar.title("📚 学习分析系统")
page = st.sidebar.selectbox("导航", ["今日记录", "数据看板", "智能分析", "历史数据"])

# 主题颜色
primary_color = "#1f77b4"

def calculate_duration(start_time, end_time):
    """计算两个时间之间的时长（分钟）"""
    if start_time and end_time:
        duration = (end_time - start_time).total_seconds() / 60
        return max(0, int(duration))
    return 0

# 页面1: 今日记录
if page == "今日记录":
    st.title("📝 今日学习记录")
    
    # 初始化session state来存储任务时间
    if 'task_times' not in st.session_state:
        st.session_state.task_times = {}
    
    with st.form("daily_record"):
        col1, col2, col3 = st.columns(3)
        with col1:
            date = st.date_input("日期", datetime.now())
        with col2:
            weather = st.selectbox("天气", ["晴", "多云", "雨", "阴", "雪"])
        with col3:
            energy_level = st.slider("精力水平", 1, 10, 7)
        
        st.subheader("今日计划任务")
        planned_tasks = []

        # 初始化展开状态
        if 'expander_expanded' not in st.session_state:
            st.session_state.expander_expanded = True

        with st.expander("添加计划任务", expanded=st.session_state.expander_expanded):
            task_count = st.number_input("任务数量", min_value=1, max_value=10, value=3)
            
            for i in range(task_count):
                st.markdown(f"**任务 {i+1}**")
                
                # 单行布局：任务基本信息 + 时间设置
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
                
                with col1:
                    task_name = st.text_input(
                        "任务名称", 
                        key=f"task_name_{i}", 
                        placeholder="如：群论复习",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    subject = st.selectbox(
                        "学科", 
                        ["math", "physics", "econ", "cs", "other"], 
                        key=f"subject_{i}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    difficulty = st.selectbox(
                        "难度", 
                        [1, 2, 3, 4, 5], 
                        index=2,
                        key=f"difficulty_{i}",
                        label_visibility="collapsed"
                    )
                
                with col4:
                    start_time = st.time_input(
                        "开始时间", 
                        value=datetime.now().time().replace(hour=9, minute=0),
                        key=f"start_{i}",
                        step=300,
                        label_visibility="collapsed"
                    )
                
                with col5:
                    # 获取当前结束时间值
                    current_end_time = st.session_state.get(f"end_{i}", datetime.now().time().replace(hour=10, minute=0))
                    
                    # 如果结束时间在开始时间之前，自动调整
                    if current_end_time <= start_time:
                        # 自动设置为开始时间+30分钟
                        adjusted_end = (datetime.combine(date, start_time) + timedelta(minutes=30)).time()
                        # 更新session state
                        st.session_state[f"end_{i}"] = adjusted_end
                        current_end_time = adjusted_end
                    
                    end_time = st.time_input(
                        "结束时间", 
                        value=current_end_time,
                        key=f"end_{i}",
                        step=300,
                        label_visibility="collapsed"
                    )
                    
                    # 实时验证
                    if end_time <= start_time:
                        st.error("❌ 结束时间必须在开始时间之后")
                        # 强制调整
                        forced_end = (datetime.combine(date, start_time) + timedelta(minutes=30)).time()
                        st.session_state[f"end_{i}"] = forced_end
                        st.rerun()  # 重新运行以更新界面

                with col6:
                    st.write("")  # 占位

                with col7:
                    st.write("")  # 占位
                    st.write("")  # 占位
                    # 删除按钮
                    #if st.button("🗑️", key=f"delete_{i}", help="删除此任务", use_container_width=True):
                    #    # 这里可以添加删除逻辑
                     #   pass
                
                # 显示标签说明（在下方）
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
                    st.write("")
                with col_labels[6]:
                    st.write("")

                # 计算时长
                start_dt = datetime.combine(date, start_time)
                end_dt = datetime.combine(date, end_time)
                calculated_duration = calculate_duration(start_dt, end_dt)

                if task_name:
                    planned_tasks.append({
                        "task_id": i+1,
                        "task_name": task_name,
                        "subject": subject,
                        "planned_duration": calculated_duration,  # 使用计算出的时长
                        "planned_focus_duration": int(calculated_duration * 0.8),
                        "difficulty": difficulty,
                        "planned_start_time": start_time.strftime('%H:%M'),
                        "planned_end_time": end_time.strftime('%H:%M')
                    })
                
                st.markdown("---")

            # 在任务循环结束后添加计划任务提交按钮
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # 初始化session state
                if 'tasks_confirmed' not in st.session_state:
                    st.session_state.tasks_confirmed = False
                if 'show_final_confirmation' not in st.session_state:
                    st.session_state.show_final_confirmation = False
                
                # 如果任务已经确认，显示已确认状态
                if st.session_state.tasks_confirmed:
                    st.success("✅ 计划任务已确认，不可再修改")
                    # 显示禁用的按钮
                    disabled_btn = st.form_submit_button(
                        "✅ 计划任务已确认",
                        disabled=True,
                        use_container_width=True,
                        help="计划任务已确认，不可再修改"
                    )
                
                # 如果正在显示最终确认，不显示原始确认按钮
                elif st.session_state.show_final_confirmation:
                    # 显示最终确认区域
                    st.warning("⚠️ 请最终确认计划任务")
                    st.info("确认后将无法再修改计划任务")
                    
                    confirm_col1, confirm_col2, confirm_col3 = st.columns([1, 1, 1])
                    with confirm_col1:
                        # 取消按钮
                        cancel_confirm = st.form_submit_button(
                            "❌ 取消",
                            type="secondary",
                            use_container_width=True
                        )
                        if cancel_confirm:
                            st.session_state.show_final_confirmation = False
                            st.rerun()
                            
                    with confirm_col2:
                        # 最终确认按钮
                        final_confirm = st.form_submit_button(
                            "🔒 最终确认",
                            type="primary",
                            use_container_width=True
                        )
                        if final_confirm:
                            st.session_state.tasks_confirmed = True
                            st.session_state.show_final_confirmation = False
                            st.success(f"✅ 已确认 {len(planned_tasks)} 个计划任务！")
                            st.session_state.expander_expanded = False
                            st.rerun()
                
                # 初始状态：显示原始确认按钮
                else:
                    submit_planned_tasks = st.form_submit_button(
                        "✅ 确认计划任务",
                        type="primary",
                        use_container_width=True,
                        help="确认并保存以上计划任务"
                    )
                    
                    if submit_planned_tasks:
                        if planned_tasks:
                            # 验证任务时间不重叠
                            time_conflicts = check_time_conflicts(planned_tasks, date)
                            
                            if time_conflicts:
                                st.error("❌ 存在时间冲突的任务，请调整：")
                                for conflict in time_conflicts:
                                    st.error(f"- {conflict}")
                            else:
                                # 进入最终确认状态
                                st.session_state.show_final_confirmation = True                               
                                st.rerun()
                        else:
                            st.warning("⚠️ 请至少填写一个任务名称")
        

        # 显示今日时间线概览
        if planned_tasks and st.session_state.tasks_confirmed:
            st.subheader("📅 今日计划时间线")
            # st.expander("添加计划任务", expanded=False)

            # 创建时间线数据
            timeline_data = []
            current_date = date
            

            for task in planned_tasks:
                start_dt = datetime.combine(current_date, datetime.strptime(task['planned_start_time'], '%H:%M').time())
                end_dt = datetime.combine(current_date, datetime.strptime(task['planned_end_time'], '%H:%M').time())
                calculated_duration = calculate_duration(start_dt, end_dt)

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
        
            st.subheader("实际执行情况")
            actual_execution = []

            # 按照开始时间排序
            sorted_tasks = sorted(planned_tasks, key=lambda x: datetime.strptime(x['planned_start_time'], '%H:%M'))

            for i, task in enumerate(sorted_tasks):
                st.markdown(f"**{task['task_name']}**")
                
                # 执行情况输入 - 使用紧凑布局
                col1, col2, col3 = st.columns([2, 2, 2])
                
                with col1:
                    # 初始化实际开始时间（只在第一次运行时）
                    #start_key = f'actual_start_{i}'
                    #if start_key not in st.session_state:
                    #    st.session_state[start_key] = datetime.strptime(task['planned_start_time'], '%H:%M').time()
                    
                    actual_start_time = st.time_input(
                        "实际开始时间",
                        value=datetime.strptime(task['planned_start_time'], '%H:%M').time(),
                        key=f"actual_start_{i}",  # 使用不同的key
                        step=300
                    )
                
                with col2:
                    # 获取当前实际结束时间值
                    current_actual_end_time = st.session_state.get(f"actual_end_{i}", datetime.strptime(task['planned_end_time'], '%H:%M').time())
                    
                    # 如果实际结束时间在实际开始时间之前，自动调整
                    start_dt = datetime.combine(date, actual_start_time)
                    end_dt = datetime.combine(date, current_actual_end_time)
                    
                    actual_end_time = st.time_input(
                        "实际结束时间",
                        value=current_actual_end_time,
                        key=f"actual_end_{i}",
                        step=300,
                    )
                    
                    # 实时验证
                    start_dt = datetime.combine(date, actual_start_time)
                    end_dt = datetime.combine(date, actual_end_time)
                    
                    if end_dt <= start_dt:
                        st.error("❌ 实际结束时间必须在实际开始时间之后")
                        # 强制调整
                        time.sleep(0.1)  # 确保状态更新
                        st.rerun()  # 重新运行以更新界面


                with col3:
                    # 初始化精力水平
                    energy_key = f'energy_{i}'
                    if energy_key not in st.session_state:
                        st.session_state[energy_key] = 7
                        
                    task_energy = st.select_slider(
                        "结束后精力", 
                        options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                        value=st.session_state[energy_key],
                        key=f"energy_input_{i}"  # 使用不同的key
                    )

                # 计算实际时长（只有在时间有效时）
                start_dt = datetime.combine(date, actual_start_time)
                end_dt = datetime.combine(date, actual_end_time)
                
                if start_dt < end_dt:
                    actual_duration = calculate_duration(start_dt, end_dt)
                    
                    # 显示实际时长信息
                    st.caption(f"实际学习时长: {actual_duration}分钟")
                    
                    # 添加到执行记录
                    actual_execution.append({
                        "task_id": task['task_id'],
                        "actual_start_time": actual_start_time.strftime('%H:%M'),
                        "actual_end_time": actual_end_time.strftime('%H:%M'),
                        "actual_duration": actual_duration,
                        "actual_focus_duration": int(actual_duration * 0.8),
                        "post_energy": task_energy,
                        "completed": True
                    })
                else:
                    st.warning("⚠️ 请调整时间以确保结束时间在开始时间之后")

                st.markdown("---")
            
            # 提交按钮
            submitted = st.form_submit_button("💾 保存今日记录")
            if submitted:
                if planned_tasks:
                    # 计算每日摘要
                    planned_total = sum(t['planned_duration'] for t in planned_tasks)
                    actual_total = sum(t['actual_duration'] for t in actual_execution) if actual_execution else 0
                    completion_rate = len(actual_execution) / len(planned_tasks) if planned_tasks else 0
                    
                    daily_summary = {
                        "planned_total_time": planned_total,
                        "actual_total_time": actual_total,
                        "planned_focus_time": sum(t['planned_focus_duration'] for t in planned_tasks),
                        "actual_focus_time": sum(t['actual_focus_duration'] for t in actual_execution) if actual_execution else 0,
                        "completion_rate": completion_rate,
                        "reflection": st.text_area("今日反思", placeholder="今天的收获和改进点...", key="reflection")
                    }
                    
                    # 保存数据
                    success = data_manager.add_daily_record(
                        date.strftime("%Y-%m-%d"),
                        weather,
                        energy_level,
                        sorted_tasks, # 使用排序后的任务
                        actual_execution,
                        daily_summary
                    )
                    
                    if success:
                        st.success("✅ 今日记录保存成功！")
                        # 清空时间记录
                        st.session_state.task_times = {}
                        st.balloons()
                    else:
                        st.error("❌ 保存失败，请检查数据格式")
                else:
                    st.error("❌ 请至少添加一个计划任务")

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
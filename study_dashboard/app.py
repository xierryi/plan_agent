import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from data_manager import StudyDataManager
from study_agent import StudyAgent

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
        if end_time < start_time:
            # 如果结束时间在开始时间之前，假设是跨天的情况
            end_time += timedelta(days=1)
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
        
        with st.expander("添加计划任务", expanded=True):
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
                    # 计算并显示时长
                    start_dt = datetime.combine(date, start_time)
                    end_dt = datetime.combine(date, end_time)
                    calculated_duration = calculate_duration(start_dt, end_dt)
                    
                    # 自动更新session state
                    st.session_state.task_times[i] = {
                        'start_time': start_time,
                        'end_time': end_time,
                        'calculated_duration': calculated_duration
                    }
                    
                    # 显示时长（只读）
                    st.text_input(
                        "时长", 
                        value=f"{calculated_duration}分钟",
                        key=f"duration_display_{i}",
                        label_visibility="collapsed",
                        disabled=True
                    )

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
                    st.caption("时长")
                with col_labels[6]:
                    st.caption("操作")
                
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
        
        # 显示今日时间线概览
        if planned_tasks:
            st.subheader("📅 今日计划时间线")
            
            # 创建时间线数据
            timeline_data = []
            current_date = date
            
            for task in planned_tasks:
                start_dt = datetime.combine(current_date, datetime.strptime(task['planned_start_time'], '%H:%M').time())
                end_dt = datetime.combine(current_date, datetime.strptime(task['planned_end_time'], '%H:%M').time())
                
                # 处理跨天情况
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)
                
                timeline_data.append({
                    'Task': task['task_name'],
                    'Start': start_dt,
                    'Finish': end_dt,
                    'Duration': f"{task['planned_duration']}分钟",
                    'Subject': task['subject'],
                    'Difficulty': task['difficulty']
                })
            
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
        
        for i, task in enumerate(planned_tasks):
            st.markdown(f"**{task['task_name']}**")
            
            # 执行情况输入 - 使用紧凑布局
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            with col1:
                completed = st.checkbox("已完成", value=True, key=f"completed_{i}")
            with col2:
                # 实际时长可以调整，默认为计划时长
                actual_duration = st.number_input(
                    "实际时长", 
                    min_value=0, 
                    max_value=480, 
                    value=task['planned_duration'], 
                    key=f"actual_dur_{i}"
                )
            with col3:
                interruptions = st.number_input(
                    "中断次数", 
                    min_value=0, 
                    max_value=10, 
                    value=0,
                    key=f"inter_{i}"
                )
            with col4:
                task_energy = st.select_slider(
                    "任务后精力", 
                    options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                    value=7,
                    key=f"energy_{i}"
                )
            
            if completed:
                actual_execution.append({
                    "task_id": task['task_id'],
                    "actual_duration": actual_duration,
                    "actual_focus_duration": int(actual_duration * 0.8),
                    "interruptions": interruptions,
                    "post_energy": task_energy,
                    "completed": True
                })
            
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
                    planned_tasks,
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

# 其他页面保持不变...
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
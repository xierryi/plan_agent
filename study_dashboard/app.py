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

# 页面1: 今日记录
if page == "今日记录":
    st.title("📝 今日学习记录")
    
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
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    task_name = st.text_input(f"任务名称", key=f"task_name_{i}", placeholder="如：群论复习")
                with col2:
                    subject = st.selectbox("学科", ["math", "physics", "econ", "cs", "other"], key=f"subject_{i}")
                with col3:
                    planned_duration = st.number_input("计划时长(分)", min_value=15, max_value=240, value=60, key=f"duration_{i}")
                with col4:
                    difficulty = st.slider("难度", 1, 5, 3, key=f"difficulty_{i}")
                
                if task_name:
                    planned_tasks.append({
                        "task_id": i+1,
                        "task_name": task_name,
                        "subject": subject,
                        "planned_duration": planned_duration,
                        "planned_focus_duration": int(planned_duration * 0.8),
                        "difficulty": difficulty
                    })
        
        st.subheader("实际执行情况")
        actual_execution = []
        
        for i, task in enumerate(planned_tasks):
            st.markdown(f"**{task['task_name']}**")
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            with col1:
                completed = st.checkbox("已完成", value=True, key=f"completed_{i}")
            with col2:
                actual_duration = st.number_input("实际时长", min_value=0, max_value=240, 
                                                value=task['planned_duration'], key=f"actual_dur_{i}")
            with col3:
                interruptions = st.number_input("中断次数", min_value=0, max_value=10, key=f"inter_{i}")
            with col4:
                task_energy = st.slider("任务后精力", 1, 10, 7, key=f"energy_{i}")
            
            if completed:
                actual_execution.append({
                    "task_id": task['task_id'],
                    "actual_duration": actual_duration,
                    "actual_focus_duration": int(actual_duration * 0.8),
                    "interruptions": interruptions,
                    "post_energy": task_energy,
                    "completed": True
                })
        
        # 提交按钮
        submitted = st.form_submit_button("保存今日记录")
        if submitted:
            if planned_tasks and actual_execution:
                # 计算每日摘要
                planned_total = sum(t['planned_duration'] for t in planned_tasks)
                actual_total = sum(t['actual_duration'] for t in actual_execution)
                completion_rate = len(actual_execution) / len(planned_tasks)
                
                daily_summary = {
                    "planned_total_time": planned_total,
                    "actual_total_time": actual_total,
                    "planned_focus_time": sum(t['planned_focus_duration'] for t in planned_tasks),
                    "actual_focus_time": sum(t['actual_focus_duration'] for t in actual_execution),
                    "completion_rate": completion_rate,
                    "reflection": st.text_area("今日反思", placeholder="今天的收获和改进点...")
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
                    st.balloons()
            else:
                st.error("请至少添加一个计划任务并记录执行情况")

# 页面2: 数据看板
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

# 环境配置提示
with st.sidebar.expander("环境配置"):
    st.code("""
# 安装依赖
pip install -r requirements.txt

# 设置API密钥（可选，用于智能分析）
echo "OPENAI_API_KEY=your_key_here" > .env

# 运行应用
streamlit run app.py
""")

if __name__ == "__main__":
    pass
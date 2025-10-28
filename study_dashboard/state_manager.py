import streamlit as st
import json
from datetime import datetime, date
import copy

class StateManager:
    """状态管理器 - 最优解决方案"""
    
    @staticmethod
    def init_session_state():
        """初始化所有 session state 变量"""
        default_states = {
            # 任务状态
            'tasks_confirmed': False,
            'show_final_confirmation': False,
            'tasks_saved': False,
            'expander_expanded': True,
            
            # 表单数据
            'current_date': datetime.now().date(),
            'current_weather': "晴",
            'current_energy_level': 7,
            'current_reflection': "",
            
            # 任务数据
            'planned_tasks': [],
            'actual_execution': [],
            
            # 时间数据缓存
            'time_inputs_cache': {},
            
            # 最后保存时间戳
            'last_auto_save': None
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def auto_save_state():
        """自动保存当前所有状态"""
        save_data = {
            # 任务状态
            'tasks_confirmed': st.session_state.tasks_confirmed,
            'show_final_confirmation': st.session_state.show_final_confirmation,
            'tasks_saved': st.session_state.tasks_saved,
            'expander_expanded': st.session_state.expander_expanded,
            
            # 表单数据
            'current_date': st.session_state.current_date.isoformat(),
            'current_weather': st.session_state.current_weather,
            'current_energy_level': st.session_state.current_energy_level,
            'current_reflection': st.session_state.current_reflection,
            
            # 任务数据
            'planned_tasks': copy.deepcopy(st.session_state.planned_tasks),
            'actual_execution': copy.deepcopy(st.session_state.actual_execution),
            
            # 时间数据缓存
            'time_inputs_cache': copy.deepcopy(st.session_state.time_inputs_cache),
            
            # 时间戳
            'last_auto_save': datetime.now().isoformat()
        }
        
        # 保存到 session state
        st.session_state.auto_saved_data = save_data
        st.session_state.last_auto_save = datetime.now()
    
    @staticmethod
    def restore_state():
        """恢复之前保存的状态"""
        if 'auto_saved_data' in st.session_state:
            saved_data = st.session_state.auto_saved_data
            
            # 恢复任务状态
            st.session_state.tasks_confirmed = saved_data.get('tasks_confirmed', False)
            st.session_state.show_final_confirmation = saved_data.get('show_final_confirmation', False)
            st.session_state.tasks_saved = saved_data.get('tasks_saved', False)
            st.session_state.expander_expanded = saved_data.get('expander_expanded', True)
            
            # 恢复表单数据
            if 'current_date' in saved_data:
                st.session_state.current_date = date.fromisoformat(saved_data['current_date'])
            st.session_state.current_weather = saved_data.get('current_weather', "晴")
            st.session_state.current_energy_level = saved_data.get('current_energy_level', 7)
            st.session_state.current_reflection = saved_data.get('current_reflection', "")
            
            # 恢复任务数据
            st.session_state.planned_tasks = saved_data.get('planned_tasks', [])
            st.session_state.actual_execution = saved_data.get('actual_execution', [])
            
            # 恢复时间缓存
            st.session_state.time_inputs_cache = saved_data.get('time_inputs_cache', {})
            
            return True
        return False
    
    @staticmethod
    def clear_state():
        """清除所有状态（用于新的一天）"""
        keys_to_clear = [
            'tasks_confirmed', 'show_final_confirmation', 'tasks_saved',
            'expander_expanded', 'planned_tasks', 'actual_execution',
            'time_inputs_cache', 'current_reflection'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # 重新初始化
        StateManager.init_session_state()

# 在页面配置后立即初始化
StateManager.init_session_state()

# 在主要页面逻辑开始前恢复状态
StateManager.restore_state()
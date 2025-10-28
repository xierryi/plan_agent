# github_state_manager.py
import streamlit as st
import json
from datetime import datetime
from github_manager import GitHubDataManager

class GitHubStateManager:
    """使用 GitHub 作为持久化存储的状态管理器 - 仅保留当天状态"""
    
    def __init__(self):
        self.github_manager = GitHubDataManager()
        self.state_key = "daily_session_state"
        self.initialized = False
    
    def init_session_state(self):
        """初始化所有 session state 变量"""
        if self.initialized:
            return
            
        # 先尝试从 GitHub 加载当天状态
        today = datetime.now().date().isoformat()
        if self.load_from_github(today):
            st.sidebar.success("✅ 当天状态已恢复")
            self.initialized = True
            return
            
        # 否则使用默认值
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
            'last_auto_save': None,
            
            # 状态日期标识
            'state_date': today
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        self.initialized = True
        st.sidebar.info("🆕 新的一天开始")
    
    def auto_save_state(self):
        """自动保存当天状态到 GitHub"""
        try:
            today = datetime.now().date().isoformat()
            
            # 检查是否是同一天，如果不是则清除旧状态
            if st.session_state.get('state_date') != today:
                self._clear_previous_day_state()
                st.session_state.state_date = today
            
            save_data = self._prepare_save_data()
            success = self._save_to_github(today, save_data)
            
            if success:
                st.session_state.last_auto_save = datetime.now()
                return True
            else:
                return False
                
        except Exception as e:
            st.sidebar.error(f"❌ 自动保存失败: {str(e)}")
            return False
    
    def _prepare_save_data(self):
        """准备保存数据（排除不需要持久化的字段）"""
        return {
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
            'planned_tasks': st.session_state.planned_tasks,
            'actual_execution': st.session_state.actual_execution,
            
            # 时间数据缓存
            'time_inputs_cache': st.session_state.time_inputs_cache,
            
            # 元数据
            'last_auto_save': datetime.now().isoformat(),
            'state_date': st.session_state.get('state_date', datetime.now().date().isoformat())
        }
    
    def _save_to_github(self, date_key, data):
        """保存状态数据到 GitHub"""
        if not self.github_manager.is_connected():
            # GitHub 不可用时，保存到 session state
            st.session_state.auto_saved_data = data
            return True
            
        try:
            # 加载所有状态数据
            all_states = self._load_all_states_from_github()
            
            # 移除当天的旧状态（如果存在）
            all_states = {k: v for k, v in all_states.items() if k != date_key}
            
            # 添加新状态
            all_states[date_key] = data
            
            # 只保留最近3天的状态作为备份（可选）
            self._cleanup_old_states(all_states)
            
            # 保存到 GitHub
            content = json.dumps(all_states, ensure_ascii=False, indent=2)
            return self._save_raw_to_github(content)
            
        except Exception as e:
            st.sidebar.warning(f"⚠️ GitHub 保存失败，使用 session state: {str(e)}")
            st.session_state.auto_saved_data = data
            return False
    
    def _load_all_states_from_github(self):
        """从 GitHub 加载所有状态数据"""
        if not self.github_manager.is_connected():
            return {}
            
        try:
            contents = self.github_manager.repo.get_contents(self.state_key)
            file_content = self.github_manager._decode_content(contents.content)
            return json.loads(file_content)
        except Exception:
            return {}
    
    def _save_raw_to_github(self, content):
        """原始保存到 GitHub"""
        try:
            # 检查文件是否存在
            try:
                contents = self.github_manager.repo.get_contents(self.state_key)
                # 更新文件
                self.github_manager.repo.update_file(
                    self.state_key,
                    f"更新会话状态 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content,
                    contents.sha
                )
            except Exception:
                # 创建新文件
                self.github_manager.repo.create_file(
                    self.state_key,
                    f"创建会话状态 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content
                )
            return True
        except Exception:
            return False
    
    def load_from_github(self, date_key):
        """从 GitHub 加载指定日期的状态"""
        if not self.github_manager.is_connected():
            return False
            
        try:
            all_states = self._load_all_states_from_github()
            
            if date_key in all_states:
                data = all_states[date_key]
                self._restore_from_data(data)
                return True
                
            return False
            
        except Exception as e:
            st.sidebar.warning(f"⚠️ 从 GitHub 加载状态失败: {str(e)}")
            return False
    
    def _restore_from_data(self, data):
        """从数据恢复状态"""
        if not data:
            return
            
        # 恢复任务状态
        st.session_state.tasks_confirmed = data.get('tasks_confirmed', False)
        st.session_state.show_final_confirmation = data.get('show_final_confirmation', False)
        st.session_state.tasks_saved = data.get('tasks_saved', False)
        st.session_state.expander_expanded = data.get('expander_expanded', True)
        
        # 恢复表单数据
        if 'current_date' in data:
            st.session_state.current_date = datetime.fromisoformat(data['current_date']).date()
        
        st.session_state.current_weather = data.get('current_weather', "晴")
        st.session_state.current_energy_level = data.get('current_energy_level', 7)
        st.session_state.current_reflection = data.get('current_reflection', "")
        
        # 恢复任务数据
        st.session_state.planned_tasks = data.get('planned_tasks', [])
        st.session_state.actual_execution = data.get('actual_execution', [])
        st.session_state.time_inputs_cache = data.get('time_inputs_cache', {})
        
        # 恢复状态日期
        st.session_state.state_date = data.get('state_date', datetime.now().date().isoformat())
        
        if 'last_auto_save' in data:
            st.session_state.last_auto_save = datetime.fromisoformat(data['last_auto_save'])
    
    def _clear_previous_day_state(self):
        """清除前一天的状态"""
        keys_to_clear = [
            'tasks_confirmed', 'show_final_confirmation', 'tasks_saved',
            'expander_expanded', 'planned_tasks', 'actual_execution',
            'time_inputs_cache', 'current_reflection', 'auto_saved_data'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def _cleanup_old_states(self, all_states):
        """清理旧的状态数据（只保留最近3天）"""
        try:
            # 按日期排序
            sorted_dates = sorted(all_states.keys(), reverse=True)
            
            # 只保留最近3天
            if len(sorted_dates) > 3:
                for old_date in sorted_dates[3:]:
                    del all_states[old_date]
                    
        except Exception:
            # 如果清理失败，不影响主要功能
            pass
    
    def clear_current_state(self):
        """清除当前状态（开始新的一天）"""
        today = datetime.now().date().isoformat()
        
        # 清除 session state
        self._clear_previous_day_state()
        
        # 重置为默认值
        st.session_state.tasks_confirmed = False
        st.session_state.show_final_confirmation = False
        st.session_state.tasks_saved = False
        st.session_state.expander_expanded = True
        st.session_state.current_date = datetime.now().date()
        st.session_state.current_weather = "晴"
        st.session_state.current_energy_level = 7
        st.session_state.current_reflection = ""
        st.session_state.planned_tasks = []
        st.session_state.actual_execution = []
        st.session_state.time_inputs_cache = {}
        st.session_state.state_date = today
        
        # 从 GitHub 删除当天状态
        if self.github_manager.is_connected():
            try:
                all_states = self._load_all_states_from_github()
                if today in all_states:
                    del all_states[today]
                    content = json.dumps(all_states, ensure_ascii=False, indent=2)
                    self._save_raw_to_github(content)
            except Exception:
                pass
        
        return True
    
    def get_state_info(self):
        """获取状态信息"""
        today = datetime.now().date().isoformat()
        is_today = st.session_state.get('state_date') == today
        
        return {
            'is_today': is_today,
            'state_date': st.session_state.get('state_date'),
            'has_planned_tasks': len(st.session_state.get('planned_tasks', [])) > 0,
            'tasks_confirmed': st.session_state.get('tasks_confirmed', False),
            'tasks_saved': st.session_state.get('tasks_saved', False),
            'github_connected': self.github_manager.is_connected(),
            'last_save': st.session_state.get('last_auto_save'),
            'planned_task_count': len(st.session_state.get('planned_tasks', [])),
            'actual_execution_count': len(st.session_state.get('actual_execution', []))
        }

# 创建全局状态管理器实例
github_state_manager = GitHubStateManager()
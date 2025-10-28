# github_state_manager.py
import streamlit as st
import json
from datetime import datetime, time, timedelta
from github_manager import GitHubDataManager

class GitHubStateManager:
    """使用 GitHub 作为持久化存储的状态管理器 - 仅保留当天状态"""
    
    def __init__(self):
        self.github_manager = GitHubDataManager()
        self.state_key = "daily_session_state"
        self.initialized = False
        self.last_save_time = None
        self.min_save_interval = timedelta(seconds=30)  # 最小保存间隔10秒
        self.last_state_hash = None  # 用于检测状态变化
    
    def init_session_state(self):
        """初始化所有 session state 变量"""
        if self.initialized:
            return
            
        # 先尝试从 GitHub 加载当天状态
        today = datetime.now().date().isoformat()
        
        # 强制从 GitHub 加载状态
        if self.load_from_github(today):
            self.initialized = True
            return
            
        # 如果加载失败，使用默认值
        default_states = {
            'tasks_confirmed': False,
            'show_final_confirmation': False,
            'tasks_saved': False,
            'expander_expanded': True,
            'current_date': datetime.now().date(),
            'current_weather': "晴",
            'current_energy_level': 7,
            'current_reflection': "",
            'planned_tasks': [],
            'actual_execution': [],
            'time_inputs_cache': {},
            'last_auto_save': None,
            'state_date': today
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        self.initialized = True
    
    def auto_save_state(self, force=False):
        """智能保存状态到 GitHub"""
        try:
            # 频率控制：避免过于频繁的保存
            current_time = datetime.now()
            if (self.last_save_time and 
                current_time - self.last_save_time < self.min_save_interval and 
                not force):
                return False  # 跳过保存
            
            # 检查是否有实际数据变化
            current_state_hash = self._get_state_hash()
            if (not force and 
                self.last_state_hash and 
                current_state_hash == self.last_state_hash):
                return False  # 状态没有变化，跳过保存
            
            # 确保所有必要的属性都存在
            self._ensure_session_state_initialized()
            
            today = datetime.now().date().isoformat()
            
            # 检查是否是同一天，如果不是则清除旧状态
            if st.session_state.get('state_date') != today:
                self._clear_previous_day_state()
                st.session_state.state_date = today
                force = True
            
            # 只有在有实际数据变化或强制保存时才保存
            if force or self._has_meaningful_changes():
                save_data = self._prepare_save_data()
                success = self._save_to_github(today, save_data)
                
                if success:
                    st.session_state.last_auto_save = current_time
                    self.last_save_time = current_time
                    self.last_state_hash = current_state_hash
                    
                    # 只在调试模式下显示成功信息
                    if st.session_state.get('debug_mode', False):
                        st.sidebar.success("💾 状态已智能保存")
                    return True
            
            return False
                    
        except Exception as e:
            if st.session_state.get('debug_mode', False):
                st.sidebar.error(f"❌ 自动保存失败: {str(e)}")
            return False
    
    def _get_state_hash(self):
        """生成状态哈希值，用于检测变化"""
        import hashlib
        state_data = {
            'planned_tasks': st.session_state.get('planned_tasks', []),
            'actual_execution': st.session_state.get('actual_execution', []),
            'current_reflection': st.session_state.get('current_reflection', ''),
            'tasks_confirmed': st.session_state.get('tasks_confirmed', False),
            'tasks_saved': st.session_state.get('tasks_saved', False),
        }
        state_str = json.dumps(state_data, sort_keys=True, default=str)
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def _has_meaningful_changes(self):
        """检查是否有有意义的数据变化"""
        # 如果有计划任务且任务名称不为空
        planned_tasks = st.session_state.get('planned_tasks', [])
        if planned_tasks:
            for task in planned_tasks:
                if task.get('task_name', '').strip():  # 任务名称不为空
                    return True
        
        # 如果有实际执行数据
        actual_execution = st.session_state.get('actual_execution', [])
        if actual_execution:
            for execution in actual_execution:
                if execution.get('actual_duration', 0) > 0:  # 有实际时长
                    return True
        
        # 如果有反思内容
        if st.session_state.get('current_reflection', '').strip():
            return True
        
        # 如果任务已确认或已保存
        if (st.session_state.get('tasks_confirmed', False) or 
            st.session_state.get('tasks_saved', False)):
            return True
        
        return False
    
    def manual_save_state(self):
        """手动保存状态"""
        return self.auto_save_state(force=True)
    
    def _ensure_session_state_initialized(self):
        """确保所有必要的 session state 属性都已初始化"""
        required_states = {
            'tasks_confirmed': False,
            'show_final_confirmation': False,
            'tasks_saved': False,
            'expander_expanded': True,
            'current_date': datetime.now().date(),
            'current_weather': "晴",
            'current_energy_level': 7,
            'current_reflection': "",
            'planned_tasks': [],
            'actual_execution': [],
            'time_inputs_cache': {},
            'state_date': datetime.now().date().isoformat()
        }
        
        for key, default_value in required_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def _prepare_save_data(self):
        """准备保存数据（处理时间对象的序列化）"""
        # 处理时间输入缓存中的时间对象
        serializable_time_cache = {}
        time_inputs_cache = st.session_state.get('time_inputs_cache', {})
        
        for key, value in time_inputs_cache.items():
            if isinstance(value, time):  # 如果是 time 对象
                serializable_time_cache[key] = value.strftime('%H:%M:%S')
            else:
                serializable_time_cache[key] = value
        
        # 处理 planned_tasks 中的时间对象
        serializable_planned_tasks = []
        planned_tasks = st.session_state.get('planned_tasks', [])
        
        for task in planned_tasks:
            serializable_task = task.copy()
            # 确保时间字段是字符串格式
            if 'planned_start_time' in serializable_task and isinstance(serializable_task['planned_start_time'], time):
                serializable_task['planned_start_time'] = serializable_task['planned_start_time'].strftime('%H:%M')
            if 'planned_end_time' in serializable_task and isinstance(serializable_task['planned_end_time'], time):
                serializable_task['planned_end_time'] = serializable_task['planned_end_time'].strftime('%H:%M')
            serializable_planned_tasks.append(serializable_task)
        
        # 处理 actual_execution 中的时间对象
        serializable_actual_execution = []
        actual_execution = st.session_state.get('actual_execution', [])
        
        for execution in actual_execution:
            serializable_execution = execution.copy()
            # 确保时间字段是字符串格式
            if 'actual_start_time' in serializable_execution and isinstance(serializable_execution['actual_start_time'], time):
                serializable_execution['actual_start_time'] = serializable_execution['actual_start_time'].strftime('%H:%M')
            if 'actual_end_time' in serializable_execution and isinstance(serializable_execution['actual_end_time'], time):
                serializable_execution['actual_end_time'] = serializable_execution['actual_end_time'].strftime('%H:%M')
            serializable_actual_execution.append(serializable_execution)
        
        return {
            # 任务状态
            'tasks_confirmed': st.session_state.get('tasks_confirmed', False),
            'show_final_confirmation': st.session_state.get('show_final_confirmation', False),
            'tasks_saved': st.session_state.get('tasks_saved', False),
            'expander_expanded': st.session_state.get('expander_expanded', True),
            
            # 表单数据
            'current_date': st.session_state.get('current_date', datetime.now().date()).isoformat(),
            'current_weather': st.session_state.get('current_weather', "晴"),
            'current_energy_level': st.session_state.get('current_energy_level', 7),
            'current_reflection': st.session_state.get('current_reflection', ""),
            
            # 任务数据（使用处理后的可序列化版本）
            'planned_tasks': serializable_planned_tasks,
            'actual_execution': serializable_actual_execution,
            
            # 时间数据缓存（使用处理后的可序列化版本）
            'time_inputs_cache': serializable_time_cache,
            
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
        """从数据恢复状态（处理时间字符串的反序列化）"""
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
        
        # 恢复任务数据（处理时间字符串）
        planned_tasks = data.get('planned_tasks', [])
        restored_planned_tasks = []
        for task in planned_tasks:
            restored_task = task.copy()
            # 转换时间字符串为 time 对象
            if 'planned_start_time' in restored_task and isinstance(restored_task['planned_start_time'], str):
                try:
                    restored_task['planned_start_time'] = datetime.strptime(restored_task['planned_start_time'], '%H:%M').time()
                except ValueError:
                    # 如果解析失败，保持原样
                    pass
            if 'planned_end_time' in restored_task and isinstance(restored_task['planned_end_time'], str):
                try:
                    restored_task['planned_end_time'] = datetime.strptime(restored_task['planned_end_time'], '%H:%M').time()
                except ValueError:
                    # 如果解析失败，保持原样
                    pass
            restored_planned_tasks.append(restored_task)
        
        st.session_state.planned_tasks = restored_planned_tasks
        
        # 恢复实际执行数据（处理时间字符串）
        actual_execution = data.get('actual_execution', [])
        restored_actual_execution = []
        for execution in actual_execution:
            restored_execution = execution.copy()
            # 转换时间字符串为 time 对象
            if 'actual_start_time' in restored_execution and isinstance(restored_execution['actual_start_time'], str):
                try:
                    restored_execution['actual_start_time'] = datetime.strptime(restored_execution['actual_start_time'], '%H:%M').time()
                except ValueError:
                    pass
            if 'actual_end_time' in restored_execution and isinstance(restored_execution['actual_end_time'], str):
                try:
                    restored_execution['actual_end_time'] = datetime.strptime(restored_execution['actual_end_time'], '%H:%M').time()
                except ValueError:
                    pass
            restored_actual_execution.append(restored_execution)
        
        st.session_state.actual_execution = restored_actual_execution
        
        # 恢复时间缓存（处理时间字符串）
        time_inputs_cache = data.get('time_inputs_cache', {})
        restored_time_cache = {}
        for key, value in time_inputs_cache.items():
            if isinstance(value, str) and ':' in value:
                try:
                    # 尝试解析时间字符串
                    restored_time_cache[key] = datetime.strptime(value, '%H:%M:%S').time()
                except ValueError:
                    try:
                        # 尝试另一种格式
                        restored_time_cache[key] = datetime.strptime(value, '%H:%M').time()
                    except ValueError:
                        # 如果解析失败，保持原样
                        restored_time_cache[key] = value
            else:
                restored_time_cache[key] = value
        
        st.session_state.time_inputs_cache = restored_time_cache
        
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
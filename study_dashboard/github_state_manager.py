# github_state_manager.py
import streamlit as st
import json
from datetime import datetime, time, timedelta
from github_manager import GitHubDataManager
import pytz

# 北京时区
beijing_tz = pytz.timezone('Asia/Shanghai')

class GitHubStateManager:
    """使用 GitHub 作为持久化存储的状态管理器 - 仅保留当天状态"""
    
    def __init__(self):
        self.github_manager = GitHubDataManager()
        self.state_key = "daily_session_state.json"  # 明确指定文件扩展名
        self.initialized = False
        self.last_save_time = None
        self.min_save_interval = timedelta(seconds=30)
        self.last_state_hash = None
    
    def init_session_state(self):
        """初始化所有 session state 变量"""
        if self.initialized:
            return
            
        # 先尝试从 GitHub 加载当天状态
        today = datetime.now(beijing_tz).date().isoformat()
        
        # 强制从 GitHub 加载状态
        if self.load_from_github(today):
            st.sidebar.success("✅ 状态恢复成功")
            self.initialized = True
            return
            
        # 如果加载失败，使用默认值
        default_states = {
            'tasks_confirmed': False,
            'show_final_confirmation': False,
            'tasks_saved': False,
            'expander_expanded': True,
            'current_date': datetime.now(beijing_tz).date(),
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
        st.sidebar.info("🆕 开始新的一天")
    
    def auto_save_state(self, force=False):
        """智能保存状态到 GitHub"""
        try:
            # 检查是否是空状态
            if not force and self._is_empty_state():
                return False
                
            # 频率控制
            current_time = datetime.now(beijing_tz)
            if (self.last_save_time and 
                current_time - self.last_save_time < self.min_save_interval and 
                not force):
                return False
            
            # 检查是否有实际数据变化
            current_state_hash = self._get_state_hash()
            if (not force and 
                self.last_state_hash and 
                current_state_hash == self.last_state_hash):
                return False

            # 确保所有必要的属性都存在
            self._ensure_session_state_initialized()
            
            today = datetime.now(beijing_tz).date().isoformat()
            
            # 检查是否是同一天
            if st.session_state.get('state_date') != today:
                self._clear_previous_day_state()
                st.session_state.state_date = today
                force = True
            
            save_data = self._prepare_save_data()
            success = self._save_to_github(today, save_data)
            
            if success:
                st.session_state.last_auto_save = current_time
                self.last_save_time = current_time
                self.last_state_hash = current_state_hash
                return True
            
            return False
                    
        except Exception as e:
            return False

    def _is_empty_state(self):
        """检查是否是空状态（没有用户数据）"""
        # 检查是否有计划任务
        planned_tasks = st.session_state.get('planned_tasks', [])
        if planned_tasks:
            for task in planned_tasks:
                if task.get('task_name', '').strip():
                    return False
        
        # 检查是否有实际执行数据
        actual_execution = st.session_state.get('actual_execution', [])
        if actual_execution:
            return False
        
        # 检查是否有反思内容
        if st.session_state.get('current_reflection', '').strip():
            return False
        
        # 检查任务状态
        if (st.session_state.get('tasks_confirmed', False) or 
            st.session_state.get('tasks_saved', False)):
            return False
        
        return True
    
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
            'current_date': datetime.now(beijing_tz).date(),
            'current_weather': "晴",
            'current_energy_level': 7,
            'current_reflection': "",
            'planned_tasks': [],
            'actual_execution': [],
            'time_inputs_cache': {},
            'state_date': datetime.now(beijing_tz).date().isoformat()
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
            if isinstance(value, time):
                serializable_time_cache[key] = value.strftime('%H:%M:%S')
            else:
                serializable_time_cache[key] = value
        
        # 处理 planned_tasks 中的时间对象
        serializable_planned_tasks = []
        planned_tasks = st.session_state.get('planned_tasks', [])
        
        for task in planned_tasks:
            serializable_task = task.copy()
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
            if 'actual_start_time' in serializable_execution and isinstance(serializable_execution['actual_start_time'], time):
                serializable_execution['actual_start_time'] = serializable_execution['actual_start_time'].strftime('%H:%M')
            if 'actual_end_time' in serializable_execution and isinstance(serializable_execution['actual_end_time'], time):
                serializable_execution['actual_end_time'] = serializable_execution['actual_end_time'].strftime('%H:%M')
            serializable_actual_execution.append(serializable_execution)
        
        return {
            'tasks_confirmed': st.session_state.get('tasks_confirmed', False),
            'show_final_confirmation': st.session_state.get('show_final_confirmation', False),
            'tasks_saved': st.session_state.get('tasks_saved', False),
            'expander_expanded': st.session_state.get('expander_expanded', True),
            'current_date': st.session_state.get('current_date', datetime.now(beijing_tz).date()).isoformat(),
            'current_weather': st.session_state.get('current_weather', "晴"),
            'current_energy_level': st.session_state.get('current_energy_level', 7),
            'current_reflection': st.session_state.get('current_reflection', ""),
            'planned_tasks': serializable_planned_tasks,
            'actual_execution': serializable_actual_execution,
            'time_inputs_cache': serializable_time_cache,
            'last_auto_save': datetime.now(beijing_tz).isoformat(),
            'state_date': st.session_state.get('state_date', datetime.now(beijing_tz).date().isoformat())
        }
    
    def _save_to_github(self, date_key, data):
        """保存状态数据到 GitHub"""
        if not self.github_manager.is_connected():
            return False
            
        try:
            # 加载所有状态数据
            all_states = self._load_all_states_from_github()
            
            # 更新当天状态
            all_states[date_key] = data
            
            # 只保留最近3天的状态
            self._cleanup_old_states(all_states)
            
            # 保存到 GitHub
            content = json.dumps(all_states, ensure_ascii=False, indent=2)
            return self._save_raw_to_github(content)
            
        except Exception as e:
            return False
    
    def _load_all_states_from_github(self):
        """从 GitHub 加载所有状态数据"""
        if not self.github_manager.is_connected():
            return {}
            
        try:
            # 直接使用 github_manager 的方法
            if hasattr(self.github_manager, 'repo'):
                contents = self.github_manager.repo.get_contents(self.state_key)
                file_content = contents.decoded_content.decode('utf-8')
                return json.loads(file_content)
            return {}
        except Exception as e:
            # 文件不存在，返回空字典
            return {}
    
    def _save_raw_to_github(self, content):
        """原始保存到 GitHub"""
        try:
            if hasattr(self.github_manager, 'repo'):
                # 检查文件是否存在
                try:
                    contents = self.github_manager.repo.get_contents(self.state_key)
                    # 更新文件
                    self.github_manager.repo.update_file(
                        self.state_key,
                        f"更新会话状态 {datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')}",
                        content,
                        contents.sha
                    )
                except Exception:
                    # 创建新文件
                    self.github_manager.repo.create_file(
                        self.state_key,
                        f"创建会话状态 {datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')}",
                        content
                    )
                return True
            return False
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
            return False
    
    def _restore_from_data(self, data):
        """从数据恢复状态"""
        if not data:
            return False
            
        try:
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
                        pass
                if 'planned_end_time' in restored_task and isinstance(restored_task['planned_end_time'], str):
                    try:
                        restored_task['planned_end_time'] = datetime.strptime(restored_task['planned_end_time'], '%H:%M').time()
                    except ValueError:
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
                        restored_time_cache[key] = datetime.strptime(value, '%H:%M:%S').time()
                    except ValueError:
                        try:
                            restored_time_cache[key] = datetime.strptime(value, '%H:%M').time()
                        except ValueError:
                            restored_time_cache[key] = value
                else:
                    restored_time_cache[key] = value
            
            st.session_state.time_inputs_cache = restored_time_cache
            
            # 恢复状态日期
            st.session_state.state_date = data.get('state_date', datetime.now(beijing_tz).date().isoformat())
            
            if 'last_auto_save' in data:
                st.session_state.last_auto_save = datetime.fromisoformat(data['last_auto_save'])
            
            return True
            
        except Exception as e:
            return False
    
    def _clear_previous_day_state(self):
        """清除前一天的状态"""
        keys_to_clear = [
            'tasks_confirmed', 'show_final_confirmation', 'tasks_saved',
            'expander_expanded', 'planned_tasks', 'actual_execution',
            'time_inputs_cache', 'current_reflection'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def _cleanup_old_states(self, all_states):
        """清理旧的状态数据（只保留最近3天）"""
        try:
            sorted_dates = sorted(all_states.keys(), reverse=True)
            if len(sorted_dates) > 3:
                for old_date in sorted_dates[3:]:
                    del all_states[old_date]
        except Exception:
            pass
    
    def clear_current_state(self):
        """清除当前状态（开始新的一天）"""
        today = datetime.now(beijing_tz).date().isoformat()
        
        # 清除 session state
        self._clear_previous_day_state()
        
        # 重置为默认值
        st.session_state.tasks_confirmed = False
        st.session_state.show_final_confirmation = False
        st.session_state.tasks_saved = False
        st.session_state.expander_expanded = True
        st.session_state.current_date = datetime.now(beijing_tz).date()
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
        today = datetime.now(beijing_tz).date().isoformat()
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
    
    def get_data_stats(self):
        """获取数据统计信息"""
        stats = {
            'state_count': 0,
            'study_data_count': 0,
            'old_states': 0,
            'old_study_data': 0,
            'cache_size': 0
        }
        
        # 统计缓存大小
        cache_keys = ['time_inputs_cache', 'auto_saved_data']
        for key in cache_keys:
            if key in st.session_state:
                stats['cache_size'] += len(str(st.session_state[key]))
        
        if not self.github_manager.is_connected():
            return stats
            
        try:
            # 统计状态数据
            all_states = self._load_all_states_from_github()
            stats['state_count'] = len(all_states)
            
            # 统计30天前的旧状态数据
            cutoff_date = datetime.now(beijing_tz) - timedelta(days=30)
            stats['old_states'] = sum(
                1 for date in all_states.keys() 
                if datetime.fromisoformat(date).date() < cutoff_date.date()
            )
            
            # 统计学习数据
            all_study_data = self.github_manager.load_all_data()
            stats['study_data_count'] = len(all_study_data)
            
            # 统计30天前的旧学习数据
            stats['old_study_data'] = sum(
                1 for data in all_study_data 
                if datetime.fromisoformat(data['date']).date() < cutoff_date.date()
            )
            
        except Exception:
            pass
            
        return stats
    
    def cleanup_data(self, days_to_keep=30, clear_all=False, clear_cache=False):
        """清理数据
        
        Args:
            days_to_keep: 保留最近多少天的数据
            clear_all: 是否清除所有数据
            clear_cache: 是否清除缓存
        """
        if not self.github_manager.is_connected():
            st.error("❌ GitHub 未连接，无法清理数据")
            return False
            
        try:
            if clear_all:
                # 清除所有数据
                return self._clear_all_data()
            elif clear_cache:
                # 只清除缓存
                return self._clear_cache_only()
            else:
                # 清除指定天数前的数据
                return self._cleanup_old_data(days_to_keep)
                
        except Exception as e:
            st.error(f"❌ 数据清理失败: {str(e)}")
            return False
    
    def _clear_cache_only(self):
        """只清除缓存数据"""
        try:
            # 清除 session state 中的缓存
            cache_keys = ['time_inputs_cache', 'auto_saved_data']
            for key in cache_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            # 清除 GitHub 上的状态缓存（保留当天状态）
            today = datetime.now(beijing_tz).date().isoformat()
            all_states = self._load_all_states_from_github()
            
            # 只保留今天的状态
            cleaned_states = {}
            if today in all_states:
                cleaned_states[today] = all_states[today]
            
            if len(cleaned_states) < len(all_states):
                content = json.dumps(cleaned_states, ensure_ascii=False, indent=2)
                self._save_raw_to_github(content)
            
            st.success("✅ 缓存数据已清除")
            return True
            
        except Exception as e:
            st.error(f"❌ 清除缓存失败: {str(e)}")
            return False
    
    def _clear_all_data(self):
        """清除所有数据"""
        try:
            # 清除状态数据
            try:
                contents = self.github_manager.repo.get_contents(self.state_key)
                self.github_manager.repo.delete_file(
                    self.state_key,
                    "清除所有状态数据",
                    contents.sha
                )
            except Exception:
                pass  # 文件不存在
            
            # 清除学习数据
            try:
                data_contents = self.github_manager.repo.get_contents("study_data.json")
                self.github_manager.repo.delete_file(
                    "study_data.json",
                    "清除所有学习数据",
                    data_contents.sha
                )
            except Exception:
                pass  # 文件不存在
            
            # 清除 session state 中的所有数据
            self._clear_all_session_state()
            
            st.success("✅ 所有数据已清除")
            return True
            
        except Exception as e:
            st.error(f"❌ 清除所有数据失败: {str(e)}")
            return False
    
    def _clear_all_session_state(self):
        """清除所有 session state 数据"""
        keys_to_clear = [
            'tasks_confirmed', 'show_final_confirmation', 'tasks_saved',
            'expander_expanded', 'planned_tasks', 'actual_execution',
            'time_inputs_cache', 'current_reflection', 'auto_saved_data',
            'current_date', 'current_weather', 'current_energy_level',
            'last_auto_save', 'state_date'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # 重新初始化
        self.initialized = False
        self.init_session_state()
    
    
# 创建全局状态管理器实例
github_state_manager = GitHubStateManager()
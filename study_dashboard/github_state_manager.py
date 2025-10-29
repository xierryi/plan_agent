# github_state_manager.py
import streamlit as st
import json
from datetime import datetime, time, timedelta
from github_manager import GitHubDataManager
import pytz
import hashlib

# 北京时区
beijing_tz = pytz.timezone('Asia/Shanghai')

class GitHubStateManager:
    """使用 GitHub 作为持久化存储的状态管理器 - 长期解决方案"""
    
    def __init__(self):
        self.github_manager = GitHubDataManager()
        self.state_key = "daily_session_state.json"
        self.initialized = False
        self.last_save_time = None
        self.min_save_interval = timedelta(seconds=30)
        self.last_state_hash = None
    
    def init_session_state(self):
        """初始化 session state - 直接加载当前日期的状态"""
        if self.initialized:
            return
            
        today = datetime.now(beijing_tz).date()
        today_iso = today.isoformat()
        
        # 直接尝试加载今天的状态
        if self.load_from_github(today_iso):
            st.sidebar.success("✅ 今日状态恢复成功")
        else:
            # 初始化新状态
            self._initialize_new_day(today_iso)
        
        self.initialized = True
    
    def _load_today_state(self, today_iso: str) -> bool:
        """加载今天的状态"""
        if self.load_from_github(today_iso):
            st.sidebar.success("✅ 今日状态恢复成功")
            return True
        return False
    
    def _has_valid_tasks(self, tasks: list) -> bool:
        """检查任务列表是否包含有效任务"""
        for task in tasks:
            if task.get('task_name', '').strip():
                return True
        return False
    
    def _initialize_new_day(self, today_iso: str):
        """完全新的初始化"""
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
            'state_date': today_iso,
            'plan_source': "new"
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        st.sidebar.info("🆕 开始新的一天")
    
    def auto_save_state(self, force=False):
        """增强的智能保存状态"""
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
            
            # 智能变化检测
            current_state_hash = self._get_state_hash()
            
            # 如果有实际执行数据，降低保存门槛
            actual_execution = st.session_state.get('actual_execution', [])
            has_actual_data = actual_execution and len(actual_execution) > 0
            
            if has_actual_data:
                # 执行阶段：频繁保存
                pass
            else:
                # 计划阶段：严格检查变化
                if (not force and 
                    self.last_state_hash and 
                    current_state_hash == self.last_state_hash):
                    return False

            # 确保状态正确性
            self._ensure_state_consistency()
            
            today = datetime.now(beijing_tz).date().isoformat()
            
            # 检查日期变化
            if st.session_state.get('state_date') != today:
                self._handle_date_change(today)
                force = True
            
            save_data = self._prepare_save_data()
            success = self._save_to_github(today, save_data)
            
            if success:
                st.session_state.last_auto_save = current_time
                self.last_save_time = current_time
                self.last_state_hash = current_state_hash
                
                # 只在强制保存时显示提示，避免干扰
                if force:
                    st.sidebar.success("💾 状态已保存")
                    
                return True
            
            return False
                    
        except Exception as e:
            st.sidebar.error(f"❌ 保存失败: {str(e)}")
            return False
    
    def _ensure_state_consistency(self):
        """确保状态一致性"""
        today = datetime.now(beijing_tz).date().isoformat()
        
        # 确保状态日期正确
        if 'state_date' not in st.session_state:
            st.session_state.state_date = today
        
        # 确保计划来源存在
        if 'plan_source' not in st.session_state:
            st.session_state.plan_source = "new"
    
    def _handle_date_change(self, new_date: str):
        """处理日期变化 - 直接加载目标日期的状态"""
        old_date = st.session_state.get('state_date')
        
        # 更新状态日期
        st.session_state.state_date = new_date
        
        # 直接尝试加载目标日期的状态
        if self.load_from_github(new_date):
            st.sidebar.success(f"✅ 已加载 {new_date} 的计划")
        else:
            # 如果目标日期没有保存的状态，初始化空状态
            st.sidebar.info(f"📝 {new_date} 没有保存的计划")
            
            # 清除执行数据，但保持其他设置
            st.session_state.actual_execution = []
            st.session_state.time_inputs_cache = {}
            st.session_state.current_reflection = ""
            st.session_state.tasks_saved = False
            st.session_state.show_final_confirmation = False
            st.session_state.plan_source = "new_date"
            
            # 如果切换到未来日期，保持计划任务；如果切换到过去，清空
            if new_date < datetime.now(beijing_tz).date().isoformat():
                st.session_state.planned_tasks = []
                st.session_state.tasks_confirmed = False
    
    def get_state_info(self):
        """增强的状态信息"""
        today = datetime.now(beijing_tz).date().isoformat()
        state_date = st.session_state.get('state_date')
        is_today = state_date == today
        
        info = {
            'is_today': is_today,
            'state_date': state_date,
            'current_date': st.session_state.get('current_date'),
            'has_planned_tasks': len(st.session_state.get('planned_tasks', [])) > 0,
            'tasks_confirmed': st.session_state.get('tasks_confirmed', False),
            'tasks_saved': st.session_state.get('tasks_saved', False),
            'github_connected': self.github_manager.is_connected(),
            'last_save': st.session_state.get('last_auto_save'),
            'planned_task_count': len(st.session_state.get('planned_tasks', [])),
            'actual_execution_count': len(st.session_state.get('actual_execution', [])),
            'plan_source': st.session_state.get('plan_source', 'unknown')
        }
        
        # 计算日期差异
        if state_date and info['current_date']:
            state_date_obj = datetime.fromisoformat(state_date).date() if isinstance(state_date, str) else state_date
            current_date_obj = info['current_date']
            info['date_diff_days'] = (current_date_obj - state_date_obj).days
        else:
            info['date_diff_days'] = 0
            
        return info

    def _is_empty_state(self):
        """检查是否是空状态"""
        # 如果有计划来源，不算空状态
        if st.session_state.get('plan_source') not in [None, "new"]:
            return False
            
        planned_tasks = st.session_state.get('planned_tasks', [])
        if planned_tasks:
            for task in planned_tasks:
                if task.get('task_name', '').strip():
                    return False
        
        actual_execution = st.session_state.get('actual_execution', [])
        if actual_execution:
            return False
        
        if st.session_state.get('current_reflection', '').strip():
            return False
        
        if (st.session_state.get('tasks_confirmed', False) or 
            st.session_state.get('tasks_saved', False)):
            return False
        
        return True

    def _prepare_save_data(self):
        """准备保存数据"""
        # 处理时间对象的序列化
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
            'state_date': st.session_state.get('state_date', datetime.now(beijing_tz).date().isoformat()),
            'plan_source': st.session_state.get('plan_source', 'new')
        }

    def manual_save_state(self):
        """手动保存状态"""
        return self.auto_save_state(force=True)

    def _get_state_hash(self):
        """生成状态哈希值"""
        import hashlib
        
        state_data = {
            'planned_tasks': st.session_state.get('planned_tasks', []),
            'actual_execution': st.session_state.get('actual_execution', []),
            'tasks_confirmed': st.session_state.get('tasks_confirmed', False),
            'tasks_saved': st.session_state.get('tasks_saved', False),
            'show_final_confirmation': st.session_state.get('show_final_confirmation', False),
            'current_reflection': st.session_state.get('current_reflection', ''),
            'current_weather': st.session_state.get('current_weather', ''),
            'current_energy_level': st.session_state.get('current_energy_level', 0),
            'current_date': str(st.session_state.get('current_date', '')),
            'time_inputs_cache': st.session_state.get('time_inputs_cache', {}),
            'plan_source': st.session_state.get('plan_source', 'new')
        }
        
        # 深度处理任务数据
        processed_planned_tasks = []
        for task in state_data['planned_tasks']:
            processed_task = {
                'task_name': task.get('task_name', ''),
                'subject': task.get('subject', ''),
                'difficulty': task.get('difficulty', 0),
                'planned_start_time': task.get('planned_start_time', ''),
                'planned_end_time': task.get('planned_end_time', ''),
                'planned_duration': task.get('planned_duration', 0)
            }
            processed_planned_tasks.append(processed_task)
        state_data['planned_tasks'] = processed_planned_tasks
        
        # 深度处理执行数据
        processed_actual_execution = []
        for execution in state_data['actual_execution']:
            processed_execution = {
                'task_id': execution.get('task_id', 0),
                'actual_start_time': execution.get('actual_start_time', ''),
                'actual_end_time': execution.get('actual_end_time', ''),
                'actual_duration': execution.get('actual_duration', 0),
                'post_energy': execution.get('post_energy', 0)
            }
            processed_actual_execution.append(processed_execution)
        state_data['actual_execution'] = processed_actual_execution
        
        state_str = json.dumps(state_data, sort_keys=True, default=str)
        return hashlib.md5(state_str.encode()).hexdigest()

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
            # 恢复基础状态
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
            
            # 恢复计划来源
            st.session_state.plan_source = data.get('plan_source', 'new')
            
            # 恢复任务数据（处理时间字符串）
            planned_tasks = data.get('planned_tasks', [])
            restored_planned_tasks = []
            for task in planned_tasks:
                restored_task = task.copy()
                # 转换时间字符串为 time 对象
                if 'planned_start_time' in restored_task and isinstance(restored_task['planned_start_time'], str):
                    try:
                        time_str = restored_task['planned_start_time']
                        if ':' in time_str:
                            parts = time_str.split(':')
                            if len(parts) >= 2:
                                restored_task['planned_start_time'] = datetime.strptime(f"{parts[0]}:{parts[1]}", '%H:%M').time()
                    except ValueError:
                        restored_task['planned_start_time'] = datetime.strptime("09:00", '%H:%M').time()
                if 'planned_end_time' in restored_task and isinstance(restored_task['planned_end_time'], str):
                    try:
                        time_str = restored_task['planned_end_time']
                        if ':' in time_str:
                            parts = time_str.split(':')
                            if len(parts) >= 2:
                                restored_task['planned_end_time'] = datetime.strptime(f"{parts[0]}:{parts[1]}", '%H:%M').time()
                    except ValueError:
                        restored_task['planned_end_time'] = datetime.strptime("10:00", '%H:%M').time()
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
                        time_str = restored_execution['actual_start_time']
                        if ':' in time_str:
                            parts = time_str.split(':')
                            if len(parts) >= 2:
                                restored_execution['actual_start_time'] = datetime.strptime(f"{parts[0]}:{parts[1]}", '%H:%M').time()
                    except ValueError:
                        restored_execution['actual_start_time'] = datetime.strptime("09:00", '%H:%M').time()
                if 'actual_end_time' in restored_execution and isinstance(restored_execution['actual_end_time'], str):
                    try:
                        time_str = restored_execution['actual_end_time']
                        if ':' in time_str:
                            parts = time_str.split(':')
                            if len(parts) >= 2:
                                restored_execution['actual_end_time'] = datetime.strptime(f"{parts[0]}:{parts[1]}", '%H:%M').time()
                    except ValueError:
                        restored_execution['actual_end_time'] = datetime.strptime("10:00", '%H:%M').time()
                restored_actual_execution.append(restored_execution)
            
            st.session_state.actual_execution = restored_actual_execution
            
            # 恢复时间缓存（处理时间字符串）
            time_inputs_cache = data.get('time_inputs_cache', {})
            restored_time_cache = {}
            for key, value in time_inputs_cache.items():
                if isinstance(value, str) and ':' in value:
                    try:
                        parts = value.split(':')
                        if len(parts) >= 2:
                            restored_time_cache[key] = datetime.strptime(f"{parts[0]}:{parts[1]}", '%H:%M').time()
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

    def _save_to_github(self, date_key, data):
        """保存状态数据到 GitHub"""
        if not self.github_manager.is_connected():
            return False
            
        try:
            all_states = self._load_all_states_from_github()
            all_states[date_key] = data
            self._cleanup_old_states(all_states)
            
            content = json.dumps(all_states, ensure_ascii=False, indent=2)
            return self._save_raw_to_github(content)
            
        except Exception as e:
            return False

    def _load_all_states_from_github(self):
        """从 GitHub 加载所有状态数据"""
        if not self.github_manager.is_connected():
            return {}
            
        try:
            # 使用新的 load_raw_content 方法
            file_content = self.github_manager.load_raw_content(self.state_key)
            if file_content:
                return json.loads(file_content)
            return {}
        except Exception as e:
            return {}

    def _save_raw_to_github(self, content):
        """原始保存到 GitHub"""
        try:
            # 使用新的 save_raw_content 方法
            return self.github_manager.save_raw_content(
                self.state_key,
                content,
                f"更新会话状态 {datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')}"
            )
        except Exception:
            return False

    def _cleanup_old_states(self, all_states):
        """清理旧的状态数据（保留最近7天）"""
        try:
            sorted_dates = sorted(all_states.keys(), reverse=True)
            if len(sorted_dates) > 7:
                for old_date in sorted_dates[7:]:
                    del all_states[old_date]
        except Exception:
            pass

    def clear_current_state(self):
        """清除当前状态"""
        today = datetime.now(beijing_tz).date().isoformat()
        
        keys_to_clear = [
            'tasks_confirmed', 'show_final_confirmation', 'tasks_saved',
            'expander_expanded', 'planned_tasks', 'actual_execution',
            'time_inputs_cache', 'current_reflection', 'plan_source'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
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
        st.session_state.plan_source = "new"
        
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

    def get_data_stats(self):
        """获取数据统计信息"""
        stats = {
            'state_count': 0,
            'study_data_count': 0,
            'old_states': 0,
            'old_study_data': 0,
            'cache_size': 0
        }
        
        cache_keys = ['time_inputs_cache']
        for key in cache_keys:
            if key in st.session_state:
                stats['cache_size'] += len(str(st.session_state[key]))
        
        if not self.github_manager.is_connected():
            return stats
            
        try:
            all_states = self._load_all_states_from_github()
            stats['state_count'] = len(all_states)
            
            cutoff_date = datetime.now(beijing_tz) - timedelta(days=30)
            stats['old_states'] = sum(
                1 for date in all_states.keys() 
                if datetime.fromisoformat(date).date() < cutoff_date.date()
            )
            
            all_study_data = self.github_manager.load_all_data()
            stats['study_data_count'] = len(all_study_data)
            
            stats['old_study_data'] = sum(
                1 for data in all_study_data 
                if datetime.fromisoformat(data['date']).date() < cutoff_date.date()
            )
            
        except Exception:
            pass
            
        return stats

    def cleanup_data(self, days_to_keep=30, clear_all=False, clear_cache=False):
        """清理数据"""
        if not self.github_manager.is_connected():
            st.error("❌ GitHub 未连接，无法清理数据")
            return False
            
        try:
            if clear_all:
                return self._clear_all_data()
            elif clear_cache:
                return self._clear_cache_only()
            else:
                return self._cleanup_old_data(days_to_keep)
                
        except Exception as e:
            st.error(f"❌ 数据清理失败: {str(e)}")
            return False

    def _clear_cache_only(self):
        """只清除缓存数据"""
        try:
            # 清除 session state 中的缓存
            cache_keys = ['time_inputs_cache']
            for key in cache_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.success("✅ 缓存数据已清除")
            return True
            
        except Exception as e:
            st.error(f"❌ 清除缓存失败: {str(e)}")
            return False

    def _cleanup_old_data(self, days_to_keep):
        """清理指定天数前的数据"""
        try:
            cutoff_date = datetime.now(beijing_tz) - timedelta(days=days_to_keep)
            deleted_count = 0
            
            # 清理状态数据
            try:
                all_states = self._load_all_states_from_github()
                original_count = len(all_states)
                
                all_states = {
                    date: data for date, data in all_states.items() 
                    if datetime.fromisoformat(date).date() >= cutoff_date.date()
                }
                
                if len(all_states) < original_count:
                    content = json.dumps(all_states, ensure_ascii=False, indent=2)
                    self._save_raw_to_github(content)
                    deleted_count += (original_count - len(all_states))
            except Exception:
                pass
            
            # 清理学习数据
            try:
                all_study_data = self.github_manager.load_all_data()
                original_study_count = len(all_study_data)
                
                all_study_data = [
                    data for data in all_study_data 
                    if datetime.fromisoformat(data['date']).date() >= cutoff_date.date()
                ]
                
                if len(all_study_data) < original_study_count:
                    content = json.dumps(all_study_data, ensure_ascii=False, indent=2)
                    self.github_manager._save_to_github(all_study_data)
                    deleted_count += (original_study_count - len(all_study_data))
            except Exception:
                pass
            
            if deleted_count > 0:
                st.success(f"✅ 已清理 {deleted_count} 条旧数据（保留最近 {days_to_keep} 天）")
            else:
                st.info("📝 没有需要清理的旧数据")
                
            return True
            
        except Exception as e:
            st.error(f"❌ 清理旧数据失败: {str(e)}")
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
                pass
            
            # 清除学习数据
            try:
                data_contents = self.github_manager.repo.get_contents("study_data.json")
                self.github_manager.repo.delete_file(
                    "study_data.json",
                    "清除所有学习数据",
                    data_contents.sha
                )
            except Exception:
                pass
            
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
            'time_inputs_cache', 'current_reflection', 'plan_source',
            'current_date', 'current_weather', 'current_energy_level',
            'last_auto_save', 'state_date'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        self.initialized = False
        self.init_session_state()


# 创建全局状态管理器实例
github_state_manager = GitHubStateManager()
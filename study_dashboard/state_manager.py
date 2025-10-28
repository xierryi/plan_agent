import streamlit as st
import pickle
import os
from datetime import datetime, date
import copy

class StateManager:
    """状态管理器 - 带文件持久化的完整解决方案"""
    
    def __init__(self, state_file="session_state.pkl"):
        self.state_file = state_file
        self.initialized = False
    
    def init_session_state(self):
        """初始化所有 session state 变量"""
        if self.initialized:
            return
            
        # 先尝试从文件加载
        if self.load_from_file():
            st.sidebar.success("✅ 状态已从文件恢复")
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
            
            # 应用状态
            'app_initialized': True
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        self.initialized = True
        st.sidebar.info("🆕 新会话已初始化")
    
    def auto_save_state(self):
        """自动保存当前所有状态到文件和session state"""
        try:
            # 准备保存数据
            save_data = {
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
                
                # 任务数据
                'planned_tasks': copy.deepcopy(st.session_state.get('planned_tasks', [])),
                'actual_execution': copy.deepcopy(st.session_state.get('actual_execution', [])),
                
                # 时间数据缓存
                'time_inputs_cache': copy.deepcopy(st.session_state.get('time_inputs_cache', {})),
                
                # 元数据
                'last_auto_save': datetime.now().isoformat(),
                'save_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version': '1.0'
            }
            
            # 保存到 session state
            st.session_state.auto_saved_data = save_data
            st.session_state.last_auto_save = datetime.now()
            
            # 保存到文件
            self.save_to_file(save_data)
            
            return True
            
        except Exception as e:
            st.sidebar.error(f"❌ 自动保存失败: {str(e)}")
            return False
    
    def save_to_file(self, data):
        """保存状态到文件"""
        try:
            with open(self.state_file, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"保存状态文件失败: {e}")
            return False
    
    def load_from_file(self):
        """从文件加载状态"""
        try:
            if not os.path.exists(self.state_file):
                return False
                
            with open(self.state_file, 'rb') as f:
                saved_data = pickle.load(f)
            
            # 验证数据格式
            if not isinstance(saved_data, dict):
                return False
            
            # 恢复到 session state
            st.session_state.tasks_confirmed = saved_data.get('tasks_confirmed', False)
            st.session_state.show_final_confirmation = saved_data.get('show_final_confirmation', False)
            st.session_state.tasks_saved = saved_data.get('tasks_saved', False)
            st.session_state.expander_expanded = saved_data.get('expander_expanded', True)
            
            # 恢复日期
            date_str = saved_data.get('current_date')
            if date_str:
                try:
                    st.session_state.current_date = datetime.fromisoformat(date_str).date()
                except:
                    st.session_state.current_date = datetime.now().date()
            else:
                st.session_state.current_date = datetime.now().date()
            
            st.session_state.current_weather = saved_data.get('current_weather', "晴")
            st.session_state.current_energy_level = saved_data.get('current_energy_level', 7)
            st.session_state.current_reflection = saved_data.get('current_reflection', "")
            
            st.session_state.planned_tasks = saved_data.get('planned_tasks', [])
            st.session_state.actual_execution = saved_data.get('actual_execution', [])
            st.session_state.time_inputs_cache = saved_data.get('time_inputs_cache', {})
            
            # 恢复时间戳
            last_save_str = saved_data.get('last_auto_save')
            if last_save_str:
                try:
                    st.session_state.last_auto_save = datetime.fromisoformat(last_save_str)
                except:
                    st.session_state.last_auto_save = None
            
            st.session_state.auto_saved_data = saved_data
            return True
            
        except Exception as e:
            print(f"加载状态文件失败: {e}")
            # 如果文件损坏，删除它
            try:
                os.remove(self.state_file)
            except:
                pass
            return False
    
    def clear_state(self):
        """清除所有状态（用于新的一天或重置）"""
        keys_to_clear = [
            'tasks_confirmed', 'show_final_confirmation', 'tasks_saved',
            'expander_expanded', 'planned_tasks', 'actual_execution',
            'time_inputs_cache', 'current_reflection', 'auto_saved_data',
            'last_auto_save'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # 删除文件
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
        except Exception as e:
            print(f"删除状态文件失败: {e}")
        
        # 重新初始化
        self.initialized = False
        self.init_session_state()
        
        return True
    
    def get_state_info(self):
        """获取状态信息"""
        return {
            'has_planned_tasks': len(st.session_state.get('planned_tasks', [])) > 0,
            'tasks_confirmed': st.session_state.get('tasks_confirmed', False),
            'tasks_saved': st.session_state.get('tasks_saved', False),
            'file_exists': os.path.exists(self.state_file),
            'last_save': st.session_state.get('last_auto_save'),
            'planned_task_count': len(st.session_state.get('planned_tasks', [])),
            'actual_execution_count': len(st.session_state.get('actual_execution', []))
        }
    
    def export_state(self):
        """导出状态数据（用于备份）"""
        if 'auto_saved_data' in st.session_state:
            return copy.deepcopy(st.session_state.auto_saved_data)
        return None
    
    def import_state(self, state_data):
        """导入状态数据（从备份恢复）"""
        try:
            if not isinstance(state_data, dict):
                return False, "无效的数据格式"
            
            # 保存到文件
            success = self.save_to_file(state_data)
            if success:
                # 重新加载
                return self.load_from_file(), "状态导入成功"
            else:
                return False, "保存导入数据失败"
                
        except Exception as e:
            return False, f"导入状态失败: {str(e)}"
    
    def backup_state(self, backup_file=None):
        """备份状态到指定文件"""
        if backup_file is None:
            backup_file = f"state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        
        try:
            if os.path.exists(self.state_file):
                import shutil
                shutil.copy2(self.state_file, backup_file)
                return True, f"状态已备份到: {backup_file}"
            else:
                return False, "没有状态文件可备份"
        except Exception as e:
            return False, f"备份失败: {str(e)}"

# 创建全局状态管理器实例
state_manager = StateManager()
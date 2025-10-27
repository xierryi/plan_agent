# github_manager.py
import base64
import json
from datetime import datetime
import streamlit as st
from github import Github, GithubException
import pandas as pd

class GitHubDataManager:
    def __init__(self):
        self.repo_owner = None
        self.repo_name = None
        self.data_file = "study_data.json"
        self.gh = None
        self.repo = None
        self.setup_github()
    
    def setup_github(self):
        """设置 GitHub 连接"""
        try:
            if 'GITHUB_TOKEN' in st.secrets:
                self.gh = Github(st.secrets['GITHUB_TOKEN'])
                
                # 从 secrets 获取仓库信息，或使用默认值
                self.repo_owner = st.secrets.get('GITHUB_OWNER', '你的用户名')
                self.repo_name = st.secrets.get('GITHUB_REPO', 'study-analysis-app')
                
                self.repo = self.gh.get_repo(f"{self.repo_owner}/{self.repo_name}")
                st.sidebar.success("✅ GitHub 连接成功")
            else:
                st.sidebar.warning("⚠️ 未配置 GitHub Token，使用本地存储")
                
        except Exception as e:
            st.sidebar.error(f"❌ GitHub 连接失败: {e}")
    
    def is_connected(self):
        """检查是否成功连接到 GitHub"""
        return self.gh is not None and self.repo is not None
    
    def load_all_data(self):
        """从 GitHub 加载所有数据"""
        if not self.is_connected():
            return self._load_local_fallback()
        
        try:
            # 尝试从 GitHub 获取文件
            contents = self.repo.get_contents(self.data_file)
            file_content = base64.b64decode(contents.content).decode('utf-8')
            data = json.loads(file_content)
            
            # 同时更新本地 session state 作为缓存
            st.session_state.github_data_cache = data
            return data
            
        except GithubException as e:
            if e.status == 404:
                # 文件不存在，创建空数据结构
                st.info("📝 首次使用，创建新的数据文件")
                initial_data = []
                self._save_to_github(initial_data)
                return initial_data
            else:
                st.error(f"❌ 从 GitHub 加载数据失败: {e}")
                return self._load_local_fallback()
        except Exception as e:
            st.error(f"❌ 加载数据时出错: {e}")
            return self._load_local_fallback()
    
    def _load_local_fallback(self):
        """GitHub 不可用时使用本地回退"""
        return st.session_state.get('study_data', [])
    
    def _save_to_github(self, data):
        """保存数据到 GitHub"""
        try:
            content = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 检查文件是否存在
            try:
                contents = self.repo.get_contents(self.data_file)
                # 文件存在，更新它
                self.repo.update_file(
                    self.data_file,
                    f"更新学习数据 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content,
                    contents.sha
                )
            except GithubException:
                # 文件不存在，创建新文件
                self.repo.create_file(
                    self.data_file,
                    f"创建学习数据 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    content
                )
            
            return True
            
        except Exception as e:
            st.error(f"❌ 保存到 GitHub 失败: {e}")
            return False
    
    def add_daily_record(self, date, weather, energy_level, planned_tasks, actual_execution, daily_summary):
        """添加每日记录到 GitHub"""
        try:
            # 加载现有数据
            all_data = self.load_all_data()
            
            # 创建新记录
            new_record = {
                "date": date,
                "weather": weather,
                "energy_level": energy_level,
                "planned_tasks": planned_tasks,
                "actual_execution": actual_execution,
                "daily_summary": daily_summary,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 移除同一天的旧记录（如果存在）
            all_data = [record for record in all_data if record['date'] != date]
            
            # 添加新记录
            all_data.append(new_record)
            
            # 按日期排序
            all_data.sort(key=lambda x: x['date'], reverse=True)
            
            # 保存到 GitHub
            success = self._save_to_github(all_data)
            
            if success:
                # 更新本地缓存
                st.session_state.github_data_cache = all_data
                st.session_state.study_data = all_data
                
                # 记录同步状态
                st.session_state.last_sync = datetime.now().isoformat()
                
            return success
            
        except Exception as e:
            st.error(f"❌ 添加记录失败: {e}")
            return False
    
    def get_recent_data(self, days=30):
        """获取最近N天的数据"""
        data = self.load_all_data()
        if not data:
            return []
        
        return data[:days]
    
    def calculate_daily_metrics(self, day_data):
        """计算每日指标（与原有方法兼容）"""
        try:
            planned_total = day_data['daily_summary'].get('planned_total_time', 0)
            actual_total = day_data['daily_summary'].get('actual_total_time', 0)
            planned_focus = day_data['daily_summary'].get('planned_focus_time', 0)
            actual_focus = day_data['daily_summary'].get('actual_focus_time', 0)
            
            completion_rate = actual_total / planned_total if planned_total > 0 else 0
            focus_efficiency = actual_focus / actual_total if actual_total > 0 else 0
            planning_accuracy = 1 - abs(actual_total - planned_total) / planned_total if planned_total > 0 else 0
            
            return {
                'date': day_data['date'],
                'completion_rate': completion_rate,
                'focus_efficiency': focus_efficiency,
                'planning_accuracy': planning_accuracy,
                'total_focus_time': actual_focus
            }
        except Exception as e:
            print(f"计算指标时出错: {e}")
            return {
                'date': day_data['date'],
                'completion_rate': 0,
                'focus_efficiency': 0,
                'planning_accuracy': 0,
                'total_focus_time': 0
            }
    
    def get_subject_stats(self, data):
        """获取学科统计（与原有方法兼容）"""
        subject_stats = {}
        
        for day in data:
            for task in day.get('planned_tasks', []):
                subject = task.get('subject', 'other')
                if subject not in subject_stats:
                    subject_stats[subject] = {
                        'planned_time': 0,
                        'actual_time': 0
                    }
                
                # 计划时间
                subject_stats[subject]['planned_time'] += task.get('planned_duration', 0)
                
                # 实际时间
                task_id = task.get('task_id')
                actual_task = next(
                    (t for t in day.get('actual_execution', []) if t.get('task_id') == task_id),
                    None
                )
                if actual_task:
                    subject_stats[subject]['actual_time'] += actual_task.get('actual_duration', 0)
        
        return subject_stats
    
    def get_sync_status(self):
        """获取同步状态"""
        return {
            'connected': self.is_connected(),
            'last_sync': st.session_state.get('last_sync'),
            'repo_info': f"{self.repo_owner}/{self.repo_name}" if self.is_connected() else "未连接",
            'data_count': len(self.load_all_data())
        }
    
    def force_sync(self):
        """强制同步数据"""
        try:
            data = self.load_all_data()
            success = self._save_to_github(data)
            if success:
                st.session_state.last_sync = datetime.now().isoformat()
            return success
        except Exception as e:
            st.error(f"❌ 强制同步失败: {e}")
            return False
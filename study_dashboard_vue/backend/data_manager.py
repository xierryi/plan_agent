"""
数据管理器 - 独立版本
支持本地 JSON 存储和 GitHub 同步
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataManager:
    """本地 JSON 数据管理器"""
    
    def __init__(self, data_file: str = "study_data.json"):
        self.data_file = data_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def load_all_data(self) -> List[Dict]:
        """加载所有数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_all_data(self, data: List[Dict]) -> bool:
        """保存所有数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False
    
    def add_daily_record(self, date: str, weather: str, energy_level: int,
                        planned_tasks: List[Dict], actual_execution: List[Dict],
                        daily_summary: Dict) -> bool:
        """添加每日记录"""
        try:
            data = self.load_all_data()
            
            # 检查是否已存在该日期的记录
            existing_index = next((i for i, d in enumerate(data) if d['date'] == date), None)
            
            record = {
                "date": date,
                "weather": weather,
                "energy_level": energy_level,
                "planned_tasks": planned_tasks,
                "actual_execution": actual_execution,
                "daily_summary": daily_summary,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            if existing_index is not None:
                record["created_at"] = data[existing_index].get("created_at", record["created_at"])
                data[existing_index] = record
            else:
                data.append(record)
            
            # 按日期排序
            data.sort(key=lambda x: x['date'], reverse=True)
            
            return self.save_all_data(data)
        except Exception as e:
            logger.error(f"添加记录失败: {e}")
            return False
    
    def get_recent_data(self, days: int = 30) -> List[Dict]:
        """获取最近 N 天的数据"""
        all_data = self.load_all_data()
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return [d for d in all_data if d['date'] >= cutoff_date]
    
    def get_record_by_date(self, date: str) -> Optional[Dict]:
        """获取指定日期的记录"""
        all_data = self.load_all_data()
        return next((d for d in all_data if d['date'] == date), None)
    
    def get_subject_stats(self, data: List[Dict]) -> Dict[str, Dict]:
        """统计各学科数据"""
        stats = {}
        for record in data:
            for task in record.get('planned_tasks', []):
                subject = task.get('subject', 'other')
                if subject not in stats:
                    stats[subject] = {
                        'planned_time': 0,
                        'actual_time': 0,
                        'task_count': 0,
                        'completed_count': 0
                    }
                stats[subject]['planned_time'] += task.get('planned_duration', 0)
                stats[subject]['task_count'] += 1
            
            for exec_data in record.get('actual_execution', []):
                task = next((t for t in record.get('planned_tasks', []) 
                           if t.get('task_id') == exec_data.get('task_id')), {})
                subject = task.get('subject', 'other')
                if subject in stats:
                    stats[subject]['actual_time'] += exec_data.get('actual_duration', 0)
                    if exec_data.get('completed'):
                        stats[subject]['completed_count'] += 1
        
        return stats
    
    def calculate_daily_metrics(self, record: Dict) -> Dict:
        """计算单日指标"""
        planned_tasks = record.get('planned_tasks', [])
        actual_execution = record.get('actual_execution', [])
        summary = record.get('daily_summary', {})
        
        planned_total = sum(t.get('planned_duration', 0) for t in planned_tasks)
        actual_total = sum(e.get('actual_duration', 0) for e in actual_execution)
        completed = len([e for e in actual_execution if e.get('completed')])
        
        return {
            'date': record.get('date'),
            'completion_rate': completed / len(planned_tasks) if planned_tasks else 0,
            'focus_efficiency': actual_total / planned_total if planned_total > 0 else 0,
            'total_focus_time': actual_total,
            'planning_accuracy': 1 - abs(actual_total - planned_total) / planned_total if planned_total > 0 else 0,
            'task_count': len(planned_tasks),
            'completed_count': completed
        }
    
    def get_sync_status(self) -> Dict:
        """获取同步状态"""
        return {
            "connected": False,
            "repo_info": "本地存储",
            "data_count": len(self.load_all_data()),
            "last_sync": None
        }
    
    def force_sync(self) -> bool:
        """强制同步"""
        return True  # 本地存储无需同步


class GitHubDataManager(DataManager):
    """GitHub 数据管理器"""
    
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.owner = os.getenv('GITHUB_OWNER')
        self.repo = os.getenv('GITHUB_REPO')
        self.file_path = 'study_data.json'
        self.api_base = 'https://api.github.com'
        
        self._data_cache: List[Dict] = []
        self._last_sync: Optional[str] = None
        self._sha: Optional[str] = None
        
        # 初始化时加载数据
        if self.is_configured:
            self._load_from_github()
    
    @property
    def is_configured(self) -> bool:
        return all([self.token, self.owner, self.repo])
    
    @property
    def headers(self) -> Dict:
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def _load_from_github(self) -> bool:
        """从 GitHub 加载数据"""
        if not self.is_configured:
            return False
        
        try:
            url = f'{self.api_base}/repos/{self.owner}/{self.repo}/contents/{self.file_path}'
            response = httpx.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                content = response.json()
                self._sha = content['sha']
                import base64
                data_str = base64.b64decode(content['content']).decode('utf-8')
                self._data_cache = json.loads(data_str)
                self._last_sync = datetime.now().isoformat()
                logger.info(f"从 GitHub 加载了 {len(self._data_cache)} 条记录")
                return True
            elif response.status_code == 404:
                # 文件不存在，创建空数据
                self._data_cache = []
                self._save_to_github()
                return True
            else:
                logger.error(f"GitHub API 错误: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"从 GitHub 加载失败: {e}")
            return False
    
    def _save_to_github(self) -> bool:
        """保存数据到 GitHub"""
        if not self.is_configured:
            return False
        
        try:
            import base64
            content = base64.b64encode(
                json.dumps(self._data_cache, ensure_ascii=False, indent=2).encode('utf-8')
            ).decode('utf-8')
            
            url = f'{self.api_base}/repos/{self.owner}/{self.repo}/contents/{self.file_path}'
            
            data = {
                'message': f'Update study data - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'content': content
            }
            
            if self._sha:
                data['sha'] = self._sha
            
            response = httpx.put(url, headers=self.headers, json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                self._sha = response.json()['content']['sha']
                self._last_sync = datetime.now().isoformat()
                logger.info("数据已保存到 GitHub")
                return True
            else:
                logger.error(f"保存到 GitHub 失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"保存到 GitHub 失败: {e}")
            return False
    
    def load_all_data(self) -> List[Dict]:
        return self._data_cache
    
    def save_all_data(self, data: List[Dict]) -> bool:
        self._data_cache = data
        return self._save_to_github()
    
    def get_sync_status(self) -> Dict:
        return {
            "connected": self.is_configured,
            "repo_info": f"{self.owner}/{self.repo}" if self.is_configured else "",
            "data_count": len(self._data_cache),
            "last_sync": self._last_sync
        }
    
    def force_sync(self) -> bool:
        return self._save_to_github()


def get_data_manager() -> DataManager:
    """获取数据管理器实例"""
    if os.getenv('GITHUB_TOKEN') and os.getenv('GITHUB_OWNER') and os.getenv('GITHUB_REPO'):
        logger.info("使用 GitHub 数据管理器")
        return GitHubDataManager()
    else:
        logger.info("使用本地数据管理器")
        return DataManager()

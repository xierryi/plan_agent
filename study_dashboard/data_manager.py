import json
import pandas as pd
from datetime import datetime, timedelta
import os

datetime.now = lambda: __import__('datetime').datetime.now(__import__('pytz').timezone('Asia/Shanghai'))

class StudyDataManager:
    def __init__(self, data_file="study_data.jsonl"):
        self.data_file = data_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """确保数据文件存在"""
        if not os.path.exists(self.data_file):
            open(self.data_file, 'w').close()
    
    def add_daily_record(self, date, weather, energy_level, planned_tasks, actual_execution, daily_summary):
        """添加单日记录"""
        record = {
            "date": date,
            "weather": weather,
            "energy_level": energy_level,
            "planned_tasks": planned_tasks,
            "actual_execution": actual_execution,
            "daily_summary": daily_summary,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.data_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    
    def load_all_data(self):
        """加载所有历史数据"""
        data = []
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        except FileNotFoundError:
            pass
        return data
    
    def get_recent_data(self, days=30):
        """获取最近N天的数据"""
        all_data = self.load_all_data()
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return [d for d in all_data if d['date'] >= cutoff_date]
    
    def calculate_daily_metrics(self, data):
        """计算每日指标"""
        if not data:
            return {}
        
        summary = data['daily_summary']
        planned_total = summary['planned_total_time']
        actual_total = summary['actual_total_time']
        
        metrics = {
            'date': data['date'],
            'completion_rate': summary['completion_rate'],
            'focus_efficiency': summary['actual_focus_time'] / actual_total if actual_total > 0 else 0,
            'planning_accuracy': 1 - abs(planned_total - actual_total) / planned_total if planned_total > 0 else 0,
            'total_focus_time': summary['actual_focus_time'],
            'task_count': len(data['planned_tasks']),
            'completed_count': len([t for t in data['actual_execution'] if t.get('completed', True)])
        }
        return metrics
    
    def get_subject_stats(self, data):
        """按学科统计"""
        subject_stats = {}
        for day_data in data:
            for task in day_data['planned_tasks']:
                subject = task['subject']
                if subject not in subject_stats:
                    subject_stats[subject] = {'planned_time': 0, 'actual_time': 0, 'count': 0}
                
                subject_stats[subject]['planned_time'] += task['planned_duration']
                subject_stats[subject]['count'] += 1
            
            for task in day_data['actual_execution']:
                subject = next((t['subject'] for t in day_data['planned_tasks'] 
                              if t['task_id'] == task['task_id']), '未知')
                if subject in subject_stats:
                    subject_stats[subject]['actual_time'] += task['actual_duration']
        
        return subject_stats
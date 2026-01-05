"""
AI Agent 工具集 - 独立版本
提供数据查询和分析功能
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StudyTools:
    """学习分析工具集"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        
        # 学科名称映射
        self.subject_names = {
            'math': '数学',
            'physics': '物理',
            'econ': '经济学',
            'cs': '计算机',
            'other': '其他'
        }
    
    def get_tool_definitions(self) -> List[Dict]:
        """获取工具定义（OpenAI Function Calling 格式）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_weekly_stats",
                    "description": "获取最近一周的学习统计数据，包括总学习时间、完成率、各学科分布等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "统计的天数，默认7天",
                                "default": 7
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_subject_analysis",
                    "description": "分析特定学科的学习情况，包括时间投入、完成率、效率趋势",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "学科代码: math, physics, econ, cs, other",
                                "enum": ["math", "physics", "econ", "cs", "other"]
                            }
                        },
                        "required": ["subject"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_history",
                    "description": "查询指定日期范围的历史学习记录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "开始日期，格式 YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期，格式 YYYY-MM-DD"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_smart_plan",
                    "description": "基于历史数据智能生成学习计划",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "计划日期，格式 YYYY-MM-DD"
                            },
                            "total_hours": {
                                "type": "integer",
                                "description": "计划总学习时长（小时）",
                                "default": 4
                            },
                            "focus_subject": {
                                "type": "string",
                                "description": "重点学科（可选）",
                                "enum": ["math", "physics", "econ", "cs", "other"]
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_learning_pattern",
                    "description": "分析学习模式和规律，包括最佳学习时段、效率周期等",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_improvement_suggestions",
                    "description": "基于学习数据生成个性化改进建议",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """执行工具调用"""
        tool_map = {
            "get_weekly_stats": self.get_weekly_stats,
            "get_subject_analysis": self.get_subject_analysis,
            "query_history": self.query_history,
            "generate_smart_plan": self.generate_smart_plan,
            "analyze_learning_pattern": self.analyze_learning_pattern,
            "get_improvement_suggestions": self.get_improvement_suggestions
        }
        
        if tool_name not in tool_map:
            return {"success": False, "message": f"未知工具: {tool_name}"}
        
        try:
            return tool_map[tool_name](**arguments)
        except Exception as e:
            logger.error(f"工具执行错误 {tool_name}: {e}")
            return {"success": False, "message": str(e)}
    
    def get_weekly_stats(self, days: int = 7) -> Dict:
        """获取周度统计"""
        data = self.data_manager.get_recent_data(days)
        
        if not data:
            return {
                "success": True,
                "data": {
                    "total_days": 0,
                    "total_study_time": 0,
                    "avg_daily_time": 0,
                    "avg_completion_rate": 0,
                    "subject_distribution": {},
                    "message": "暂无学习记录"
                }
            }
        
        total_planned = 0
        total_actual = 0
        total_completed = 0
        total_tasks = 0
        subject_time = {}
        
        for record in data:
            for task in record.get('planned_tasks', []):
                total_planned += task.get('planned_duration', 0)
                subject = task.get('subject', 'other')
                subject_time[subject] = subject_time.get(subject, 0) + task.get('planned_duration', 0)
                total_tasks += 1
            
            for exec_data in record.get('actual_execution', []):
                total_actual += exec_data.get('actual_duration', 0)
                if exec_data.get('completed'):
                    total_completed += 1
        
        # 转换学科名称
        subject_dist = {
            self.subject_names.get(k, k): round(v / 60, 1)
            for k, v in subject_time.items()
        }
        
        return {
            "success": True,
            "data": {
                "total_days": len(data),
                "total_study_time": round(total_actual / 60, 1),
                "total_planned_time": round(total_planned / 60, 1),
                "avg_daily_time": round(total_actual / 60 / len(data), 1) if data else 0,
                "avg_completion_rate": round(total_completed / total_tasks * 100, 1) if total_tasks else 0,
                "total_tasks": total_tasks,
                "completed_tasks": total_completed,
                "subject_distribution": subject_dist
            }
        }
    
    def get_subject_analysis(self, subject: str) -> Dict:
        """分析特定学科"""
        data = self.data_manager.get_recent_data(30)
        
        subject_data = {
            "total_time": 0,
            "planned_time": 0,
            "task_count": 0,
            "completed_count": 0,
            "avg_difficulty": 0,
            "daily_records": []
        }
        
        difficulties = []
        
        for record in data:
            day_time = 0
            for task in record.get('planned_tasks', []):
                if task.get('subject') == subject:
                    subject_data['planned_time'] += task.get('planned_duration', 0)
                    subject_data['task_count'] += 1
                    difficulties.append(task.get('difficulty', 3))
            
            for exec_data in record.get('actual_execution', []):
                task = next((t for t in record.get('planned_tasks', [])
                           if t.get('task_id') == exec_data.get('task_id') 
                           and t.get('subject') == subject), None)
                if task:
                    actual_time = exec_data.get('actual_duration', 0)
                    subject_data['total_time'] += actual_time
                    day_time += actual_time
                    if exec_data.get('completed'):
                        subject_data['completed_count'] += 1
            
            if day_time > 0:
                subject_data['daily_records'].append({
                    'date': record['date'],
                    'time': day_time
                })
        
        subject_data['avg_difficulty'] = round(sum(difficulties) / len(difficulties), 1) if difficulties else 0
        subject_data['completion_rate'] = round(
            subject_data['completed_count'] / subject_data['task_count'] * 100, 1
        ) if subject_data['task_count'] else 0
        
        return {
            "success": True,
            "data": {
                "subject": subject,
                "subject_name": self.subject_names.get(subject, subject),
                "total_time_hours": round(subject_data['total_time'] / 60, 1),
                "planned_time_hours": round(subject_data['planned_time'] / 60, 1),
                "task_count": subject_data['task_count'],
                "completed_count": subject_data['completed_count'],
                "completion_rate": subject_data['completion_rate'],
                "avg_difficulty": subject_data['avg_difficulty'],
                "recent_trend": subject_data['daily_records'][-7:]
            }
        }
    
    def query_history(self, start_date: str = None, end_date: str = None) -> Dict:
        """查询历史记录"""
        all_data = self.data_manager.load_all_data()
        
        if start_date:
            all_data = [d for d in all_data if d['date'] >= start_date]
        if end_date:
            all_data = [d for d in all_data if d['date'] <= end_date]
        
        # 简化返回数据
        records = []
        for record in all_data[:10]:  # 最多返回10条
            summary = record.get('daily_summary', {})
            records.append({
                'date': record['date'],
                'weather': record.get('weather'),
                'energy_level': record.get('energy_level'),
                'task_count': len(record.get('planned_tasks', [])),
                'completed_count': len([e for e in record.get('actual_execution', []) if e.get('completed')]),
                'total_time': summary.get('actual_total_time', 0),
                'completion_rate': summary.get('completion_rate', 0)
            })
        
        return {
            "success": True,
            "data": {
                "total_records": len(all_data),
                "records": records
            }
        }
    
    def generate_smart_plan(self, date: str = None, total_hours: int = 4, 
                           focus_subject: str = None) -> Dict:
        """生成智能计划"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 获取历史数据分析学习模式
        recent_data = self.data_manager.get_recent_data(14)
        subject_stats = self.data_manager.get_subject_stats(recent_data) if recent_data else {}
        
        # 默认学科时间分配
        default_distribution = {
            'math': 0.3,
            'physics': 0.25,
            'econ': 0.2,
            'cs': 0.15,
            'other': 0.1
        }
        
        # 如果有重点学科，调整分配
        if focus_subject:
            for key in default_distribution:
                if key == focus_subject:
                    default_distribution[key] = 0.4
                else:
                    default_distribution[key] *= 0.6 / 0.7
        
        # 生成任务
        tasks = []
        total_minutes = total_hours * 60
        start_hour = 9
        
        for subject, ratio in default_distribution.items():
            duration = int(total_minutes * ratio)
            if duration >= 30:  # 至少30分钟才安排
                end_hour = start_hour + duration // 60
                end_minute = duration % 60
                
                tasks.append({
                    'subject': subject,
                    'subject_name': self.subject_names.get(subject, subject),
                    'duration_minutes': duration,
                    'start_time': f"{start_hour:02d}:00",
                    'end_time': f"{end_hour:02d}:{end_minute:02d}",
                    'difficulty': 3
                })
                
                start_hour = end_hour + (1 if end_minute > 0 else 0)
        
        tips = [
            "建议每学习50分钟休息10分钟",
            "保持充足的水分摄入",
            "学习环境保持安静整洁"
        ]
        
        if focus_subject:
            tips.insert(0, f"今日重点关注{self.subject_names.get(focus_subject, focus_subject)}")
        
        return {
            "success": True,
            "data": {
                "date": date,
                "total_hours": total_hours,
                "tasks": tasks,
                "tips": tips
            }
        }
    
    def analyze_learning_pattern(self) -> Dict:
        """分析学习模式"""
        data = self.data_manager.get_recent_data(30)
        
        if len(data) < 3:
            return {
                "success": True,
                "data": {
                    "message": "数据不足，需要至少3天的记录才能分析学习模式",
                    "patterns": []
                }
            }
        
        # 分析完成率趋势
        completion_rates = []
        daily_times = []
        
        for record in data:
            metrics = self.data_manager.calculate_daily_metrics(record)
            completion_rates.append(metrics['completion_rate'])
            daily_times.append(metrics['total_focus_time'])
        
        avg_completion = sum(completion_rates) / len(completion_rates)
        avg_daily_time = sum(daily_times) / len(daily_times)
        
        patterns = []
        
        # 完成率分析
        if avg_completion >= 0.8:
            patterns.append("✅ 任务完成率优秀，保持当前节奏")
        elif avg_completion >= 0.6:
            patterns.append("📊 任务完成率良好，可适当增加挑战")
        else:
            patterns.append("⚠️ 任务完成率偏低，建议减少每日任务量")
        
        # 时间分析
        if avg_daily_time >= 180:
            patterns.append(f"⏰ 日均学习{avg_daily_time/60:.1f}小时，学习强度较高")
        elif avg_daily_time >= 60:
            patterns.append(f"⏰ 日均学习{avg_daily_time/60:.1f}小时，学习节奏适中")
        else:
            patterns.append(f"⏰ 日均学习{avg_daily_time/60:.1f}小时，建议增加学习时间")
        
        return {
            "success": True,
            "data": {
                "total_days_analyzed": len(data),
                "avg_completion_rate": round(avg_completion * 100, 1),
                "avg_daily_time_minutes": round(avg_daily_time),
                "patterns": patterns
            }
        }
    
    def get_improvement_suggestions(self) -> Dict:
        """获取改进建议"""
        data = self.data_manager.get_recent_data(14)
        
        if not data:
            return {
                "success": True,
                "data": {
                    "suggestions": ["开始记录学习数据，积累足够数据后将提供个性化建议"]
                }
            }
        
        suggestions = []
        
        # 分析数据
        total_completion = 0
        subject_times = {}
        
        for record in data:
            metrics = self.data_manager.calculate_daily_metrics(record)
            total_completion += metrics['completion_rate']
            
            for task in record.get('planned_tasks', []):
                subject = task.get('subject', 'other')
                subject_times[subject] = subject_times.get(subject, 0) + task.get('planned_duration', 0)
        
        avg_completion = total_completion / len(data)
        
        # 生成建议
        if avg_completion < 0.7:
            suggestions.append("📋 当前任务完成率较低，建议适当减少每日计划任务数量，确保核心任务优先完成")
        
        if subject_times:
            max_subject = max(subject_times, key=subject_times.get)
            min_subject = min(subject_times, key=subject_times.get)
            if subject_times[max_subject] > subject_times[min_subject] * 3:
                suggestions.append(f"⚖️ 学科时间分配不均衡，{self.subject_names.get(min_subject, min_subject)}投入时间较少，建议适当增加")
        
        suggestions.append("💡 尝试使用番茄工作法，每25分钟专注学习后休息5分钟")
        suggestions.append("📝 养成每日反思的习惯，记录学习中的困难和收获")
        
        return {
            "success": True,
            "data": {
                "based_on_days": len(data),
                "suggestions": suggestions[:5]
            }
        }

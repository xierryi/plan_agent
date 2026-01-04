"""
学习助手工具集 - 供 AI Agent 调用的工具函数
"""
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any


class StudyTools:
    """学习助手工具集"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    # ==================== 工具定义（供 OpenAI Function Calling 使用）====================
    
    @staticmethod
    def get_tool_definitions() -> List[Dict]:
        """返回所有工具的定义，供 OpenAI Function Calling 使用"""
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
                                "description": "统计天数，默认7天",
                                "default": 7
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_subject_analysis",
                    "description": "分析特定学科的学习情况，包括学习时间、完成率、效率趋势",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "学科名称，可选：math(数学), physics(物理), econ(经济), cs(计算机), other(其他)",
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
                    "description": "查询特定日期或日期范围的学习记录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "查询日期，格式：YYYY-MM-DD"
                            },
                            "days_range": {
                                "type": "integer",
                                "description": "查询天数范围（从今天往前），与date二选一"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_smart_plan",
                    "description": "基于历史数据智能生成学习计划，考虑学科平衡、效率模式、难度分配",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "计划日期，格式：YYYY-MM-DD，默认明天"
                            },
                            "total_hours": {
                                "type": "number",
                                "description": "计划总学习时长（小时），默认4小时"
                            },
                            "focus_subject": {
                                "type": "string",
                                "description": "重点学科（可选）",
                                "enum": ["math", "physics", "econ", "cs", "other"]
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_learning_pattern",
                    "description": "分析学习模式，发现效率高峰时段、薄弱环节、进步趋势",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "aspect": {
                                "type": "string",
                                "description": "分析角度",
                                "enum": ["time_pattern", "efficiency", "completion", "all"]
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_improvement_suggestions",
                    "description": "基于数据分析获取个性化改进建议",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "focus_area": {
                                "type": "string",
                                "description": "关注领域",
                                "enum": ["efficiency", "time_management", "subject_balance", "general"]
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_periods",
                    "description": "对比两个时间段的学习表现",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period1_days": {
                                "type": "integer",
                                "description": "第一个时间段（最近N天）",
                                "default": 7
                            },
                            "period2_days": {
                                "type": "integer",
                                "description": "第二个时间段（再往前N天）",
                                "default": 7
                            }
                        },
                        "required": []
                    }
                }
            }
        ]
    
    # ==================== 工具实现 ====================
    
    def get_weekly_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取最近N天的学习统计"""
        data = self.data_manager.get_recent_data(days)
        
        if not data:
            return {
                "success": False,
                "message": f"最近{days}天没有学习记录",
                "data": None
            }
        
        total_planned_time = 0
        total_actual_time = 0
        total_tasks = 0
        completed_tasks = 0
        subject_times = {}
        daily_stats = []
        
        for day_data in data:
            summary = day_data.get('daily_summary', {})
            total_planned_time += summary.get('planned_total_time', 0)
            total_actual_time += summary.get('actual_total_time', 0)
            
            planned_tasks = day_data.get('planned_tasks', [])
            actual_execution = day_data.get('actual_execution', [])
            
            total_tasks += len(planned_tasks)
            completed_tasks += len([e for e in actual_execution if e.get('completed', True)])
            
            # 统计各学科时间
            for task in planned_tasks:
                subject = task.get('subject', 'other')
                if subject not in subject_times:
                    subject_times[subject] = {'planned': 0, 'actual': 0}
                subject_times[subject]['planned'] += task.get('planned_duration', 0)
            
            for i, execution in enumerate(actual_execution):
                if i < len(planned_tasks):
                    subject = planned_tasks[i].get('subject', 'other')
                    if subject in subject_times:
                        subject_times[subject]['actual'] += execution.get('actual_duration', 0)
            
            daily_stats.append({
                'date': day_data['date'],
                'planned_time': summary.get('planned_total_time', 0),
                'actual_time': summary.get('actual_total_time', 0),
                'completion_rate': summary.get('completion_rate', 0)
            })
        
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        efficiency = total_actual_time / total_planned_time if total_planned_time > 0 else 0
        
        return {
            "success": True,
            "message": f"最近{days}天学习统计",
            "data": {
                "period": f"最近{days}天",
                "record_count": len(data),
                "total_planned_time_hours": round(total_planned_time / 60, 1),
                "total_actual_time_hours": round(total_actual_time / 60, 1),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": f"{completion_rate:.1%}",
                "time_efficiency": f"{efficiency:.1%}",
                "avg_daily_time_hours": round(total_actual_time / 60 / len(data), 1) if data else 0,
                "subject_distribution": subject_times,
                "daily_trend": daily_stats[-5:]  # 最近5天趋势
            }
        }
    
    def get_subject_analysis(self, subject: str) -> Dict[str, Any]:
        """分析特定学科的学习情况"""
        data = self.data_manager.get_recent_data(30)
        
        if not data:
            return {
                "success": False,
                "message": "没有足够的学习记录进行分析",
                "data": None
            }
        
        subject_names = {
            'math': '数学',
            'physics': '物理',
            'econ': '经济学',
            'cs': '计算机科学',
            'other': '其他'
        }
        
        subject_data = {
            'total_planned_time': 0,
            'total_actual_time': 0,
            'task_count': 0,
            'completed_count': 0,
            'difficulty_sum': 0,
            'daily_records': []
        }
        
        for day_data in data:
            planned_tasks = day_data.get('planned_tasks', [])
            actual_execution = day_data.get('actual_execution', [])
            
            day_planned = 0
            day_actual = 0
            
            for i, task in enumerate(planned_tasks):
                if task.get('subject') == subject:
                    subject_data['task_count'] += 1
                    subject_data['total_planned_time'] += task.get('planned_duration', 0)
                    subject_data['difficulty_sum'] += task.get('difficulty', 3)
                    day_planned += task.get('planned_duration', 0)
                    
                    if i < len(actual_execution):
                        execution = actual_execution[i]
                        subject_data['total_actual_time'] += execution.get('actual_duration', 0)
                        day_actual += execution.get('actual_duration', 0)
                        if execution.get('completed', True):
                            subject_data['completed_count'] += 1
            
            if day_planned > 0:
                subject_data['daily_records'].append({
                    'date': day_data['date'],
                    'planned': day_planned,
                    'actual': day_actual
                })
        
        if subject_data['task_count'] == 0:
            return {
                "success": False,
                "message": f"没有{subject_names.get(subject, subject)}的学习记录",
                "data": None
            }
        
        avg_difficulty = subject_data['difficulty_sum'] / subject_data['task_count']
        completion_rate = subject_data['completed_count'] / subject_data['task_count']
        time_efficiency = subject_data['total_actual_time'] / subject_data['total_planned_time'] if subject_data['total_planned_time'] > 0 else 0
        
        return {
            "success": True,
            "message": f"{subject_names.get(subject, subject)}学习分析",
            "data": {
                "subject": subject_names.get(subject, subject),
                "total_tasks": subject_data['task_count'],
                "completed_tasks": subject_data['completed_count'],
                "total_planned_hours": round(subject_data['total_planned_time'] / 60, 1),
                "total_actual_hours": round(subject_data['total_actual_time'] / 60, 1),
                "completion_rate": f"{completion_rate:.1%}",
                "time_efficiency": f"{time_efficiency:.1%}",
                "avg_difficulty": round(avg_difficulty, 1),
                "recent_trend": subject_data['daily_records'][-7:]  # 最近7天趋势
            }
        }
    
    def query_history(self, date: Optional[str] = None, days_range: Optional[int] = None) -> Dict[str, Any]:
        """查询历史记录"""
        if date:
            # 查询特定日期
            all_data = self.data_manager.load_all_data()
            day_data = next((d for d in all_data if d['date'] == date), None)
            
            if not day_data:
                return {
                    "success": False,
                    "message": f"{date} 没有学习记录",
                    "data": None
                }
            
            return {
                "success": True,
                "message": f"{date} 学习记录",
                "data": {
                    "date": day_data['date'],
                    "weather": day_data.get('weather', '未记录'),
                    "energy_level": day_data.get('energy_level', '未记录'),
                    "tasks": [{
                        "name": t.get('task_name'),
                        "subject": t.get('subject'),
                        "planned_duration": t.get('planned_duration'),
                        "time_range": f"{t.get('planned_start_time', '?')} - {t.get('planned_end_time', '?')}"
                    } for t in day_data.get('planned_tasks', [])],
                    "summary": day_data.get('daily_summary', {}),
                    "reflection": day_data.get('daily_summary', {}).get('reflection', '无')
                }
            }
        else:
            # 查询日期范围
            days = days_range or 7
            data = self.data_manager.get_recent_data(days)
            
            if not data:
                return {
                    "success": False,
                    "message": f"最近{days}天没有学习记录",
                    "data": None
                }
            
            records = []
            for day_data in data:
                summary = day_data.get('daily_summary', {})
                records.append({
                    "date": day_data['date'],
                    "task_count": len(day_data.get('planned_tasks', [])),
                    "total_time_hours": round(summary.get('actual_total_time', 0) / 60, 1),
                    "completion_rate": f"{summary.get('completion_rate', 0):.1%}"
                })
            
            return {
                "success": True,
                "message": f"最近{days}天学习记录概览",
                "data": {
                    "record_count": len(records),
                    "records": records
                }
            }
    
    def generate_smart_plan(self, date: Optional[str] = None, total_hours: float = 4, 
                           focus_subject: Optional[str] = None) -> Dict[str, Any]:
        """智能生成学习计划"""
        # 获取历史数据进行分析
        history = self.data_manager.get_recent_data(14)
        
        if not history:
            # 没有历史数据，生成默认计划
            return self._generate_default_plan(date, total_hours, focus_subject)
        
        # 分析历史模式
        subject_stats = self.data_manager.get_subject_stats(history)
        
        # 计算各学科需要的时间
        total_minutes = int(total_hours * 60)
        subjects_to_plan = []
        
        # 确定需要安排的学科
        if focus_subject:
            subjects_to_plan.append({
                'subject': focus_subject,
                'weight': 0.4,  # 重点学科占40%
                'reason': '用户指定的重点学科'
            })
            remaining_weight = 0.6
        else:
            remaining_weight = 1.0
        
        # 根据历史数据分析薄弱学科
        for subject, stats in subject_stats.items():
            if focus_subject and subject == focus_subject:
                continue
            
            efficiency = stats['actual_time'] / stats['planned_time'] if stats['planned_time'] > 0 else 0
            
            subjects_to_plan.append({
                'subject': subject,
                'weight': remaining_weight / len(subject_stats),
                'efficiency': efficiency,
                'reason': '效率较低需加强' if efficiency < 0.8 else '保持学习'
            })
        
        # 生成具体任务
        plan_date = date or (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        tasks = []
        start_hour = 9  # 默认从9点开始
        
        subject_names = {
            'math': '数学',
            'physics': '物理', 
            'econ': '经济学',
            'cs': '计算机',
            'other': '其他'
        }
        
        for item in subjects_to_plan[:4]:  # 最多4个任务
            duration = int(total_minutes * item['weight'])
            if duration < 30:
                duration = 30  # 最少30分钟
            
            tasks.append({
                'subject': item['subject'],
                'subject_name': subject_names.get(item['subject'], item['subject']),
                'duration_minutes': duration,
                'start_time': f"{start_hour:02d}:00",
                'end_time': f"{start_hour + duration // 60:02d}:{duration % 60:02d}",
                'difficulty': 3,
                'reason': item.get('reason', '')
            })
            
            start_hour += duration // 60 + 1  # 加1小时休息
        
        return {
            "success": True,
            "message": f"{plan_date} 智能学习计划",
            "data": {
                "date": plan_date,
                "total_hours": total_hours,
                "task_count": len(tasks),
                "tasks": tasks,
                "tips": [
                    "建议每学习50分钟休息10分钟",
                    "上午精力充沛，适合难度较高的任务",
                    "保持充足睡眠有助于提高学习效率"
                ]
            }
        }
    
    def _generate_default_plan(self, date: Optional[str], total_hours: float, 
                               focus_subject: Optional[str]) -> Dict[str, Any]:
        """生成默认计划（无历史数据时）"""
        plan_date = date or (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        total_minutes = int(total_hours * 60)
        
        default_subjects = ['math', 'physics', 'cs'] if not focus_subject else [focus_subject, 'math', 'physics']
        
        tasks = []
        start_hour = 9
        time_per_task = total_minutes // len(default_subjects)
        
        subject_names = {
            'math': '数学',
            'physics': '物理',
            'econ': '经济学', 
            'cs': '计算机',
            'other': '其他'
        }
        
        for subject in default_subjects:
            tasks.append({
                'subject': subject,
                'subject_name': subject_names.get(subject, subject),
                'duration_minutes': time_per_task,
                'start_time': f"{start_hour:02d}:00",
                'end_time': f"{start_hour + time_per_task // 60:02d}:{time_per_task % 60:02d}",
                'difficulty': 3,
                'reason': '均衡分配'
            })
            start_hour += time_per_task // 60 + 1
        
        return {
            "success": True,
            "message": f"{plan_date} 学习计划（默认模板）",
            "data": {
                "date": plan_date,
                "total_hours": total_hours,
                "task_count": len(tasks),
                "tasks": tasks,
                "tips": [
                    "这是默认计划模板",
                    "随着学习记录积累，AI会提供更个性化的建议",
                    "建议先记录几天学习数据"
                ]
            }
        }
    
    def analyze_learning_pattern(self, aspect: str = "all") -> Dict[str, Any]:
        """分析学习模式"""
        data = self.data_manager.get_recent_data(30)
        
        if len(data) < 3:
            return {
                "success": False,
                "message": "需要至少3天的数据才能分析学习模式",
                "data": None
            }
        
        analysis = {}
        
        # 时间模式分析
        if aspect in ["time_pattern", "all"]:
            time_slots = {'morning': 0, 'afternoon': 0, 'evening': 0}
            
            for day_data in data:
                for task in day_data.get('planned_tasks', []):
                    start_time = task.get('planned_start_time', '09:00')
                    if isinstance(start_time, str):
                        hour = int(start_time.split(':')[0])
                    else:
                        hour = start_time.hour if hasattr(start_time, 'hour') else 9
                    
                    duration = task.get('planned_duration', 60)
                    
                    if hour < 12:
                        time_slots['morning'] += duration
                    elif hour < 18:
                        time_slots['afternoon'] += duration
                    else:
                        time_slots['evening'] += duration
            
            total = sum(time_slots.values())
            analysis['time_pattern'] = {
                'morning_ratio': f"{time_slots['morning']/total:.1%}" if total > 0 else "0%",
                'afternoon_ratio': f"{time_slots['afternoon']/total:.1%}" if total > 0 else "0%",
                'evening_ratio': f"{time_slots['evening']/total:.1%}" if total > 0 else "0%",
                'peak_time': max(time_slots, key=time_slots.get),
                'suggestion': self._get_time_suggestion(time_slots)
            }
        
        # 效率分析
        if aspect in ["efficiency", "all"]:
            efficiencies = []
            for day_data in data:
                summary = day_data.get('daily_summary', {})
                planned = summary.get('planned_total_time', 0)
                actual = summary.get('actual_total_time', 0)
                if planned > 0:
                    efficiencies.append(actual / planned)
            
            if efficiencies:
                avg_eff = sum(efficiencies) / len(efficiencies)
                trend = efficiencies[-1] - efficiencies[0] if len(efficiencies) > 1 else 0
                
                analysis['efficiency'] = {
                    'average': f"{avg_eff:.1%}",
                    'trend': '上升' if trend > 0.05 else '下降' if trend < -0.05 else '稳定',
                    'best_day': max(range(len(efficiencies)), key=lambda i: efficiencies[i]),
                    'suggestion': '效率良好，继续保持' if avg_eff > 0.8 else '建议适当调整计划难度'
                }
        
        # 完成率分析
        if aspect in ["completion", "all"]:
            completion_rates = []
            for day_data in data:
                summary = day_data.get('daily_summary', {})
                completion_rates.append(summary.get('completion_rate', 0))
            
            if completion_rates:
                avg_completion = sum(completion_rates) / len(completion_rates)
                analysis['completion'] = {
                    'average': f"{avg_completion:.1%}",
                    'consistency': '稳定' if max(completion_rates) - min(completion_rates) < 0.3 else '波动较大',
                    'suggestion': '完成率良好' if avg_completion > 0.8 else '建议设置更合理的任务目标'
                }
        
        return {
            "success": True,
            "message": "学习模式分析",
            "data": analysis
        }
    
    def _get_time_suggestion(self, time_slots: Dict) -> str:
        """根据时间分布给出建议"""
        peak = max(time_slots, key=time_slots.get)
        if peak == 'morning':
            return "您是早起型学习者，建议把重要任务安排在上午"
        elif peak == 'afternoon':
            return "您下午学习效率较高，建议保持这个节奏"
        else:
            return "您偏向晚间学习，注意保证充足睡眠"
    
    def get_improvement_suggestions(self, focus_area: str = "general") -> Dict[str, Any]:
        """获取改进建议"""
        data = self.data_manager.get_recent_data(14)
        
        if len(data) < 3:
            return {
                "success": True,
                "message": "改进建议",
                "data": {
                    "suggestions": [
                        "📊 继续积累学习数据，AI会提供更精准的建议",
                        "⏰ 建议每天固定时间进行学习",
                        "📝 记录学习反思有助于持续改进"
                    ]
                }
            }
        
        suggestions = []
        
        # 分析数据生成建议
        stats = self.get_weekly_stats(7)
        if stats['success']:
            stat_data = stats['data']
            
            # 完成率建议
            completion = float(stat_data['completion_rate'].rstrip('%')) / 100
            if completion < 0.7:
                suggestions.append("📉 完成率较低，建议减少每日任务数量或降低难度")
            elif completion > 0.95:
                suggestions.append("🎯 完成率很高！可以尝试增加一些挑战性任务")
            
            # 时间效率建议
            efficiency = float(stat_data['time_efficiency'].rstrip('%')) / 100
            if efficiency < 0.8:
                suggestions.append("⏱️ 实际用时少于计划，建议更精确估算任务时间")
            elif efficiency > 1.2:
                suggestions.append("⚠️ 实际用时超出计划较多，建议预留更多缓冲时间")
            
            # 学科平衡建议
            subjects = stat_data.get('subject_distribution', {})
            if subjects:
                max_subject = max(subjects.items(), key=lambda x: x[1].get('actual', 0))
                min_subject = min(subjects.items(), key=lambda x: x[1].get('actual', 0))
                if max_subject[1].get('actual', 0) > 3 * min_subject[1].get('actual', 1):
                    suggestions.append(f"📚 学科分配不均衡，{min_subject[0]}学习时间较少，建议适当增加")
        
        # 通用建议
        if len(suggestions) < 3:
            general_suggestions = [
                "🌟 设置明确的学习目标有助于提高效率",
                "💪 保持规律的作息对学习效率很重要",
                "📱 学习时减少手机干扰可以提高专注度",
                "🎵 找到适合自己的学习环境和背景音乐",
                "📖 定期复习可以巩固学习成果"
            ]
            suggestions.extend(general_suggestions[:3-len(suggestions)])
        
        return {
            "success": True,
            "message": "个性化改进建议",
            "data": {
                "focus_area": focus_area,
                "suggestions": suggestions[:5],
                "data_based": len(data) >= 3
            }
        }
    
    def compare_periods(self, period1_days: int = 7, period2_days: int = 7) -> Dict[str, Any]:
        """对比两个时间段的学习表现"""
        all_data = self.data_manager.get_recent_data(period1_days + period2_days)
        
        if len(all_data) < period1_days:
            return {
                "success": False,
                "message": f"数据不足，需要至少{period1_days + period2_days}天的记录",
                "data": None
            }
        
        # 分割数据
        recent_data = all_data[-period1_days:]
        previous_data = all_data[-(period1_days + period2_days):-period1_days]
        
        def calculate_period_stats(data):
            if not data:
                return None
            total_time = 0
            total_tasks = 0
            completed = 0
            
            for day in data:
                summary = day.get('daily_summary', {})
                total_time += summary.get('actual_total_time', 0)
                total_tasks += len(day.get('planned_tasks', []))
                completed += len([e for e in day.get('actual_execution', []) if e.get('completed', True)])
            
            return {
                'total_hours': round(total_time / 60, 1),
                'avg_daily_hours': round(total_time / 60 / len(data), 1),
                'total_tasks': total_tasks,
                'completed_tasks': completed,
                'completion_rate': completed / total_tasks if total_tasks > 0 else 0
            }
        
        recent_stats = calculate_period_stats(recent_data)
        previous_stats = calculate_period_stats(previous_data)
        
        if not previous_stats:
            return {
                "success": False,
                "message": "对比期间数据不足",
                "data": None
            }
        
        # 计算变化
        time_change = recent_stats['total_hours'] - previous_stats['total_hours']
        completion_change = recent_stats['completion_rate'] - previous_stats['completion_rate']
        
        return {
            "success": True,
            "message": f"最近{period1_days}天 vs 之前{period2_days}天对比",
            "data": {
                "recent_period": {
                    "days": period1_days,
                    **recent_stats,
                    "completion_rate": f"{recent_stats['completion_rate']:.1%}"
                },
                "previous_period": {
                    "days": period2_days,
                    **previous_stats,
                    "completion_rate": f"{previous_stats['completion_rate']:.1%}"
                },
                "changes": {
                    "time_change_hours": round(time_change, 1),
                    "time_trend": "增加" if time_change > 0 else "减少" if time_change < 0 else "持平",
                    "completion_change": f"{completion_change:+.1%}",
                    "completion_trend": "提升" if completion_change > 0.05 else "下降" if completion_change < -0.05 else "稳定"
                },
                "summary": self._generate_comparison_summary(recent_stats, previous_stats)
            }
        }
    
    def _generate_comparison_summary(self, recent: Dict, previous: Dict) -> str:
        """生成对比总结"""
        time_diff = recent['total_hours'] - previous['total_hours']
        completion_diff = recent['completion_rate'] - previous['completion_rate']
        
        if time_diff > 2 and completion_diff > 0.05:
            return "🎉 表现优秀！学习时间增加且完成率提升，继续保持！"
        elif time_diff > 2 and completion_diff < -0.05:
            return "⚠️ 学习时间增加但完成率下降，建议检查任务难度是否合理"
        elif time_diff < -2 and completion_diff > 0.05:
            return "💡 效率提升！用更少时间完成更多任务"
        elif time_diff < -2 and completion_diff < -0.05:
            return "📉 学习时间和完成率都有下降，需要调整学习计划"
        else:
            return "📊 整体表现稳定，可以尝试设定新的挑战目标"
    
    # ==================== 工具调用入口 ====================
    
    def execute_tool(self, tool_name: str, arguments: Dict) -> Dict[str, Any]:
        """执行工具"""
        tool_map = {
            'get_weekly_stats': self.get_weekly_stats,
            'get_subject_analysis': self.get_subject_analysis,
            'query_history': self.query_history,
            'generate_smart_plan': self.generate_smart_plan,
            'analyze_learning_pattern': self.analyze_learning_pattern,
            'get_improvement_suggestions': self.get_improvement_suggestions,
            'compare_periods': self.compare_periods
        }
        
        if tool_name not in tool_map:
            return {
                "success": False,
                "message": f"未知工具: {tool_name}",
                "data": None
            }
        
        try:
            return tool_map[tool_name](**arguments)
        except Exception as e:
            return {
                "success": False,
                "message": f"工具执行错误: {str(e)}",
                "data": None
            }


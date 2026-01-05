"""
StudyAgent 后端 API 服务
FastAPI + OpenAI Function Calling
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="StudyAgent API",
    description="智能学习效率分析 AI Agent 后端服务",
    version="2.0.0"
)

# CORS 配置 - 支持环境变量配置允许的域名
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
# 生产环境添加 Vercel 域名
if os.getenv("RENDER"):
    allowed_origins.extend([
        "https://*.vercel.app",
        "https://study-dashboard.vercel.app",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 暂时允许所有域名，生产环境可以限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入本地模块
from data_manager import get_data_manager, DataManager
from study_agent import StudyAgent
from tools import StudyTools

# 初始化
data_manager = get_data_manager()
agent = StudyAgent(data_manager)
tools = StudyTools(data_manager)

# 状态存储
state_cache: Dict[str, Dict] = {}


# ==================== 数据模型 ====================

class StateData(BaseModel):
    date: str
    planned_tasks: List[Dict] = []
    actual_execution: List[Dict] = []
    tasks_confirmed: bool = False
    tasks_saved: bool = False
    weather: str = "晴"
    energy_level: int = 7
    reflection: str = ""


class DailyRecordData(BaseModel):
    date: str
    weather: str
    energy_level: int
    planned_tasks: List[Dict]
    actual_execution: List[Dict]
    reflection: str = ""


class ChatMessage(BaseModel):
    message: str


class PlanRequest(BaseModel):
    total_hours: int = 4
    focus_subject: Optional[str] = None
    date: Optional[str] = None


# ==================== API 路由 ====================

@app.get("/")
async def root():
    return {"message": "StudyAgent API v2.0.0", "status": "running"}


# ---------- 状态管理 ----------

@app.get("/api/state/{date}")
async def get_state(date: str):
    """获取指定日期的状态"""
    if date in state_cache:
        return state_cache[date]
    return {
        "date": date,
        "planned_tasks": [],
        "actual_execution": [],
        "tasks_confirmed": False,
        "tasks_saved": False,
        "weather": "晴",
        "energy_level": 7,
        "reflection": ""
    }


@app.post("/api/state")
async def save_state(data: StateData):
    """保存状态"""
    state_cache[data.date] = data.model_dump()
    return {"success": True, "message": "状态已保存"}


# ---------- 学习记录 ----------

@app.post("/api/records")
async def save_daily_record(data: DailyRecordData):
    """保存每日学习记录"""
    try:
        # 计算汇总
        planned_total = sum(t.get('planned_duration', 0) for t in data.planned_tasks)
        actual_total = sum(e.get('actual_duration', 0) for e in data.actual_execution)
        completion_rate = len([e for e in data.actual_execution if e.get('completed')]) / len(data.planned_tasks) if data.planned_tasks else 0

        success = data_manager.add_daily_record(
            data.date,
            data.weather,
            data.energy_level,
            data.planned_tasks,
            data.actual_execution,
            {
                "planned_total_time": planned_total,
                "actual_total_time": actual_total,
                "planned_focus_time": int(planned_total * 0.8),
                "actual_focus_time": int(actual_total * 0.8),
                "completion_rate": completion_rate,
                "reflection": data.reflection
            }
        )
        
        if success:
            return {"success": True, "message": "记录已保存"}
        else:
            raise HTTPException(status_code=500, detail="保存失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/records")
async def get_history(days: int = 30):
    """获取历史记录"""
    try:
        data = data_manager.get_recent_data(days)
        return data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/records/{date}")
async def get_record_by_date(date: str):
    """获取指定日期的记录"""
    try:
        record = data_manager.get_record_by_date(date)
        if record:
            return record
        raise HTTPException(status_code=404, detail="记录不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/records/{date}")
async def delete_record(date: str):
    """删除指定日期的记录"""
    try:
        success = data_manager.delete_record(date)
        if success:
            # 同时清除状态缓存
            if date in state_cache:
                del state_cache[date]
            return {"success": True, "message": f"已删除 {date} 的记录"}
        raise HTTPException(status_code=404, detail="记录不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- 统计分析 ----------

@app.get("/api/stats/weekly")
async def get_weekly_stats():
    """获取周度统计"""
    try:
        result = tools.get_weekly_stats(days=7)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/subject/{subject}")
async def get_subject_analysis(subject: str):
    """获取学科分析"""
    try:
        result = tools.get_subject_analysis(subject=subject)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats/pattern")
async def get_pattern_analysis():
    """获取学习模式分析"""
    try:
        result = tools.analyze_learning_pattern()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- AI 助手 ----------

@app.post("/api/chat")
async def chat(data: ChatMessage):
    """AI 对话"""
    try:
        response = agent.chat(data.message)
        return {
            "message": response,
            "tool_calls": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/history")
async def clear_chat_history():
    """清除对话历史"""
    agent.clear_history()
    return {"success": True, "message": "对话历史已清除"}


@app.post("/api/plan/generate")
async def generate_plan(data: PlanRequest):
    """生成学习计划"""
    try:
        target_date = data.date or datetime.now().strftime("%Y-%m-%d")
        result = tools.generate_smart_plan(
            date=target_date,
            total_hours=data.total_hours,
            focus_subject=data.focus_subject
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- 同步 ----------

@app.get("/api/sync/status")
async def get_sync_status():
    """获取同步状态"""
    return data_manager.get_sync_status()


@app.post("/api/sync/github")
async def sync_to_github():
    """强制同步到 GitHub"""
    success = data_manager.force_sync()
    if success:
        return {"success": True, "message": "同步成功"}
    raise HTTPException(status_code=500, detail="同步失败")


# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    print("Starting StudyAgent API...")
    print("API docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

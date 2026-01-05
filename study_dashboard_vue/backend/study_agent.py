"""
学习分析 AI Agent - 独立版本
支持 OpenAI Function Calling
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StudyAgent:
    """学习分析 AI Agent"""
    
    def __init__(self, data_manager=None):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.model_name = os.getenv('MODEL_NAME', 'gpt-4o-mini')
        self.data_manager = data_manager
        self.tools = None
        
        if data_manager:
            from tools import StudyTools
            self.tools = StudyTools(data_manager)
        
        self.system_prompt = """你是一个专业的学习效率分析助手。你的任务是帮助用户分析学习数据、提供个性化建议、生成学习计划。

你可以使用以下工具来获取数据和执行操作：
1. get_weekly_stats - 获取最近一周学习统计
2. get_subject_analysis - 分析特定学科的学习情况
3. query_history - 查询历史学习记录
4. generate_smart_plan - 智能生成学习计划
5. analyze_learning_pattern - 分析学习模式
6. get_improvement_suggestions - 获取改进建议

请根据用户的问题，选择合适的工具获取数据，然后基于数据给出专业、具体、可操作的分析和建议。

回复要求：
- 使用中文回复
- 结构清晰，突出重点
- 基于数据事实，避免空泛建议
- 语气友好、鼓励性"""

        self.conversation_history: List[Dict] = []
    
    def set_data_manager(self, data_manager):
        """设置数据管理器"""
        self.data_manager = data_manager
        if data_manager:
            from tools import StudyTools
            self.tools = StudyTools(data_manager)
    
    def chat(self, user_message: str) -> str:
        """与 AI 对话"""
        if not self.tools:
            return "⚠️ 数据管理器未初始化，无法访问学习数据。"
        
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history[-10:]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self.tools.get_tool_definitions(),
                tool_choice="auto",
                temperature=0.3
            )
            
            assistant_message = response.choices[0].message
            
            if assistant_message.tool_calls:
                tool_results = []
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"调用工具: {function_name}, 参数: {function_args}")
                    
                    result = self.tools.execute_tool(function_name, function_args)
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in assistant_message.tool_calls
                    ]
                })
                messages.extend(tool_results)
                
                final_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.3
                )
                
                final_content = final_response.choices[0].message.content
            else:
                final_content = assistant_message.content
            
            self.conversation_history.append({
                "role": "assistant",
                "content": final_content
            })
            
            return final_content
            
        except Exception as e:
            logger.error(f"对话错误: {str(e)}")
            return f"抱歉，发生了错误: {str(e)}"
    
    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = []
    
    def analyze_weekly_trends(self, weekly_data: List[Dict]) -> str:
        """分析周度趋势"""
        if len(weekly_data) < 3:
            return "数据不足，请继续积累几天数据后再进行分析。"
        
        context = f"""
        用户最近{len(weekly_data)}天的学习数据如下：
        {json.dumps(weekly_data, ensure_ascii=False, indent=2)}
        
        请从以下角度进行分析：
        1. **效率趋势**：专注效率和任务完成率的变化趋势
        2. **时间管理**：计划准确性和时间分配合理性
        3. **学科表现**：不同学科的学习效果对比
        4. **具体建议**：基于发现的问题给出3条具体改进建议
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"分析服务暂时不可用: {str(e)}"
    
    def generate_tomorrow_plan(self, recent_data: List[Dict]) -> str:
        """生成明日计划建议"""
        if not recent_data:
            return "暂无足够数据生成个性化建议。"
        
        context = f"""
        基于用户最近的学习记录：
        {json.dumps(recent_data[-3:], ensure_ascii=False, indent=2)}
        
        请为明天的时间规划提供具体建议，包括：
        1. 最佳学习时段推荐
        2. 各学科的时间分配建议
        3. 需要特别注意的事项
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"建议服务暂时不可用: {str(e)}"

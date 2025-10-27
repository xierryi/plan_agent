import json
try:
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
except ImportError:
    # 兼容旧版本
    from langchain.schema import BaseMessage, HumanMessage, SystemMessage
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_load_dotenv():
    """安全加载环境变量，处理编码问题"""
    try:
        # 尝试直接读取.env文件并重新创建
        env_path = '.env'
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 重新用正确编码写入
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("已修复.env文件编码")
            except UnicodeDecodeError:
                # 如果还是编码错误，创建新的.env文件
                logger.warning("检测到编码问题，创建新的.env文件")
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write('OPENAI_API_KEY=your_api_key_here\n')
                    f.write('DEBUG=True\n')
        
        load_dotenv()
        logger.info("环境变量加载成功")
    except Exception as e:
        logger.warning(f"环境变量加载失败: {e}，使用默认配置")

# 安全加载环境变量
safe_load_dotenv()

class StudyAgent:
    def __init__(self):
        self.llm = OpenAI(
            temperature=0.3,
            model="gpt-3.5-turbo",
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        self.system_prompt = """你是一个专业的学习效率分析助手。请基于用户提供的学习数据，提供专业、具体、可操作的分析和建议。分析要基于数据事实，建议要具体可行。"""
    
    def analyze_weekly_trends(self, weekly_data):
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
        
        请用中文回复，结构清晰，突出重点。
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=context)
            ])
            return response.content
        except Exception as e:
            return f"分析服务暂时不可用: {str(e)}"
    
    def generate_tomorrow_plan(self, recent_data):
        """基于历史数据生成明日计划建议"""
        if not recent_data:
            return "暂无足够数据生成个性化建议。"
        
        context = f"""
        基于用户最近的学习记录：
        {json.dumps(recent_data[-3:], ensure_ascii=False, indent=2)}
        
        请为明天的时间规划提供具体建议，包括：
        1. 最佳学习时段推荐
        2. 各学科的时间分配建议
        3. 需要特别注意的事项
        
        请给出具体、可执行的建议。
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=context)
            ])
            return response.content
        except Exception as e:
            return "建议服务暂时不可用，请手动规划明日安排。"
        
#if __name__ == "__main__":
#    openai_api_key=os.getenv("OPENAI_API_KEY")
#   print(f"{openai_api_key}")
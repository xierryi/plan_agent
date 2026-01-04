# 📚 StudyAgent - 智能学习效率分析 AI Agent

> 一个基于 OpenAI Function Calling 的智能学习助手，帮助学生追踪学习计划、分析效率模式、获取个性化建议。

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://plan-agent.streamlit.app/)

---

## 📋 目录

- [项目背景](#-项目背景)
- [解决方案](#-解决方案)
- [系统架构](#-系统架构)
- [AI Agent 设计](#-ai-agent-设计)
- [功能展示](#-功能展示)
- [快速开始](#-快速开始)
- [技术实现](#-技术实现)
- [项目结构](#-项目结构)
- [未来展望](#-未来展望)

---

## 🎯 项目背景

### 问题描述

在科研学习生活中，学生常常面临以下挑战：

1. **计划难以执行** - 制定了学习计划却难以坚持，缺乏有效的追踪机制
2. **效率难以衡量** - 不清楚自己的学习效率如何，哪些学科需要加强
3. **缺乏数据支撑** - 凭感觉安排学习，没有基于历史数据的科学规划
4. **反馈不及时** - 无法及时发现学习中的问题并调整策略

### 项目目标

开发一个 **AI Agent** 应用，通过：
- 🤖 **智能对话** - 自然语言交互，随时询问学习情况
- 🔧 **工具调用** - AI 自主决策调用数据分析工具
- 📊 **数据驱动** - 基于历史数据提供个性化建议
- 🚀 **自动规划** - 一键生成并应用学习计划

---

## 💡 解决方案

### 核心理念

本项目采用 **AI Agent + 工具调用（Function Calling）** 架构，让 AI 能够：

```
用户提问 → AI 分析意图 → 自主选择工具 → 执行数据查询 → 生成个性化回复
```

### 功能模块

| 模块 | 功能 | 说明 |
|------|------|------|
| 🤖 **AI 助手** | 对话式交互 | 支持自然语言询问学习情况 |
| 🎯 **一键规划** | 智能生成计划 | AI 分析历史数据，自动填入任务表单 |
| 📝 **今日记录** | 任务管理 | 记录计划任务和实际执行情况 |
| 📊 **数据看板** | 可视化统计 | 效率趋势、学科分布等图表 |
| 🔍 **智能分析** | AI 深度分析 | 周度报告、改进建议 |
| 📚 **历史数据** | 记录查询 | 浏览和搜索历史学习记录 |
| ☁️ **云端同步** | GitHub 存储 | 数据自动同步到 GitHub 仓库 |

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面 (Streamlit)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ AI 助手  │  │ 今日记录 │  │ 数据看板 │  │ 智能分析 │  ...    │
│  └────┬─────┘  └──────────┘  └──────────┘  └──────────┘         │
│       │                                                          │
├───────┼──────────────────────────────────────────────────────────┤
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   StudyAgent (AI Agent)                  │    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │    │
│  │  │ OpenAI API  │───▶│  Function   │───▶│   Tools     │  │    │
│  │  │  (GPT-4o)   │    │  Calling    │    │  Execution  │  │    │
│  │  └─────────────┘    └─────────────┘    └──────┬──────┘  │    │
│  └───────────────────────────────────────────────┼──────────┘    │
│                                                  │               │
├──────────────────────────────────────────────────┼───────────────┤
│                                                  ▼               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    StudyTools (工具集)                   │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐  │    │
│  │  │get_weekly_stats│  │analyze_pattern│  │generate_plan│  │    │
│  │  ├───────────────┤  ├───────────────┤  ├─────────────┤  │    │
│  │  │query_history  │  │get_suggestions│  │compare_periods│ │    │
│  │  ├───────────────┤  └───────────────┘  └─────────────┘  │    │
│  │  │subject_analysis│                                      │    │
│  │  └───────────────┘                                       │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   数据层 (Data Layer)                    │    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │    │
│  │  │DataManager  │    │StateManager │    │GitHubManager│  │    │
│  │  │(本地存储)   │    │(状态管理)   │    │(云端同步)   │  │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 AI Agent 设计

### Agent 核心特征

本项目实现了一个具备以下特征的 AI Agent：

#### 1. 工具调用 (Function Calling)

AI 可以自主决定调用 7 个工具函数：

```python
tools = [
    "get_weekly_stats",       # 获取学习统计
    "get_subject_analysis",   # 学科分析
    "query_history",          # 查询历史
    "generate_smart_plan",    # 生成计划
    "analyze_learning_pattern", # 分析模式
    "get_improvement_suggestions", # 改进建议
    "compare_periods"         # 时段对比
]
```

#### 2. 自主决策流程

```
用户: "我上周数学学得怎么样？"
   │
   ▼
AI 分析: 用户想了解数学学科的学习情况
   │
   ▼
AI 决策: 调用 get_subject_analysis(subject="math")
   │
   ▼
工具执行: 分析最近30天数学学习数据
   │
   ▼
AI 回复: 基于数据生成个性化分析报告
```

#### 3. 工具定义示例

```python
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
                    "description": "学科名称",
                    "enum": ["math", "physics", "econ", "cs", "other"]
                }
            },
            "required": ["subject"]
        }
    }
}
```

### 对话示例

| 用户输入 | AI 调用的工具 | AI 回复要点 |
|---------|-------------|------------|
| "这周学了多少小时？" | `get_weekly_stats(days=7)` | 总时长、完成率、各学科分布 |
| "帮我规划明天的学习" | `generate_smart_plan(date="明天")` | 基于历史数据的个性化计划 |
| "我的学习效率怎么样？" | `analyze_learning_pattern(aspect="efficiency")` | 效率趋势、高峰时段、建议 |
| "这周和上周比怎么样？" | `compare_periods(7, 7)` | 时间变化、完成率对比 |

---

## 🖼 功能展示

### 1. AI 助手对话界面

用户可以用自然语言与 AI 对话，AI 会自动调用相应工具获取数据：

```
👤 用户: 帮我看看这周的学习统计

🤖 AI: 根据数据分析，您这周的学习情况如下：

📊 **本周学习统计**
- 总学习时间：12.5 小时
- 任务完成率：85%
- 平均每日学习：1.8 小时

📈 **学科分布**
- 数学：4.5 小时 (36%)
- 物理：3.0 小时 (24%)
- 计算机：3.0 小时 (24%)
- 经济学：2.0 小时 (16%)

💡 **建议**
1. 数学学习时间充足，继续保持
2. 建议适当增加经济学的学习时间
3. 您的学习效率在下午较高，建议把难度大的任务安排在下午
```

### 2. 一键生成计划

AI 分析历史数据，智能生成学习计划并自动填入表单：

```
🎯 一键生成今日计划
┌──────────────┬──────────┬──────────┬──────────────┐
│ 计划时长: 4h │ 重点: 数学│ 日期: 今天│ [🚀 生成并应用] │
└──────────────┴──────────┴──────────┴──────────────┘

✅ 已生成 4 个任务，总计 4 小时！

📋 计划预览：
- 数学: 09:00 - 10:30 (90分钟)
- 物理: 11:00 - 12:00 (60分钟)
- 计算机: 14:00 - 15:00 (60分钟)
- 经济学: 15:30 - 16:00 (30分钟)
```

### 3. 数据可视化看板

- 📈 效率趋势图
- 📊 学科时间分布
- 📉 完成率变化
- 🎯 关键指标卡片

### 4. 历史记录管理

- 按日期浏览历史学习记录
- 查看任务详情和执行情况
- 阅读学习反思和总结

---

## 🚀 快速开始

### 在线体验

直接访问部署在 Streamlit Cloud 的应用：

👉 **[https://plan-agent.streamlit.app/](https://plan-agent.streamlit.app/)**

### 本地运行

#### 1. 克隆项目

```bash
git clone https://github.com/xierryi/plan_agent.git
cd plan_agent/study_dashboard
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

创建 `.env` 文件：

```env
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，默认官方地址
MODEL_NAME=gpt-4o-mini  # 可选，默认 gpt-4o-mini

# GitHub 数据同步配置（可选）
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_username
GITHUB_REPO=your_repo_name
```

#### 4. 运行应用

```bash
streamlit run app.py
```

#### 5. 访问应用

打开浏览器访问 `http://localhost:8501`

---

## 🔧 技术实现

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | Streamlit | Python Web 框架，快速构建数据应用 |
| **AI** | OpenAI GPT-4o-mini | 大语言模型，支持 Function Calling |
| **可视化** | Plotly | 交互式图表库 |
| **数据处理** | Pandas, NumPy | 数据分析和处理 |
| **存储** | JSON/JSONL + GitHub | 本地文件 + 云端同步 |
| **部署** | Streamlit Cloud | 免费托管服务 |

### 核心代码示例

#### AI Agent 工具调用

```python
class StudyAgent:
    def chat(self, user_message: str) -> str:
        # 第一次调用：让 AI 决定是否需要调用工具
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=self.tools.get_tool_definitions(),
            tool_choice="auto"
        )
        
        # 如果 AI 决定调用工具
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                # 执行工具
                result = self.tools.execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
            
            # 第二次调用：基于工具结果生成回复
            final_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages + tool_results
            )
```

#### 工具执行器

```python
class StudyTools:
    def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
        tool_map = {
            'get_weekly_stats': self.get_weekly_stats,
            'get_subject_analysis': self.get_subject_analysis,
            'generate_smart_plan': self.generate_smart_plan,
            # ...
        }
        return tool_map[tool_name](**arguments)
```

### 依赖配置

`requirements.txt`:

```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.15.0
openai>=1.0.0
python-dotenv>=1.0.0
numpy>=1.21.0
PyGithub>=1.55.0
pytz>=2023.3
```

---

## 📁 项目结构

```
plan_agent/
├── study_dashboard/
│   ├── app.py                 # 主应用入口
│   ├── study_agent.py         # AI Agent 实现
│   ├── tools.py               # 工具函数定义
│   ├── data_manager.py        # 本地数据管理
│   ├── github_manager.py      # GitHub 数据同步
│   ├── github_state_manager.py # 状态管理
│   ├── state_manager.py       # Session 状态管理
│   ├── requirements.txt       # Python 依赖
│   └── .env                   # 环境变量配置（不提交）
├── README.md                  # 项目说明文档
└── .gitignore
```

### 核心文件说明

| 文件 | 说明 |
|------|------|
| `app.py` | Streamlit 应用主入口，包含所有页面逻辑 |
| `study_agent.py` | AI Agent 实现，支持 Function Calling |
| `tools.py` | 7 个工具函数的定义和实现 |
| `data_manager.py` | 本地 JSONL 数据存储 |
| `github_manager.py` | GitHub API 封装，云端数据同步 |
| `github_state_manager.py` | 基于 GitHub 的状态持久化 |

---

## 🔮 未来展望

### 功能扩展

- [ ] 添加番茄钟计时功能
- [ ] 支持多用户协作学习
- [ ] 接入更多 AI 模型（Claude、Gemini）
- [ ] 添加学习资源推荐功能
- [ ] 支持导出学习报告 PDF

### 技术优化

- [ ] 添加 RAG 检索增强，提升 AI 回答准确性
- [ ] 实现 Agent 记忆系统，支持长期学习偏好记忆
- [ ] 添加多 Agent 协作（规划 Agent + 分析 Agent）
- [ ] 优化移动端响应式布局

---

## 👨‍💻 作者

- GitHub: [@xierryi](https://github.com/xierryi)

## 📄 许可证

MIT License

---

## 🙏 致谢

- [OpenAI](https://openai.com/) - GPT 模型和 Function Calling API
- [Streamlit](https://streamlit.io/) - 优秀的 Python Web 框架
- [Plotly](https://plotly.com/) - 交互式可视化库

# 📚 StudyAgent Vue 版本

> 基于 Vue 3 + FastAPI 的智能学习效率分析系统

## 🏗️ 技术栈

### 前端 (frontend/)
- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **Vue Router** - 官方路由管理
- **Pinia** - 新一代状态管理
- **TailwindCSS** - 原子化 CSS 框架
- **Chart.js** - 数据可视化
- **Axios** - HTTP 客户端

### 后端 (backend/)
- **FastAPI** - 高性能 Python Web 框架
- **OpenAI API** - AI 对话和工具调用
- **Pydantic** - 数据验证

## 📁 项目结构

```
study_dashboard_vue/
├── frontend/                 # Vue 前端
│   ├── src/
│   │   ├── api/             # API 接口封装
│   │   ├── components/      # 公共组件
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── views/           # 页面组件
│   │   ├── App.vue          # 根组件
│   │   ├── main.js          # 入口文件
│   │   └── style.css        # 全局样式
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── backend/                  # FastAPI 后端
│   ├── main.py              # API 服务入口
│   ├── requirements.txt     # Python 依赖
│   └── env.example.txt      # 环境变量示例
│
└── README.md
```

## 🚀 快速开始

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\Activate
# Mac/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制 env.example.txt 为 .env 并填入配置）
# 必须配置 OPENAI_API_KEY

# 启动服务
python main.py
# 或
uvicorn main:app --reload --port 8000
```

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量（可选，复制 env.example.txt 为 .env）

# 启动开发服务器
npm run dev
```

### 3. 访问应用

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## ✨ 功能特性

### 📊 数据看板
- 学习效率趋势图
- 学科时间分布
- 核心指标展示

### 📝 今日记录
- 计划任务管理
- 实际执行追踪
- 学习反思记录

### 🤖 AI 助手
- 智能对话分析
- 一键生成计划
- 个性化建议

### 📚 历史数据
- 日期筛选查看
- 详情记录展示

### ⚙️ 设置
- GitHub 同步配置
- 数据管理

## 🔧 环境变量

### 后端 (.env)

| 变量名 | 说明 | 必填 |
|--------|------|------|
| OPENAI_API_KEY | OpenAI API 密钥 | ✅ |
| OPENAI_BASE_URL | API 端点（可选） | ❌ |
| MODEL_NAME | 模型名称 | ❌ |
| GITHUB_TOKEN | GitHub Token | ❌ |
| GITHUB_OWNER | GitHub 用户名 | ❌ |
| GITHUB_REPO | 数据仓库名 | ❌ |

### 前端 (.env)

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| VITE_API_URL | 后端 API 地址 | http://localhost:8000/api |

## 📝 开发说明

### 前端开发

```bash
npm run dev      # 开发服务器
npm run build    # 生产构建
npm run preview  # 预览构建结果
```

### 后端开发

```bash
uvicorn main:app --reload  # 热重载开发
```

## 🔄 与 Streamlit 版本对比

| 特性 | Streamlit 版本 | Vue 版本 |
|------|---------------|----------|
| 前端技术 | Python (Streamlit) | Vue 3 + TailwindCSS |
| 后端技术 | 同一进程 | FastAPI (独立服务) |
| 性能 | 一般 | 更好 |
| 自定义 UI | 受限 | 完全自定义 |
| 部署 | 简单 | 需要分别部署 |
| 适合场景 | 快速原型 | 生产应用 |

## 📄 许可证

MIT License

---

Made with ❤️ for better learning

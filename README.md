# OPSIGHT

一个包含后端 FastAPI 与前端 Vue3 + Vite 的全栈应用，支持任务与用户管理、AI 代理/函数配置、AI 浮动球聊天助手，以及系统与 AI 设置。

## 关键特性

- 后端：FastAPI + SQLAlchemy + Pydantic（简易 SQLite 数据库）。
- 前端：Vue3 + Pinia + Element Plus + Vite（支持 Mock/Proxy 两种 API 模式）。
- 身份与权限：支持普通用户、管理员、超级管理员（`super_admin`）等角色与权限判断。
- AI 管理：AI 代理与函数的增删改查、调用日志与统计。
- AI 浮动球：登录后显示，支持系统知识（欢迎+推荐问题）与简单聊天。
- 设置管理：系统设置与 AI 设置的读取与更新接口。

## 快速开始

### 环境要求

- Windows 环境（开发）
- Python 3.10+（建议）
- Node.js 18+ 与 npm

### 后端启动

1. 安装依赖并启动服务：

```
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

2. 后端运行在：`http://127.0.0.1:8000`。

### 前端启动

1. 安装依赖并启动开发服务器：

```
cd frontend
npm install
npm run dev -- --port=3001
```

2. 前端运行在：`http://localhost:3001/`。

### 前端 API 模式切换

- Vite 提供 Mock 与 Proxy 两种模式（参见 `frontend/vite.config.js`）。
- 推荐在本地联调使用 Proxy（真实后端），`.env.local` 设置示例：

```
VITE_USE_MOCK=false
VITE_API_BASE_URL=/api/v1
```

- 当 `VITE_USE_MOCK=false` 时，`/api/v1` 会代理到 `http://127.0.0.1:8000`（无需显式配置后端地址）。
- 如果需要直连后端而不走代理，可设置：`VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`。

## 登录与权限

- 登录页面位于前端，登录成功后会在 `localStorage` 保存用户信息与简单令牌。
- 已登录后会显示 AI 浮动球（`App.vue` 中基于 `authStore.isAuthenticated` 控制显示）。
- 访问 `/admin/ai` 需要 `super_admin` 权限（参见 `frontend/src/router/index.js`）。

## 与浮动球相关的后端接口

为匹配前端 `src/utils/ai.js` 的调用，后端新增并已启用以下接口：

- `GET /api/v1/ai/system-knowledge`
  - 响应：`{ welcome: string, recommended: string[] }`
  - 根据用户 `identity_type`（`get_ai_knowledge_branch`）返回欢迎语与推荐问题。

- `POST /api/v1/ai/chat`
  - 请求：`{ question: string, context?: object }`
  - 响应：`{ answer: string }`
  - 当前为关键词规则的示例回答，后续可接入真实大模型。

前端浮动球组件：`frontend/src/components/AIFloatingBall.vue`，工具函数：`frontend/src/utils/ai.js`。

## 其他后端接口概览

- AI 管理
  - 代理：`/api/v1/ai/agents`（CRUD）
  - 函数：`/api/v1/ai/functions`（CRUD）
  - 调用：`/api/v1/ai/call`（模拟调用）
  - 日志：`/api/v1/ai/logs`（分页与查询）
  - 统计：`/api/v1/ai/stats`
- 设置管理
  - AI 设置：`/api/v1/settings/ai`（GET/PUT）
  - 系统设置：`/api/v1/settings/system`（GET/PUT）
- 身份/权限相关逻辑：`backend/app/models.py` 中的权限判断与 `get_ai_knowledge_branch`。

## 目录结构（节选）

```
e:\51\AI\KillerApp\
├── backend\
│   ├── app\
│   │   ├── main.py        # FastAPI 入口
│   │   ├── models.py      # SQLAlchemy 模型与权限逻辑
│   │   ├── schemas.py     # Pydantic 模型（含 AI 浮动球相关）
│   │   └── auth.py        # 简易认证
│   ├── requirements.txt
│   └── tests\
│       └── test_auth_api.py
├── frontend\
│   ├── src\
│   │   ├── App.vue
│   │   ├── components\
│   │   │   └── AIFloatingBall.vue
│   │   ├── stores\
│   │   │   └── auth.js
│   │   ├── utils\
│   │   │   └── ai.js
│   │   └── views\
│   │       └── AdminAI.vue
│   └── vite.config.js
└── docs\
    └── 浮动球.md
```

## 验证与调试

### 后端接口快速验证（PowerShell）

```
# 系统知识
Invoke-WebRequest -Uri http://127.0.0.1:8000/api/v1/ai/system-knowledge

# 简易聊天
Invoke-RestMethod -Method Post \
  -Uri http://127.0.0.1:8000/api/v1/ai/chat \
  -Body (@{question='如何查看任务进度？'} | ConvertTo-Json) \
  -ContentType 'application/json'
```

### 后端测试

```
cd backend
pytest -q
```

## 常见问题

- 前端接口 404：检查 `.env.local` 的 `VITE_USE_MOCK` 是否为 `false`，确保代理到后端；或确认 `VITE_API_BASE_URL` 指向后端。
- 重复前端开发服务器：保留一个端口（如 `3001`），关闭其它 `npm run dev` 实例，避免端口与状态混乱。
- 登录后看不到浮动球：确认已登录（`localStorage` 中应存在用户信息），以及 `App.vue` 中条件渲染是否满足。

## 后续规划

- 接入真实大模型（如 OpenAI/Claude 等），替换当前关键词规则聊天。
- 丰富系统知识内容，按不同身份类型提供更细分的引导与问答。
- 增强 AI 调用链路与日志分析能力，支持更多统计维度。

---

如需进一步协助联调或完善文档，请在 Issue 中说明你的场景与需求。
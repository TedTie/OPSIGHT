### **结构化输出：AdminAI 页面重构方案**

#### **1. 项目/功能概述 (Overview)**

我们的目标是将 `AdminAI.vue` 页面重构为一个直观、统一的 **AI 控制中心**。管理员应能在此处清晰地完成两件事：1) 创建和管理提供智能的 **“智能体” (Agents)**；2) 将这些智能体分配给系统中各个需要 AI 的 **“功能点” (Features)**。

#### **2. 核心功能点 (Core Features)**

重构后的页面将提供以下核心功能：

* **智能体管理：**
 * 管理员可以创建、查看、编辑和删除智能体 (Agent)。
 * 每个智能体包含名称、描述、模型提供商 (如 OpenAI)、模型名称、以及最重要的 **系统提示词 (System Prompt)**。
* **功能点配置：**
 * 系统会 **自动展示** 所有在代码中注册的 AI 功能点（例如：“日报反思生成”、“数据洞察分析”等），管理员无需手动添加。
 * 管理员可以为每个功能点通过下拉菜单选择一个已创建的、活跃的智能体。
 * 可以随时更换或取消某个功能点关联的智能体。
* **调用日志监控：**
 * 在一个集中的地方查看所有 AI 功能点的调用记录，包括成功、失败、调用者、输入/输出等信息，便于排错和审计。
* **统计概览：**
 * 在页面顶部提供关键指标的概览，如智能体总数、今日调用次数、成功率等。

#### **3. 技术规格 (Technical Specifications)**

我们将彻底简化原有的概念，只保留 **“智能体 (Agent)”** 和 **“功能点 (Feature)”** 这两个核心实体。

##### **前端 (Frontend)**

* **页面/组件 (Pages/Components):**
 * **`AdminAI.vue` (主页面):**
 * 保留统计概览部分。
 * 将 `el-tabs` 的标签页修改为以下三个，使其职责清晰：
 1. **智能体管理 (Agent Management):** 用于管理 `AIAgents`。
 2. **功能点配置 (Feature Configuration):** 用于将 `Agents` 分配给 `Features`。
 3. **调用日志 (Call Logs):** 用于查看所有日志。
 * **建议拆分的组件:**
 * `AgentList.vue`: 专门负责展示和操作智能体列表。
 * `FeatureConfigList.vue`: 专门负责展示功能点列表及分配智能体。
 * `LogViewer.vue`: 专门负责展示和筛选日志。

* **用户流程 (User Flow):**
 1. **创建智能体：** 管理员进入“智能体管理”标签页，点击“新增智能体”，填写表单（特别是系统提示词），保存。
 2. **分配智能体：** 管理员切换到“功能点配置”标签页。页面会从后端加载一个列表，显示所有系统内置的AI功能点（如“日报情感分析”）。
 3. 管理员找到想要配置的功能点，从该行对应的下拉菜单中，选择第一步创建的智能体。选择后，系统自动保存。
 4. **监控：** 管理员可以随时切换到“调用日志”标签页，查看所有AI调用的情况。

* **数据交互 (Data Interaction):**
 * **智能体管理页:**
 * `GET /api/ai/agents`: 获取所有智能体列表。
 * `POST /api/ai/agents`: 创建新的智能体。
 * `PUT /api/ai/agents/{id}`: 更新指定智能体。
 * **功能点配置页:**
 * `GET /api/ai/features`: **[核心改动]** 获取所有在后端注册的、可配置的AI功能点列表。
 * `GET /api/ai/agents?active=true`: 获取所有“已启用”的智能体，用于填充下拉菜单。
 * `POST /api/ai/features/{feature_key}/assign`: 将一个智能体分配给一个功能点。
 * **调用日志页:**
 * `GET /api/ai/logs`: 获取分页的日志数据，支持按功能点、状态等条件筛选。

##### **后端 (Backend)**

* **API 接口 (API Endpoints):**

| 方法 | URL 路径 | 描述 | 请求体 (Payload) 示例 | 响应体 (Response) 示例 |
| :----- | :------------------------------------- | :--------------------------------------- | :------------------------------------------------- | :----------------------------------------------- |
| `GET` | `/api/ai/features` | 获取所有已注册的系统功能点 | (无) | `[{ "key": "report_analysis", "name": "日报分析", "description": "...", "assigned_agent_id": "uuid-123" }]` |
| `POST` | `/api/ai/features/{feature_key}/assign`| 为功能点分配一个智能体 | `{ "agent_id": "uuid-xyz" }` | `{ "success": true }` |
| `GET` | `/api/ai/agents` | 获取智能体列表 | (无) | `[{ "id": "uuid-123", "name": "分析师A", ... }]` |
| `POST` | `/api/ai/agents` | 创建智能体 | (Agent 表单数据) | (新创建的 Agent 对象) |
| `PUT` | `/api/ai/agents/{id}` | 更新智能体 | (Agent 表单数据) | (更新后的 Agent 对象) |
| `DELETE`| `/api/ai/agents/{id}` | 删除智能体 | (无) | `{ "success": true }` |
| `GET` | `/api/ai/logs` | 获取调用日志 (支持分页和过滤) | (无，参数在 URL query 中) | `{ "items": [...], "total": 100 }` |

* **数据模型 (Data Models):**

 1. **`AIAgents` (智能体表):**
 * `id` (主键, UUID)
 * `name` (字符串, 名称)
 * `description` (文本, 描述)
 * `provider` (字符串, 'openai', 'claude', ...)
 * `model_name` (字符串)
 * `system_prompt` (大文本, **核心**)
 * `temperature`, `max_tokens` (数值)
 * `is_active` (布尔)
 * `created_at`, `updated_at`

 2. **`AIFeatures` (AI功能点表):** **(这是新的核心模型)**
 * `key` (主键, 字符串, 如 `report_analysis`): 这是代码中唯一标识符。
 * `name` (字符串, 如 `日报分析`): 显示给用户看的名称。
 * `description` (文本, 功能描述)
 * `assigned_agent_id` (外键, 指向 `AIAgents.id`, 可为空)

 > **关键设计：** 这张表的数据来源是“半固定”的。后端代码中应有一个地方（比如一个配置文件或一个专门的注册类）来定义所有的功能点。服务启动时，会自动检查这些定义并同步到 `AIFeatures` 表中，确保数据库与代码中的功能点保持一致。这样你未来新增功能点时，只需在后端代码加一行注册即可，前端页面会自动显示。

 3. **`AILogs` (调用日志表):**
 * `id` (主键, UUID)
 * `feature_key` (外键, 指向 `AIFeatures.key`): 记录是哪个功能点的调用。
 * `user_id` (调用者ID)
 * `status` ('success', 'failed')
 * `input_text`, `output_text`, `error_message` (大文本)
 * `tokens_used` (整数)
 * ...

#### **4. 技术栈建议 (Tech Stack Suggestion)**

* **前端:** **Vue.js 3** + **Element Plus** (你已经在使用，保持即可)
* **后端:** **Python FastAPI** 或 **Flask**。FastAPI 对于创建这种结构清晰的 API 尤其高效和简单，并且自带交互式 API 文档，对初学者非常友好。

#### **5. 开发步骤建议 (Development Steps)**

我建议你分两步走：先改造后端，再重构前端。

* **第一阶段：后端改造**
 1. **数据库迁移：** 创建新的 `AIFeatures` 表。确保 `AILogs` 有 `feature_key` 字段。
 2. **实现功能点注册机制：** 在 Python 后端创建一个列表或字典来定义所有的 AI 功能点（`key`, `name`, `description`）。编写一个服务启动时运行的函数，将这些定义同步到 `AIFeatures` 数据库表中。
 3. **开发新 API：**
 * 实现 `GET /api/ai/features` 接口，直接从 `AIFeatures` 表查询并返回列表。
 * 实现 `POST /api/ai/features/{feature_key}/assign` 接口，用于更新 `AIFeatures` 表中的 `assigned_agent_id`。
 4. **调整旧 API：** 确保 `/api/ai/agents` 和 `/api/ai/logs` 接口符合新模型的设计。

* **第二阶段：前端重构 (`AdminAI.vue`)**
 1. **清理和布局：** 备份旧文件。在 `AdminAI.vue` 中，将 `el-tabs` 的内容简化为三个清晰的标签页：“智能体管理”、“功能点配置”、“调用日志”。
 2. **实现“智能体管理”：** 创建或修改 `AgentList` 组件。让它能通过 API 获取、创建、编辑智能体。这部分改动应该不大。
 3. **实现“功能点配置” (核心)：** 创建 `FeatureConfigList.vue` 组件。
 * 在该组件加载时，同时调用 `GET /api/ai/features` 和 `GET /api/ai/agents?active=true`。
 * 使用 `el-table` 渲染功能点列表。
 * 在表格的某一列中，使用 `el-select` (下拉菜单) 来显示启用的智能体列表。`v-model` 绑定到该行功能点的 `assigned_agent_id`。
 * 监听 `el-select` 的 `@change` 事件，当用户选择新的智能体时，调用 `POST /api/ai/features/{feature_key}/assign` 接口保存更改。
 4. **实现“调用日志”：** 根据新的数据模型调整日志展示和筛选逻辑。
 5. **完成与测试：** 整体测试用户流程，确保从创建智能体到分配再到查看日志的流程顺畅无误。

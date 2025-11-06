# 指令：对 OPSIGHT 权限系统进行端到端全面自查

你好，Trae。当前应用在登录后，所有身份都无法正常展示列表，疑似权限系统出现全局性问题。为了高效定位问题，请你对整个权限控制链路进行一次端到端的全面代码审查。

## 1. 审查目标 (Audit Goal)

验证从用户登录、获取权限、到前端根据权限展示/隐藏界面元素的完整流程是否正确。找出其中的逻辑断点或实现缺陷。

## 2. 核心代码清单 (Core Code Checklist)

以下是构成权限系统的所有核心文件，请逐一审查。

### 后端 (Backend - FastAPI)

**文件 1: `backend/app/api/deps.py` (权限依赖项)**
*这里是后端判断用户身份和权限的核心逻辑。*
```python
# [请在这里粘贴 deps.py 的完整代码]
```

**文件 2: `backend/app/api/v1/endpoints/login.py` (登录接口)**
*这里是“签发”用户身份和权限的源头。*
```python
# [请在这里粘贴 login.py 的完整代码]
```

**文件 3: `backend/app/models/user.py` (用户数据模型)**
*我们需要知道 User 模型中是如何定义 `role` 或 `permissions` 字段的。*
```python
# [请在这里粘贴 user.py 的完整代码]
```

**文件 4: `backend/app/api/v1/endpoints/users.py` (一个被保护的接口示例)**
*以获取用户列表接口为例，看它是如何使用 `deps.py` 来保护自己的。*
```python
# [请在这里粘贴 users.py 的完整代码]
```

### 前端 (Frontend - Vue)

**文件 5: `frontend/src/stores/auth.js` (Pinia 状态管理)**
*这里是前端“存储和管理”用户身份权限的中央仓库。*
```javascript
# [请在这里粘贴 auth.js 的完整代码]
```

**文件 6: `frontend/src/directives/can.js` (v-can 自定义指令)**
*这里是前端“使用”权限来控制UI显隐的具体实现。*
```javascript
# [请在这里粘贴 can.js 的完整代码]
```

**文件 7: `frontend/src/views/Tasks.vue` (使用 v-can 的页面)**
*以任务页面为例，看它是如何在模板中使用 `v-can` 指令的。*
```vue
# [请在这里粘贴 Tasks.vue 的完整代码，特别是 <template> 部分]
```

## 3. 预期行为描述 (Expected Behavior)

| 用户角色 | 预期前端行为 | 预期 API 访问权限 |
| :--- | :--- | :--- |
| **管理员 (admin)** | 能看到“用户管理”菜单。在任务列表页，能看到“创建”、“编辑”、“删除”所有按钮。 | 可以成功请求 `GET /api/v1/users` 和 `GET /api/v1/tasks`。 |
| **普通用户 (user)** | 看不到“用户管理”菜单。在任务列表页，只能看到列表，看不到“创建”、“编辑”、“删除”按钮。 | 请求 `GET /api/v1/users` 会被拒绝 (403 Forbidden)，但可以成功请求 `GET /api/v1/tasks`。 |

---

请 Trae 基于以上信息，进行代码审查，并以“权限认证之旅”的视角（从后端签发Token->前端存储->前端使用），指出权限控制链路中可能存在的断点或逻辑缺陷。
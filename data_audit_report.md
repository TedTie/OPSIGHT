# OPSIGHT 系统数据可见性端到端审计报告

**审计时间**: 2025-11-03 21:30:29  
**审计人员**: Trae AI Assistant  
**系统版本**: OPSIGHT v1.0  
**审计范围**: 任务列表、用户列表、日报列表、用户信息 API 端点  

---

## 1. 审计摘要 (Executive Summary)

**根本原因**: 任务过滤逻辑存在严重缺陷，仅基于 `assigned_to` 字段进行过滤，完全忽略了 `assignment_type` 字段的语义，导致分配类型为 `all`、`group`、`identity` 的任务对普通用户不可见。

**影响范围**: 所有非管理员用户无法看到应该对他们可见的任务，严重影响系统的核心功能。

---

## 2. 模拟用户测试结果 (Simulated User Test Results)

### 测试用户：`admin` (super_admin)

| API 端点 | 状态 | 结果 | 分析 |
|---------|------|------|------|
| `GET /api/v1/auth/me` | ✅ 成功 | 返回完整用户信息，角色为 `super_admin` | 正常 |
| `GET /api/v1/tasks` | ✅ 成功 | 返回 10 条任务记录 | 管理员可以看到所有任务 |
| `GET /api/v1/users` | ✅ 成功 | 返回 3 条用户记录 | 管理员权限正常 |
| `GET /api/v1/reports` | ✅ 成功 | 返回 1 条日报记录 | 正常 |

**用户信息详情**:
```json
{
  "id": 1,
  "username": "admin",
  "role": "super_admin",
  "identity_type": "sa",
  "group_id": 2,
  "group_name": "MYC-LP01Team",
  "is_admin": true,
  "is_super_admin": true
}
```

**任务分配类型分布**: `{'all': 4, 'user': 4, 'group': 2}`

### 测试用户：`jlpss-chenjianxiong` (admin)

| API 端点 | 状态 | 结果 | 分析 |
|---------|------|------|------|
| `GET /api/v1/auth/me` | ✅ 成功 | 返回完整用户信息，角色为 `admin` | 正常 |
| `GET /api/v1/tasks` | ✅ 成功 | 返回 10 条任务记录 | 管理员可以看到所有任务 |
| `GET /api/v1/users` | ✅ 成功 | 返回 3 条用户记录 | 管理员权限正常 |
| `GET /api/v1/reports` | ✅ 成功 | 返回 1 条日报记录 | 正常 |

**用户信息详情**:
```json
{
  "id": 2,
  "username": "jlpss-chenjianxiong",
  "role": "admin",
  "identity_type": "ss",
  "group_id": 1,
  "group_name": "MYC-SS01Team",
  "is_admin": true,
  "is_super_admin": false
}
```

### 测试用户：`test_user` (user)

| API 端点 | 状态 | 结果 | 分析 |
|---------|------|------|------|
| `GET /api/v1/auth/me` | ✅ 成功 | 返回完整用户信息，角色为 `user` | 正常 |
| `GET /api/v1/tasks` | ⚠️ 成功但异常 | 返回 **0 条任务记录** (预期应有 6 条) | **关键问题** |
| `GET /api/v1/users` | ✅ 预期行为 | 403 Forbidden | 权限控制正常 |
| `GET /api/v1/reports` | ✅ 成功 | 返回 0 条日报记录 | 正常（该用户确实没有日报） |

**用户信息详情**:
```json
{
  "id": 3,
  "username": "test_user",
  "role": "user",
  "identity_type": "ss",
  "group_id": 1,
  "group_name": "MYC-SS01Team",
  "is_admin": false,
  "is_super_admin": false
}
```

**关键问题**: `test_user` 应该能看到以下任务：
- 4 个 `assignment_type: "all"` 的任务（分配给所有人）
- 2 个 `assignment_type: "group"` 且 `target_group_id: 1` 的任务（分配给 MYC-SS01Team 组）
- 总计应该看到 **6 条任务**，但实际返回 **0 条**

---

## 3. 根因分析 (Root Cause Analysis)

### 3.1 核心问题定位

**问题文件**: `backend/app/main.py` 第 564 行  
**问题函数**: `get_tasks()` API 端点  

**错误代码**:
```python
# 非管理员只能看到分配给自己的任务
if not current_user.is_admin:
    query = query.filter(Task.assigned_to == current_user.id)
```

### 3.2 问题分析

1. **逻辑缺陷**: 当前代码仅检查 `Task.assigned_to == current_user.id`，这只适用于 `assignment_type = "user"` 的情况。

2. **忽略的场景**:
   - `assignment_type = "all"`: 分配给所有人的任务
   - `assignment_type = "group"`: 分配给特定用户组的任务  
   - `assignment_type = "identity"`: 分配给特定身份类型的任务

3. **数据库设计问题**: 
   - `assigned_to` 字段在 `assignment_type != "user"` 时可能为 `NULL`
   - 缺乏统一的任务可见性判断逻辑

### 3.3 模型层问题

**问题文件**: `backend/app/models.py` 第 267-290 行  
**问题函数**: `Task.is_assigned_to_user()`  

**临时解决方案的问题**:
```python
elif self.assignment_type == TaskAssignmentType.GROUP:
    # 需要查询用户信息来检查组ID
    return True  # 临时解决方案 - 这是错误的！

elif self.assignment_type == TaskAssignmentType.IDENTITY:
    # 需要查询用户信息来检查身份类型  
    return True  # 临时解决方案 - 这是错误的！
```

这些临时解决方案导致权限检查失效。

---

## 4. 修复建议 (Remediation Plan)

### 4.1 立即修复 - 任务过滤逻辑

**修改文件**: `backend/app/main.py`  
**修改位置**: 第 551-590 行的 `get_tasks()` 函数

**修复代码**:
```python
@app.get("/api/v1/tasks", response_model=List[TaskResponse])
async def get_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    assigned_to: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取任务列表"""
    query = db.query(Task)
    
    # 非管理员需要根据任务分配类型进行过滤
    if not current_user.is_admin:
        # 构建复合过滤条件
        task_filters = []
        
        # 1. 直接分配给用户的任务
        task_filters.append(
            and_(
                Task.assignment_type == TaskAssignmentType.USER,
                Task.assigned_to == current_user.id
            )
        )
        
        # 2. 分配给所有人的任务
        task_filters.append(Task.assignment_type == TaskAssignmentType.ALL)
        
        # 3. 分配给用户所在组的任务
        if current_user.group_id:
            task_filters.append(
                and_(
                    Task.assignment_type == TaskAssignmentType.GROUP,
                    Task.target_group_id == current_user.group_id
                )
            )
        
        # 4. 分配给用户身份类型的任务
        if current_user.identity_type:
            task_filters.append(
                and_(
                    Task.assignment_type == TaskAssignmentType.IDENTITY,
                    Task.target_identity == current_user.identity_type
                )
            )
        
        # 应用 OR 条件
        query = query.filter(or_(*task_filters))
    
    # 应用其他过滤条件
    if status:
        query = query.filter(Task.status == status)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    
    # 分页
    offset = (page - 1) * size
    tasks = query.offset(offset).limit(size).all()
    
    return [TaskResponse(...) for task in tasks]
```

**需要添加的导入**:
```python
from sqlalchemy import and_, or_
from app.models import TaskAssignmentType
```

### 4.2 修复模型层逻辑

**修改文件**: `backend/app/models.py`  
**修改位置**: 第 267-290 行的 `is_assigned_to_user()` 方法

**修复代码**:
```python
def is_assigned_to_user(self, user: User, db: Session = None) -> bool:
    """检查任务是否分配给指定用户"""
    if self.assignment_type == TaskAssignmentType.USER:
        return self.assigned_to == user.id
    elif self.assignment_type == TaskAssignmentType.ALL:
        return True
    elif self.assignment_type == TaskAssignmentType.GROUP:
        # 检查用户是否属于目标组
        return self.target_group_id == user.group_id if self.target_group_id else False
    elif self.assignment_type == TaskAssignmentType.IDENTITY:
        # 检查用户是否具有目标身份
        return self.target_identity == user.identity_type if self.target_identity else False
    return False
```

### 4.3 修复单个任务权限检查

**修改文件**: `backend/app/main.py`  
**修改位置**: 第 595-628 行的 `get_task()` 函数

**修复代码**:
```python
@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 检查权限 - 使用修复后的逻辑
    if not current_user.is_admin and not task.is_assigned_to_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    return TaskResponse(...)
```

### 4.4 数据库迁移建议

**建议添加数据库约束**:
```sql
-- 确保分配类型和相关字段的一致性
ALTER TABLE tasks ADD CONSTRAINT check_assignment_consistency 
CHECK (
    (assignment_type = 'user' AND assigned_to IS NOT NULL) OR
    (assignment_type = 'group' AND target_group_id IS NOT NULL) OR
    (assignment_type = 'identity' AND target_identity IS NOT NULL) OR
    (assignment_type = 'all')
);
```

### 4.5 测试验证

修复后，`test_user` 应该能看到：
- 4 个 `assignment_type: "all"` 的任务
- 2 个 `assignment_type: "group"` 且 `target_group_id: 1` 的任务
- 总计 **6 条任务记录**

---

## 5. 优先级和实施计划

### 🔴 P0 - 立即修复 (关键)
1. **修复任务列表过滤逻辑** - 影响所有普通用户
2. **修复单个任务权限检查** - 防止权限绕过

### 🟡 P1 - 短期修复 (重要)  
3. **修复模型层 `is_assigned_to_user()` 方法** - 提高代码复用性
4. **添加数据库约束** - 防止数据不一致

### 🟢 P2 - 长期优化 (建议)
5. **添加单元测试** - 覆盖各种任务分配场景
6. **添加集成测试** - 验证端到端功能
7. **性能优化** - 优化复杂查询的执行计划

---

## 6. 风险评估

### 修复风险
- **低风险**: 修复逻辑清晰，不会影响现有管理员功能
- **向后兼容**: 不会破坏现有 API 接口
- **数据安全**: 修复后权限控制更加严格

### 不修复的风险
- **功能缺失**: 普通用户无法使用核心任务功能
- **用户体验**: 严重影响系统可用性
- **业务影响**: 可能导致任务分配和跟踪失效

---

## 7. 验证清单

修复完成后，请验证以下场景：

- [ ] `test_user` 可以看到 `assignment_type: "all"` 的任务
- [ ] `test_user` 可以看到分配给其所在组的任务  
- [ ] `test_user` 可以看到分配给其身份类型的任务
- [ ] `test_user` 不能看到分配给其他用户的任务
- [ ] `test_user` 不能看到分配给其他组的任务
- [ ] 管理员仍然可以看到所有任务
- [ ] 单个任务的权限检查正常工作

---

**报告生成时间**: 2025-11-03 21:30:29  
**建议复查时间**: 修复完成后 24 小时内
# 指令：OPSIGHT 系统级可见性逻辑重构与修复 (P0-Critical)

**参考文档**: `data_audit_report.md`
**核心问题**: 审计报告揭示了一个系统性的设计缺陷——资源可见性过滤逻辑过于简单，未能处理基于用户组、身份或“全体”的分配规则。此问题不仅影响任务，还可能影响报告等其他所有受权限控制的资源。
**指令目标**: 重构并统一所有资源的可见性过滤逻辑，根除此设计缺陷。

---

## 1. 任务目标 (Objective)

1.  **创建中央过滤工具**: 在一个公共模块中（如 `deps.py` 或新的 `utils.py`）创建一个可重用的函数，名为 `apply_visibility_filters`。此函数将封装所有复杂的可见性过滤逻辑。
2.  **重构现有端点**: 修改 `get_tasks`, `get_task`, `get_reports` (以及其他相关端点) 来调用这个新的中央函数，而不是使用它们各自的、错误的内联逻辑。
3.  **验证全面修复**: 确保所有相关资源的列表和详情接口，对所有用户角色都表现出正确的、一致的权限行为。

---

## 2. 实施步骤 (Implementation Steps)

### **步骤 2.1: 创建可重用的可见性过滤函数**

**这是本次重构的核心。** 我们将把所有过滤逻辑集中到一个地方。

1.  **选择/创建文件**: `backend/app/api/deps.py` 是一个很好的位置，因为它已用于依赖项和用户逻辑。
2.  **添加依赖**: 确保文件顶部有以下导入：
    ```python
    from sqlalchemy.orm import Session, Query
    from sqlalchemy import and_, or_
    from app.models import User, Task, Report, TaskAssignmentType # 导入所有相关模型和枚举
    ```
3.  **添加新函数**: 在 `deps.py` 文件底部添加以下新函数。此函数是通用的，能够处理任何具有相似权限字段的模型。

    ```python
    def apply_visibility_filters(query: Query, user: User, model_class) -> Query:
        """
        一个通用的可见性过滤器，可应用于任何支持标准分配模型的查询。
        :param query: 原始的 SQLAlchemy 查询对象。
        :param user: 当前登录的用户对象。
        :param model_class: 正在查询的模型类 (例如 Task, Report)。
        :return: 应用了可见性过滤后的查询对象。
        """
        if user.is_admin:
            # 管理员可以看到所有内容，直接返回原始查询
            return query

        # 为非管理员构建复合过滤条件
        filters = []

        # 条件1: 资源直接分配给当前用户
        if hasattr(model_class, 'assigned_to'):
            filters.append(
                and_(
                    model_class.assignment_type == TaskAssignmentType.USER, # 假设枚举是通用的
                    model_class.assigned_to == user.id
                )
            )

        # 条件2: 资源分配给所有人
        filters.append(model_class.assignment_type == TaskAssignmentType.ALL)

        # 条件3: 资源分配给当前用户所在的小组
        if user.group_id and hasattr(model_class, 'target_group_id'):
            filters.append(
                and_(
                    model_class.assignment_type == TaskAssignmentType.GROUP,
                    model_class.target_group_id == user.group_id
                )
            )

        # 条件4: 资源分配给当前用户的身份类型
        if user.identity_type and hasattr(model_class, 'target_identity'):
            filters.append(
                and_(
                    model_class.assignment_type == TaskAssignmentType.IDENTITY,
                    model_class.target_identity == user.identity_type
                )
            )
      
        # 应用所有条件，它们之间是 OR 关系
        return query.filter(or_(*filters))
    ```

### **步骤 2.2: 重构任务列表端点 (`get_tasks`)**

现在我们将使用上面的新函数来简化 `get_tasks`。

1.  **打开文件**: `backend/app/main.py`
2.  **导入新函数**: 在文件顶部添加 `from app.api.deps import apply_visibility_filters`。
3.  **简化 `get_tasks` 函数**: 将函数内部的整个 `if not current_user.is_admin:` 代码块替换为对新函数的单行调用。

    **(修改前)**
    ```python
    # ...
    query = db.query(Task)
    if not current_user.is_admin:
        # [大量复杂的、错误的代码在这里]
    # ...
    ```

    **(修改后)**
    ```python
    @app.get("/api/v1/tasks", response_model=List[TaskResponse])
    async def get_tasks(
        # ... 函数签名不变 ...
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        query = db.query(Task)

        # 核心重构：调用中央可见性过滤器
        query = apply_visibility_filters(query, current_user, Task)

        # (可选) 其他现有的过滤条件保持不变
        if status:
            query = query.filter(Task.status == status)
        # ... 其他代码 ...
        tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(size).all()
        return [TaskResponse.from_orm(task) for task in tasks]
    ```

### **步骤 2.3: 重构报告列表端点 (`get_reports`)**

对 `get_reports` 执行完全相同的重构，以证明此模式的通用性。

1.  **打开文件**: `backend/app/main.py` (或 `reports.py` 如果存在)
2.  **定位函数**: `get_reports()`
3.  **简化函数**: 同样，用对 `apply_visibility_filters` 的单行调用替换其内部的权限检查逻辑。

    ```python
    @app.get("/api/v1/reports", response_model=List[ReportResponse])
    async def get_reports(
        # ... 函数签名 ...
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        query = db.query(Report)

        # 核心重构：对 Report 模型应用相同的过滤器
        query = apply_visibility_filters(query, current_user, Report)

        # ... 其他过滤和分页逻辑 ...
        reports = query.order_by(Report.created_at.desc()).offset(offset).limit(size).all()
        return [ReportResponse.from_orm(report) for report in reports]
    ```

### **步骤 2.4: 修复所有“获取单个资源”的端点**

应用 `is_assigned_to_user` 方法来统一单个资源的权限检查。

1.  按照上一份指令中的 `3.2` 和 `3.3` 步骤，修复 `models.py` 中的 `is_assigned_to_user` 方法，并将其应用到 `get_task(task_id: int)` 中。
2.  **举一反三**: 如果存在 `get_report(report_id: int)`，也必须在其中添加相同的权限检查逻辑，调用 `report.is_assigned_to_user(current_user)`。

---

## 3. 验证步骤 (Verification Steps)

重启后端服务后，执行以下扩展验证，确保修复是系统性的。

### **3.1 任务验证 (Task Verification)**
*   (完全同上一份指令的 `4.2` 和 `4.3` 步骤，验证 `test_user` 能看到 6 条任务，且 `admin` 能看到 10 条。)

### **3.2 报告验证 (Report Verification)**
*   **前提**: 为了测试，我们需要一个对 `test_user` 可见的报告。请手动或通过 API 创建一个分配给 `test_user` 所在的小组 (`MYC-SS01Team`, group_id: 1)的报告。
*   **测试用例: 非管理员获取报告列表**
    *   **请求**: `GET /api/v1/reports`
    *   **Header**: `Authorization: Bearer <test_user_token>`
    *   **预期结果**: HTTP `200 OK`。响应的 JSON 数组**至少包含一个**你刚刚创建的、分配给其小组的报告。这证明了重构的成功。

### **3.3 负面测试 (Negative Case Testing)**
*   (同上一份指令的 `4.2 / 测试用例 3`，验证访问一个完全不相关的任务/报告时，会返回 `403 Forbidden`。)

---

## 4. 完成指令 (Completion)

只有当**所有**资源的验证步骤（任务、报告等）的结果都与预期完全一致时，此项重构任务才算完成。

完成后，请报告：“**P0 级系统可见性逻辑已重构并修复完毕，所有关联模块的验证测试均已通过。**”

---

Trae，这份指令更加全面。它不仅修复了眼前的 bug，还提升了整个代码库的质量和可维护性。请立即开始执行。
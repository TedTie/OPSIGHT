from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.schemas import TaskResponse, TaskProgressUpdate, JielongParticipationCreate
from app.crud import task_crud
from app.models import User, Task, JielongRecord, TaskRecord, TaskCompletion
from app.api import deps
from sqlalchemy import desc

router = APIRouter()

# 新 API 1: 更新数量/金额任务进度
@router.put(
    "/{task_id}/progress",
    response_model=TaskResponse,
    summary="更新数量/金额任务的进度"
)
def update_task_progress(
    task_id: int,
    progress_in: TaskProgressUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    为指定 ID 的任务更新进度。
    - **task_id**: 任务的 ID.
    - **progress_in**: 包含新进度值 `value` 的 JSON 对象.
    """
    # 此处应有权限检查逻辑：检查 current_user 是否被分配到此任务
    # (暂时省略，集中实现核心功能)
    
    # 我们假设 task_crud 中有一个函数来处理此事
    updated_task = task_crud.log_task_progress(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        value=progress_in.value
    )
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found or permission denied")
    return updated_task

# 新 API 2: 参与接龙任务（路径与前端保持一致）
@router.post(
    "/{task_id}/jielong",
    status_code=status.HTTP_201_CREATED,
    summary="参与接龙任务"
)
def participate_in_jielong_task(
    task_id: int,
    participation_in: JielongParticipationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """为指定 ID 的接龙任务添加一条参与记录。"""
    # 基本权限检查：管理员或被分配用户可参与
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not (getattr(current_user, "is_admin", False) or task.is_assigned_to_user(current_user)):
        raise HTTPException(status_code=403, detail="无权限参与该任务")

    jielong_record = task_crud.add_jielong_participation(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        data=participation_in,
    )
    if not jielong_record:
        raise HTTPException(status_code=404, detail="任务不存在或不支持接龙类型")
    return {"message": "ok", "record_id": jielong_record.id}


# 新 API 3: 获取接龙任务参与记录列表
@router.get(
    "/{task_id}/jielong",
    summary="获取接龙参与记录列表"
)
def list_jielong_records(
    task_id: int,
    user_id: Optional[int] = Query(default=None, description="按用户ID筛选接龙记录"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """返回指定任务的接龙记录列表，包含用户名称与序号。"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not (getattr(current_user, "is_admin", False) or task.is_assigned_to_user(current_user)):
        raise HTTPException(status_code=403, detail="无权限查看该任务")

    # 权限与组过滤逻辑：
    # - 超级管理员：可筛选任意用户；查看所有用户记录
    # - 管理员：仅查看本组成员记录；筛选的 user_id 必须属于本组
    # - 普通用户：可查看任务下所有记录，但仅可按自身 user_id 进行筛选
    q = db.query(JielongRecord).filter(JielongRecord.task_id == task_id)

    if user_id is not None:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="目标用户不存在")

        if current_user.is_super_admin:
            q = q.filter(JielongRecord.user_id == user_id)
        elif current_user.is_admin:
            if current_user.group_id is None or target_user.group_id != current_user.group_id:
                raise HTTPException(status_code=403, detail="管理员仅可筛选本组成员")
            q = q.filter(JielongRecord.user_id == user_id)
        else:
            if user_id != current_user.id:
                raise HTTPException(status_code=403, detail="无权限按该用户筛选")
            q = q.filter(JielongRecord.user_id == user_id)

    # 管理员“全部”视图：根据任务的分配类型决定可见范围
    # - assignment_type == 'group'：仅本组成员
    # - assignment_type == 'identity'：仅同身份类型成员
    # - assignment_type == 'all'：可以查看所有人的记录
    # - assignment_type == 'user'：通常只涉及单用户，不额外限制
    if current_user.is_admin and not current_user.is_super_admin:
        assignment_type_val = getattr(task.assignment_type, 'value', task.assignment_type)
        if assignment_type_val == 'group':
            if current_user.group_id is None:
                # 管理员无组：返回空（通过一个永不匹配的条件）
                q = q.filter(JielongRecord.user_id == -1)
            else:
                q = q.join(User, JielongRecord.user_id == User.id).filter(User.group_id == current_user.group_id)
        elif assignment_type_val == 'identity':
            # 依据身份类型限制（例如 SS/SA/SZ 等）
            q = q.join(User, JielongRecord.user_id == User.id).filter(User.identity_type == current_user.identity_type)
        elif assignment_type_val in ('all', 'user'):
            # 不额外限制：管理员可查看所有人的记录（与超级管理员一致）
            pass

    records = q.order_by(desc(JielongRecord.created_at)).all()

    # 组装前端期望字段
    items = []
    for idx, rec in enumerate(records, start=1):
        # 获取用户名
        user = db.query(User).filter(User.id == rec.user_id).first()
        items.append({
            "sequence": idx,
            "user_username": user.username if user else None,
            "id": rec.student_id,
            "remark": rec.notes,
            "intention": rec.intention,
            "created_at": rec.created_at,
        })

    return {"items": items, "total": len(items)}


# 新 API 4: 获取金额/数量任务参与记录列表
@router.get(
    "/{task_id}/records",
    summary="获取金额/数量任务的参与记录列表"
)
def list_amount_quantity_records(
    task_id: int,
    user_id: Optional[int] = Query(default=None, description="按用户ID筛选记录"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """返回指定任务的金额/数量参与记录列表。"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 仅支持 amount/quantity 类型
    assignment_type_val = getattr(task.assignment_type, 'value', task.assignment_type)
    task_type_val = getattr(task.task_type, 'value', task.task_type)
    if task_type_val not in ('amount', 'quantity', 'normal'):
        raise HTTPException(status_code=400, detail="该任务类型不支持记录列表")

    # 基本查看权限：管理员或被分配用户可查看
    if not (getattr(current_user, "is_admin", False) or getattr(current_user, "is_super_admin", False) or task.is_assigned_to_user(current_user)):
        raise HTTPException(status_code=403, detail="无权限查看该任务")

    q = db.query(TaskRecord).filter(TaskRecord.task_id == task_id)

    # 用户筛选逻辑
    if user_id is not None:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="目标用户不存在")

        if getattr(current_user, "is_super_admin", False):
            q = q.filter(TaskRecord.user_id == user_id)
        elif getattr(current_user, "is_admin", False):
            if current_user.group_id is None or target_user.group_id != current_user.group_id:
                raise HTTPException(status_code=403, detail="管理员仅可筛选本组成员")
            q = q.filter(TaskRecord.user_id == user_id)
        else:
            if user_id != current_user.id:
                raise HTTPException(status_code=403, detail="无权限按该用户筛选")
            q = q.filter(TaskRecord.user_id == user_id)

    # 管理员“全部”视图的范围限制，依据任务分配类型
    if getattr(current_user, "is_admin", False) and not getattr(current_user, "is_super_admin", False):
        if assignment_type_val == 'group':
            if current_user.group_id is None:
                q = q.filter(TaskRecord.user_id == -1)
            else:
                q = q.join(User, TaskRecord.user_id == User.id).filter(User.group_id == current_user.group_id)
        elif assignment_type_val == 'identity':
            q = q.join(User, TaskRecord.user_id == User.id).filter(User.identity_type == current_user.identity_type)
        elif assignment_type_val in ('all', 'user'):
            pass

    records = q.order_by(desc(TaskRecord.created_at)).all()

    items = []
    for idx, rec in enumerate(records, start=1):
        user = db.query(User).filter(User.id == rec.user_id).first()
        items.append({
            "sequence": idx,
            "user_username": user.username if user else None,
            "value": rec.value,
            "created_at": rec.created_at,
        })

    return {"items": items, "total": len(items)}


# 新 API 5: 获取勾选任务完成记录列表
@router.get(
    "/{task_id}/completions",
    summary="获取勾选任务的完成记录列表"
)
def list_checkbox_completions(
    task_id: int,
    user_id: Optional[int] = Query(default=None, description="按用户ID筛选完成记录"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """返回指定任务的勾选完成记录列表。"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_type_val = getattr(task.task_type, 'value', task.task_type)
    if task_type_val != 'checkbox':
        raise HTTPException(status_code=400, detail="该任务类型不支持完成记录列表")

    # 基本查看权限：管理员或被分配用户可查看
    if not (getattr(current_user, "is_admin", False) or getattr(current_user, "is_super_admin", False) or task.is_assigned_to_user(current_user)):
        raise HTTPException(status_code=403, detail="无权限查看该任务")

    q = db.query(TaskCompletion).filter(TaskCompletion.task_id == task_id, TaskCompletion.is_completed == True)

    # 用户筛选逻辑
    if user_id is not None:
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="目标用户不存在")

        if getattr(current_user, "is_super_admin", False):
            q = q.filter(TaskCompletion.user_id == user_id)
        elif getattr(current_user, "is_admin", False):
            if current_user.group_id is None or target_user.group_id != current_user.group_id:
                raise HTTPException(status_code=403, detail="管理员仅可筛选本组成员")
            q = q.filter(TaskCompletion.user_id == user_id)
        else:
            if user_id != current_user.id:
                raise HTTPException(status_code=403, detail="无权限按该用户筛选")
            q = q.filter(TaskCompletion.user_id == user_id)

    # 管理员“全部”视图的范围限制，依据任务分配类型
    assignment_type_val = getattr(task.assignment_type, 'value', task.assignment_type)
    if getattr(current_user, "is_admin", False) and not getattr(current_user, "is_super_admin", False):
        if assignment_type_val == 'group':
            if current_user.group_id is None:
                q = q.filter(TaskCompletion.user_id == -1)
            else:
                q = q.join(User, TaskCompletion.user_id == User.id).filter(User.group_id == current_user.group_id)
        elif assignment_type_val == 'identity':
            q = q.join(User, TaskCompletion.user_id == User.id).filter(User.identity_type == current_user.identity_type)
        elif assignment_type_val in ('all', 'user'):
            pass

    records = q.order_by(desc(TaskCompletion.completed_at)).all()

    items = []
    for idx, rec in enumerate(records, start=1):
        user = db.query(User).filter(User.id == rec.user_id).first()
        items.append({
            "sequence": idx,
            "user_username": user.username if user else None,
            "completed_at": rec.completed_at,
            "completion_value": rec.completion_value,
            "completion_data": rec.completion_data,
        })

    return {"items": items, "total": len(items)}
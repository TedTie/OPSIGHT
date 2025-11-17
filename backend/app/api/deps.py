from typing import Generator, Type
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_, or_
from fastapi import Depends, Request
from ..db import SessionLocal
from ..auth import get_current_active_user as auth_get_current_active_user
from ..models import User, Task, DailyReport, TaskAssignmentType

def get_db() -> Generator:
    """获取数据库会话"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_active_user(request: Request, db: Session = Depends(get_db)) -> User:
    """获取当前活跃用户（代理至 auth.get_current_active_user 并打印调试信息）"""
    user = auth_get_current_active_user(request, db)
    # --- 临时调试代码：打印解码用户名与DB用户对象 ---
    try:
        decoded_username = request.session.get('username')
        print(
            f"[DEBUG-USER-OBJECT]: Decoded Username='{decoded_username}', DB User Object: id={user.id}, username='{user.username}', role='{user.role}', group_id={getattr(user, 'group_id', None)}, identity_type='{getattr(user, 'identity_type', None)}'"
        )
    except Exception as e:
        print(f"[DEBUG-USER-OBJECT-ERROR]: {e}")
    # --- 结束调试 ---
    return user


def apply_visibility_filters(query: Query, user: User, model_class: Type) -> Query:
    """
    统一的资源可见性过滤器。
    - 超级管理员：返回原始查询（可见所有数据）
    - 任务（Task）：管理员与普通用户均根据 assignment_type 过滤（个人 / 组内 / 身份 / 全员）
    - 日报（DailyReport）：管理员可见全部；普通用户仅可见自己的数据
    - 其他模型：原样返回（不做处理）
    """
    # 超级管理员可见全部
    if getattr(user, "is_super_admin", False):
        return query

    # 任务模型的可见性过滤
    if model_class is Task:
        filters = []

        # 分配给当前用户
        filters.append(
            and_(
                Task.assignment_type == TaskAssignmentType.USER,
                Task.assigned_to == user.id,
            )
        )

        # 分配给所有人
        filters.append(Task.assignment_type == TaskAssignmentType.ALL)

        # 分配给用户所在组
        if user.group_id:
            filters.append(
                and_(
                    Task.assignment_type == TaskAssignmentType.GROUP,
                    Task.target_group_id == user.group_id,
                )
            )

        # 分配给用户身份类型
        if user.identity_type:
            filters.append(
                and_(
                    Task.assignment_type == TaskAssignmentType.IDENTITY,
                    Task.target_identity == user.identity_type,
                )
            )

        return query.filter(or_(*filters))

    # 日报模型的可见性过滤
    if model_class is DailyReport:
        # 可见性规则：
        # - 超管已在上方返回全部
        # - 管理员：
        #   - 若设置了组：仅查看本组成员的日报
        #   - 若未设置组：为避免页面“空数据”体验，允许查看全部日报
        # - 普通用户：仅查看本人
        if getattr(user, "is_admin", False):
            if getattr(user, "group_id", None) is not None:
                return query.join(User, DailyReport.user_id == User.id).filter(User.group_id == user.group_id)
            # 管理员无组时，放宽为查看全部（与 can_view_all_reports 语义更一致）
            return query
        return query.filter(DailyReport.user_id == user.id)

    # 其他模型暂不处理
    return query
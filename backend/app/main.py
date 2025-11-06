# -*- coding: utf-8 -*-
"""
KillerApp Backend Main Application
FastAPI 主应用程序文件
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query, Request, Response
from app.crud import task_crud
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
from collections import defaultdict
import hashlib
import re
import logging
import time
import json
import os
from pathlib import Path

# 导入数据库模型和配置
from .db import SessionLocal, engine, Base, get_db
from .models import (
    User, Task, DailyReport, UserGroup, AIAgent, AIFunction, 
    AICallLog, AISettings, SystemSettings, TaskStatus, CallStatus, TaskAssignmentType, JielongRecord, TaskType,
    TaskRecord, TaskCompletion
)
from .schemas import (
    UserResponse, UserCreateRequest, UserUpdateRequest,
    TaskResponse, TaskCreateRequest, TaskUpdateRequest,
    DailyReportResponse, DailyReportCreateRequest, DailyReportUpdateRequest,
    UserGroupResponse, UserGroupCreateRequest, UserGroupUpdateRequest,
    PaginatedUserGroupResponse,
    AIAgentResponse, AIAgentCreateRequest, AIAgentUpdateRequest,
    AIFunctionResponse, AIFunctionCreateRequest, AIFunctionUpdateRequest,
    AICallLogResponse, AICallResponse, AICallRequest,
    AIStatsResponse, AISettingsResponse, AISettingsUpdateRequest,
    SystemSettingsResponse, SystemSettingsUpdateRequest,
    PaginatedAICallLogResponse, LoginRequest, AuthResponse,
    PaginatedUserResponse, PaginatedTaskResponse,
    AddMembersRequest, RemoveMemberRequest
)
from .api.deps import apply_visibility_filters
from .api.v1.endpoints.tasks import router as tasks_v1_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用
app = FastAPI(
    title="KillerApp API",
    description="企业级任务管理和日报系统",
    version="1.0.0"
)

# 添加会话中间件
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-here-change-in-production",
    max_age=86400  # 24小时
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载子路由：任务相关（v1）
app.include_router(tasks_v1_router, prefix="/api/v1/tasks")

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.4f}s")
    return response

# 全局异常处理
# 重要：HTTPException 需要透传原有状态码与信息，避免全部变成 500
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    try:
        from fastapi import HTTPException as FastAPIHTTPException
        if isinstance(exc, FastAPIHTTPException):
            # 透传 HTTPException 的状态码与消息
            logger.warning(f"HTTPException: status={exc.status_code}, detail={exc.detail}")
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    except Exception:
        # 防御性：即使上面判断失败，也继续统一处理
        pass

    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "内部服务器错误"}
    )

# 安全配置
security = HTTPBearer()

# 获取当前用户（支持会话认证）
def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户（基于会话）"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    # --- 临时调试代码：打印会话解析到的用户对象 ---
    try:
        print(
            f"[DEBUG-USER-OBJECT]: SessionUserID={user_id}, DB User Object: id={user.id}, username='{user.username}', role='{user.role}', group_id={getattr(user, 'group_id', None)}, identity_type='{getattr(user, 'identity_type', None)}'"
        )
    except Exception as e:
        print(f"[DEBUG-USER-OBJECT-ERROR]: {e}")
    # --- 结束调试 ---
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    # --- 临时调试代码：打印活跃用户对象 ---
    try:
        print(
            f"[DEBUG-USER-OBJECT]: Active User: id={current_user.id}, username='{current_user.username}', role='{current_user.role}', group_id={getattr(current_user, 'group_id', None)}, identity_type='{getattr(current_user, 'identity_type', None)}'"
        )
    except Exception as e:
        print(f"[DEBUG-USER-OBJECT-ERROR]: {e}")
    # --- 结束调试 ---
    return current_user

# ==================== 基础路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {"message": "KillerApp API 服务正在运行"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ==================== 认证相关 API ====================

@app.post("/api/v1/auth/login", response_model=AuthResponse)
async def login(
    login_request: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = db.query(User).filter(User.username == login_request.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用"
        )
    
    # 在实际应用中，这里应该验证密码
    # 暂时跳过密码验证
    
    # 设置会话
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    # 兼容依赖的会话读取：同时写入完整用户对象
    # 部分子路由（如 /api/v1/tasks 下的端点）通过 auth.get_current_active_user
    # 从 request.session['user'] 读取用户信息，否则会出现“未认证”
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "group_id": getattr(user, "group_id", None),
        "identity_type": getattr(user, "identity_type", None),
    }
    
    # --- 临时调试代码（会话模拟JWT Payload） ---
    try:
        print(
            f"[DEBUG-JWT-PAYLOAD]: {{'id': {user.id}, 'username': '{user.username}', 'role': '{user.role}', 'group_id': {getattr(user, 'group_id', None)}, 'identity_type': '{getattr(user, 'identity_type', None)}'}}"
        )
    except Exception as e:
        print(f"[DEBUG-JWT-PAYLOAD-ERROR]: {e}")
    # --- 结束调试 ---
    
    return AuthResponse(
        message="登录成功",
        user=UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            identity_type=user.identity_type,
            full_identity=user.get_full_identity(),
            ai_knowledge_branch=user.get_ai_knowledge_branch(),
            organization=user.organization,
            group_id=user.group_id,
            group_name=user.group.name if user.group else None,
            is_active=user.is_active,
            is_admin=user.is_admin,
            is_super_admin=user.is_super_admin,
            created_at=user.created_at
        )
    )

@app.post("/api/v1/auth/logout")
async def logout(request: Request):
    """用户登出"""
    request.session.clear()
    return {"message": "登出成功"}

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        identity_type=current_user.identity_type,
        full_identity=current_user.get_full_identity(),
        ai_knowledge_branch=current_user.get_ai_knowledge_branch(),
        organization=current_user.organization,
        group_id=current_user.group_id,
        group_name=current_user.group.name if current_user.group else None,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        is_super_admin=current_user.is_super_admin,
        created_at=current_user.created_at
    )

@app.get("/api/v1/auth/check")
async def check_auth(current_user: User = Depends(get_current_active_user)):
    """检查认证状态"""
    return {"authenticated": True, "user_id": current_user.id}

# ==================== 用户组管理 API ====================

@app.post("/api/v1/groups", response_model=UserGroupResponse)
async def create_group(
    group_request: UserGroupCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建用户组"""
    # 仅超级管理员可以创建用户组
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    
    # 检查组名是否已存在
    existing_group = db.query(UserGroup).filter(UserGroup.name == group_request.name).first()
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="组名已存在"
        )
    
    group = UserGroup(
        name=group_request.name,
        description=group_request.description
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    
    return UserGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        member_count=0,
        created_at=group.created_at
    )

@app.get("/api/v1/groups", response_model=PaginatedUserGroupResponse)
async def get_groups(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户组列表（分页，支持搜索）"""
    query = db.query(UserGroup)

    if search:
        like = f"%{search}%"
        query = query.filter(or_(UserGroup.name.ilike(like), UserGroup.description.ilike(like)))

    total = query.count()
    offset = (page - 1) * size
    groups = query.order_by(UserGroup.created_at.desc()).offset(offset).limit(size).all()

    items: List[UserGroupResponse] = []
    for group in groups:
        member_count = db.query(User).filter(User.group_id == group.id).count()
        items.append(UserGroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            member_count=member_count,
            created_at=group.created_at,
            updated_at=group.updated_at
        ))

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

@app.get("/api/v1/groups/{group_id}", response_model=UserGroupResponse)
async def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个用户组"""
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户组不存在"
        )
    
    member_count = db.query(User).filter(User.group_id == group.id).count()
    
    return UserGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        member_count=member_count,
        created_at=group.created_at
    )

@app.put("/api/v1/groups/{group_id}", response_model=UserGroupResponse)
async def update_group(
    group_id: int,
    group_request: UserGroupUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新用户组"""
    # 仅超级管理员可以更新用户组
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户组不存在"
        )
    
    # 更新字段
    for field, value in group_request.dict(exclude_unset=True).items():
        setattr(group, field, value)
    
    db.commit()
    db.refresh(group)
    
    member_count = db.query(User).filter(User.group_id == group.id).count()
    
    return UserGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        member_count=member_count,
        created_at=group.created_at
    )

@app.delete("/api/v1/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除用户组"""
    # 仅超级管理员可以删除用户组
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户组不存在"
        )
    
    # 检查是否有用户属于此组
    member_count = db.query(User).filter(User.group_id == group.id).count()
    if member_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法删除：还有 {member_count} 个用户属于此组"
        )
    
    db.delete(group)
    db.commit()
    
    return {"message": "用户组删除成功"}

# 组成员管理端点：管理员可查，超级管理员可改

@app.get("/api/v1/groups/{group_id}/members", response_model=List[UserResponse])
async def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取指定组的成员列表（管理员及以上可查看）"""
    # 允许管理员或超级管理员查看
    if not (current_user.is_admin or current_user.is_super_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户组不存在"
        )

    members = db.query(User).filter(User.group_id == group_id).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            identity_type=user.identity_type,
            full_identity=user.get_full_identity(),
            ai_knowledge_branch=user.get_ai_knowledge_branch(),
            organization=user.organization,
            group_id=user.group_id,
            group_name=user.group.name if user.group else None,
            is_active=user.is_active,
            is_admin=user.is_admin,
            is_super_admin=user.is_super_admin,
            created_at=user.created_at
        ) for user in members
    ]

@app.post("/api/v1/groups/{group_id}/members")
async def add_group_members(
    group_id: int,
    req: AddMembersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """批量添加成员到指定组（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )

    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户组不存在"
        )

    if not req.user_ids:
        return {"message": "未提供用户ID"}

    users = db.query(User).filter(User.id.in_(req.user_ids)).all()
    for u in users:
        u.group_id = group_id
    db.commit()

    return {"message": "成员添加成功", "added_count": len(users)}

@app.delete("/api/v1/groups/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """从组中移除成员（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )

    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户组不存在"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if user.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户不属于该组"
        )

    user.group_id = None
    db.commit()

    return {"message": "成员移除成功"}

# ==================== 用户管理 API ====================

@app.get("/api/v1/users", response_model=PaginatedUserResponse)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户列表"""
    # 权限控制：
    # - 超级管理员：查看所有用户
    # - 管理员：仅查看自己组内用户
    # - 其他：无权限
    if not (current_user.is_super_admin or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员或超级管理员权限"
        )

    query = db.query(User)
    if current_user.is_admin and not current_user.is_super_admin:
        # 管理员仅查看所属组内用户；若未设置组，则返回空列表
        if current_user.group_id is not None:
            query = query.filter(User.group_id == current_user.group_id)
        else:
            query = query.filter(User.id == -1)  # 无结果占位

    total = query.count()
    offset = (page - 1) * size
    users = query.offset(offset).limit(size).all()
    
    items = [
        UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            identity_type=user.identity_type,
            full_identity=user.get_full_identity(),
            ai_knowledge_branch=user.get_ai_knowledge_branch(),
            organization=user.organization,
            group_id=user.group_id,
            group_name=user.group.name if user.group else None,
            is_active=user.is_active,
            is_admin=user.is_admin,
            is_super_admin=user.is_super_admin,
            created_at=user.created_at
        ) for user in users
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个用户"""
    # 用户只能查看自己的信息，只有超级管理员可以查看所有用户
    if not current_user.is_super_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        identity_type=user.identity_type,
        full_identity=user.get_full_identity(),
        ai_knowledge_branch=user.get_ai_knowledge_branch(),
        organization=user.organization,
        group_id=user.group_id,
        group_name=user.group.name if user.group else None,
        is_active=user.is_active,
        is_admin=user.is_admin,
        is_super_admin=user.is_super_admin,
        created_at=user.created_at
    )

@app.put("/api/v1/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新用户信息"""
    # 仅超级管理员可以更新用户信息
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新字段
    for field, value in user_request.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        identity_type=user.identity_type,
        organization=user.organization,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at
    )

@app.delete("/api/v1/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除用户"""
    # 仅超级管理员可以删除用户
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "用户删除成功"}

# ==================== 任务管理 API ====================

@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(
    task_request: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建任务"""
    # 基础字段
    task = Task(
        title=task_request.title,
        description=task_request.description,
        task_type=task_request.task_type,
        priority=task_request.priority,
        status=TaskStatus.PENDING,
        created_by=current_user.id,
        assignment_type=task_request.assignment_type,
        due_date=task_request.due_date
    )

    # 标签（可选，兼容历史数据）
    try:
        task.tags = getattr(task_request, "tags", None)
    except Exception:
        pass

    # 分配映射
    if task_request.assignment_type == TaskAssignmentType.USER:
        if task_request.assigned_user_ids and len(task_request.assigned_user_ids) > 0:
            task.assigned_to = task_request.assigned_user_ids[0]
        else:
            task.assigned_to = current_user.id
        task.target_group_id = None
        task.target_identity = None
    elif task_request.assignment_type == TaskAssignmentType.GROUP:
        if task_request.assigned_group_ids and len(task_request.assigned_group_ids) > 0:
            task.target_group_id = task_request.assigned_group_ids[0]
        task.assigned_to = None
        task.target_identity = None
    elif task_request.assignment_type == TaskAssignmentType.IDENTITY:
        task.target_identity = task_request.target_identity
        task.assigned_to = None
        task.target_group_id = None
    elif task_request.assignment_type == TaskAssignmentType.ALL:
        task.assigned_to = None
        task.target_group_id = None
        task.target_identity = None

    # 类型特定字段
    if task_request.task_type == TaskType.AMOUNT:
        task.target_amount = task_request.target_amount or 0.0
        task.current_amount = 0.0
    elif task_request.task_type == TaskType.QUANTITY:
        task.target_quantity = task_request.target_quantity or 0
        task.current_quantity = 0
    elif task_request.task_type == TaskType.JIELONG:
        task.jielong_target_count = task_request.jielong_target_count or 0
        task.jielong_current_count = 0
        task.jielong_config = task_request.jielong_config or {}
    elif task_request.task_type == TaskType.CHECKBOX:
        task.is_completed = False
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=getattr(task.task_type, 'value', str(task.task_type)),
        assignment_type=getattr(task.assignment_type, 'value', str(task.assignment_type)),
        priority=task.priority,
        tags=task.tags,
        assigned_to=task.assigned_to,
        target_group_id=task.target_group_id,
        target_identity=task.target_identity,
        target_amount=task.target_amount,
        target_quantity=task.target_quantity,
        current_amount=task.current_amount,
        current_quantity=task.current_quantity,
        jielong_target_count=task.jielong_target_count,
        jielong_current_count=task.jielong_current_count,
        jielong_config=task.jielong_config,
        due_date=task.due_date,
        status=getattr(task.status, 'value', str(task.status)),
        is_completed=task.is_completed,
        created_by=task.created_by,
        created_at=task.created_at,
        updated_at=task.updated_at
    )

@app.get("/api/v1/tasks", response_model=PaginatedTaskResponse)
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
    # 核心重构：调用统一的可见性过滤器
    query = apply_visibility_filters(query, current_user, Task)

    # (可选) 其他现有的过滤条件保持不变
    if status:
        query = query.filter(Task.status == status)
    if assigned_to:
        # 仅在管理员视图下，按指定用户ID筛选才有意义
        if current_user.is_admin:
            query = query.filter(Task.assigned_to == assigned_to)

    # 分页和执行查询
    total = query.count() # 为前端分页返回总数
    offset = (page - 1) * size
    tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(size).all()
  
    items = []
    for task in tasks:
        # 为列表项计算个人接龙统计（仅接龙类型）
        personal_current = None
        personal_target = None
        personal_progress = None

        try:
            task_type_val = getattr(task.task_type, 'value', task.task_type)
            if task_type_val == 'jielong':
                personal_current = (
                    db.query(func.count(JielongRecord.id))
                    .filter(JielongRecord.task_id == task.id, JielongRecord.user_id == current_user.id)
                    .scalar()
                ) or 0

                cfg = task.jielong_config if isinstance(task.jielong_config, dict) else {}
                personal_targets = cfg.get('personal_targets') if isinstance(cfg, dict) else None
                if isinstance(personal_targets, dict):
                    personal_target = (
                        personal_targets.get(str(current_user.id))
                        or personal_targets.get(current_user.id)
                        or task.jielong_target_count
                    )
                else:
                    personal_target = task.jielong_target_count

                if personal_target and personal_target > 0:
                    personal_progress = round(float(personal_current) / float(personal_target), 4)
                else:
                    personal_progress = None
        except Exception:
            personal_current = None
            personal_target = None
            personal_progress = None

        items.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            assignment_type=task.assignment_type,
            priority=task.priority,
            tags=getattr(task, 'tags', None),
            assigned_to=getattr(task, 'assigned_to', None),
            target_group_id=getattr(task, 'target_group_id', None),
            target_identity=getattr(task, 'target_identity', None),
            target_amount=task.target_amount,
            target_quantity=task.target_quantity,
            current_amount=getattr(task, 'current_amount', None),
            current_quantity=getattr(task, 'current_quantity', None),
            jielong_target_count=task.jielong_target_count,
            jielong_current_count=getattr(task, 'jielong_current_count', None),
            jielong_config=task.jielong_config,
            due_date=task.due_date,
            status=task.status,
            is_completed=getattr(task, 'is_completed', None),
            created_by=task.created_by,
            created_at=task.created_at,
            updated_at=task.updated_at,
            personal_jielong_current_count=personal_current,
            personal_jielong_target_count=personal_target,
            personal_jielong_progress=personal_progress
        ))

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    view_user_id: Optional[int] = Query(None, description="查看指定用户的个人视角统计（管理员/超管可用）"),
    scope: Optional[str] = Query(None, description="视角：mine 或 all，默认为 mine"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个任务的详细信息"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 核心修复：使用模型层统一的权限检查方法
    if not current_user.is_admin and not task.is_assigned_to_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="你没有权限访问此任务"
        )
  
    # 个人接龙统计（最小改动：仅后端计算，不改动数据库结构）
    personal_jielong_current_count = None
    personal_jielong_target_count = None
    personal_jielong_progress = None
    aggregate_jielong_progress = None

    # 参与人数（用于汇总视角）
    participant_count = None

    # 其他类型的个人/汇总统计占位
    personal_current_amount = None
    personal_target_amount = None
    personal_amount_progress = None
    aggregate_current_amount = None
    aggregate_target_amount = None
    aggregate_amount_progress = None

    personal_current_quantity = None
    personal_target_quantity = None
    personal_quantity_progress = None
    aggregate_current_quantity = None
    aggregate_target_quantity = None
    aggregate_quantity_progress = None

    personal_is_completed = None
    personal_completion_count = None
    completed_count = None
    aggregate_checkbox_progress = None
    # 接龙汇总目标
    aggregate_jielong_target_count = None

    # 解析视角
    scope_val = (scope or "mine").lower()

    try:
        # 兼容 Enum 与字符串类型的 task_type
        task_type_val = getattr(task.task_type, 'value', task.task_type)

        # 计算参与用户集合（用于汇总视角与参与人数）
        def resolve_participants() -> List[int]:
            users_q = db.query(User).filter(User.is_active == True)
            assignment_type_val = getattr(task.assignment_type, 'value', task.assignment_type)
            participant_ids: List[int] = []
            if assignment_type_val == 'user':
                if task.assigned_to:
                    participant_ids = [int(task.assigned_to)]
            elif assignment_type_val == 'group':
                if task.target_group_id:
                    users_q = users_q.filter(User.group_id == task.target_group_id)
                    participant_ids = [u.id for u in users_q.all()]
            elif assignment_type_val == 'identity':
                if task.target_identity:
                    users_q = users_q.filter(User.identity_type == task.target_identity)
                    participant_ids = [u.id for u in users_q.all()]
            elif assignment_type_val == 'all':
                # 管理员：只看本组；超管：所有；普通用户：仅自己
                if current_user.is_super_admin:
                    participant_ids = [u.id for u in users_q.all()]
                elif current_user.is_admin:
                    if current_user.group_id is not None:
                        users_q = users_q.filter(User.group_id == current_user.group_id)
                    participant_ids = [u.id for u in users_q.all()]
                else:
                    participant_ids = [int(current_user.id)]
            # 去重与清洗
            return sorted({int(pid) for pid in participant_ids if pid is not None})

        participants = resolve_participants()
        participant_count = len(participants) if participants else None

        if task_type_val == 'jielong':
            # 基于 view_user_id 的个人统计权限判断
            target_user_id = current_user.id
            if view_user_id is not None:
                target_user = db.query(User).filter(User.id == view_user_id).first()
                if not target_user:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定用户不存在")

                if current_user.is_super_admin:
                    target_user_id = view_user_id
                elif current_user.is_admin:
                    if current_user.group_id is None or target_user.group_id != current_user.group_id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员仅可查看本组成员的个人统计")
                    target_user_id = view_user_id
                else:
                    if view_user_id != current_user.id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看其他用户的个人统计")
                    target_user_id = view_user_id

            # 个人当前接龙数：统计该任务下目标用户的记录数
            personal_jielong_current_count = (
                db.query(func.count(JielongRecord.id))
                .filter(JielongRecord.task_id == task_id, JielongRecord.user_id == target_user_id)
                .scalar()
            ) or 0

            # 个人目标：优先从 jielong_config.personal_targets 读取；否则回落到任务的 jielong_target_count
            cfg = task.jielong_config if isinstance(task.jielong_config, dict) else {}
            personal_targets = cfg.get('personal_targets') if isinstance(cfg, dict) else None
            if isinstance(personal_targets, dict):
                # 同时支持 str/int 键
                personal_jielong_target_count = (
                    personal_targets.get(str(target_user_id))
                    or personal_targets.get(target_user_id)
                    or task.jielong_target_count
                )
            else:
                personal_jielong_target_count = task.jielong_target_count

            if personal_jielong_target_count and personal_jielong_target_count > 0:
                personal_jielong_progress = round(
                    float(personal_jielong_current_count) / float(personal_jielong_target_count),
                    4
                )
            else:
                personal_jielong_progress = None

            # 汇总目标与进度（全部视角）：按参与用户加总目标
            try:
                if participants:
                    cfg2 = task.jielong_config if isinstance(task.jielong_config, dict) else {}
                    personal_targets2 = cfg2.get('personal_targets') if isinstance(cfg2, dict) else None
                    if isinstance(personal_targets2, dict):
                        total_target = 0
                        for uid in participants:
                            t = (
                                personal_targets2.get(str(uid))
                                or personal_targets2.get(uid)
                                or task.jielong_target_count
                            )
                            try:
                                total_target += int(t or 0)
                            except Exception:
                                total_target += 0
                        aggregate_jielong_target_count = total_target
                    else:
                        aggregate_jielong_target_count = (task.jielong_target_count or 0) * len(participants)

                    if aggregate_jielong_target_count and aggregate_jielong_target_count > 0:
                        aggregate_jielong_progress = round(
                            float(getattr(task, 'jielong_current_count', 0) or 0) / float(aggregate_jielong_target_count),
                            4
                        )
                    else:
                        aggregate_jielong_progress = None
                else:
                    aggregate_jielong_progress = None
            except Exception:
                aggregate_jielong_progress = None

        elif task_type_val == 'amount':
            # 个人金额：按用户维度汇总 TaskRecord.value
            target_user_id = current_user.id
            if view_user_id is not None:
                # 权限同接龙个人视角
                target_user = db.query(User).filter(User.id == view_user_id).first()
                if not target_user:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定用户不存在")
                if current_user.is_super_admin:
                    target_user_id = view_user_id
                elif current_user.is_admin:
                    if current_user.group_id is None or target_user.group_id != current_user.group_id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员仅可查看本组成员的个人统计")
                    target_user_id = view_user_id
                else:
                    if view_user_id != current_user.id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看其他用户的个人统计")
                    target_user_id = view_user_id

            personal_current_amount = (
                db.query(func.sum(TaskRecord.value))
                .filter(TaskRecord.task_id == task_id, TaskRecord.user_id == target_user_id)
                .scalar()
            ) or 0.0
            personal_target_amount = task.target_amount or 0.0
            personal_amount_progress = (
                round(float(personal_current_amount) / float(personal_target_amount), 4)
                if personal_target_amount and personal_target_amount > 0 else None
            )

            # 汇总金额（全部视角）
            if participants:
                aggregate_current_amount = (
                    db.query(func.sum(TaskRecord.value))
                    .filter(TaskRecord.task_id == task_id, TaskRecord.user_id.in_(participants))
                    .scalar()
                ) or 0.0
                aggregate_target_amount = (task.target_amount or 0.0) * len(participants)
                aggregate_amount_progress = (
                    round(float(aggregate_current_amount) / float(aggregate_target_amount), 4)
                    if aggregate_target_amount and aggregate_target_amount > 0 else None
                )

        elif task_type_val == 'quantity':
            target_user_id = current_user.id
            if view_user_id is not None:
                target_user = db.query(User).filter(User.id == view_user_id).first()
                if not target_user:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定用户不存在")
                if current_user.is_super_admin:
                    target_user_id = view_user_id
                elif current_user.is_admin:
                    if current_user.group_id is None or target_user.group_id != current_user.group_id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员仅可查看本组成员的个人统计")
                    target_user_id = view_user_id
                else:
                    if view_user_id != current_user.id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看其他用户的个人统计")
                    target_user_id = view_user_id

            personal_current_quantity = (
                db.query(func.sum(TaskRecord.value))
                .filter(TaskRecord.task_id == task_id, TaskRecord.user_id == target_user_id)
                .scalar()
            ) or 0
            # 转换为整数
            try:
                personal_current_quantity = int(personal_current_quantity)
            except Exception:
                personal_current_quantity = 0
            personal_target_quantity = task.target_quantity or 0
            personal_quantity_progress = (
                round(float(personal_current_quantity) / float(personal_target_quantity), 4)
                if personal_target_quantity and personal_target_quantity > 0 else None
            )

            if participants:
                aggregate_current_quantity = (
                    db.query(func.sum(TaskRecord.value))
                    .filter(TaskRecord.task_id == task_id, TaskRecord.user_id.in_(participants))
                    .scalar()
                ) or 0
                try:
                    aggregate_current_quantity = int(aggregate_current_quantity)
                except Exception:
                    aggregate_current_quantity = 0
                aggregate_target_quantity = (task.target_quantity or 0) * len(participants)
                aggregate_quantity_progress = (
                    round(float(aggregate_current_quantity) / float(aggregate_target_quantity), 4)
                    if aggregate_target_quantity and aggregate_target_quantity > 0 else None
                )

        elif task_type_val == 'checkbox':
            # 个人是否完成
            target_user_id = current_user.id
            if view_user_id is not None:
                target_user = db.query(User).filter(User.id == view_user_id).first()
                if not target_user:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定用户不存在")
                if current_user.is_super_admin:
                    target_user_id = view_user_id
                elif current_user.is_admin:
                    if current_user.group_id is None or target_user.group_id != current_user.group_id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员仅可查看本组成员的个人统计")
                    target_user_id = view_user_id
                else:
                    if view_user_id != current_user.id:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看其他用户的个人统计")
                    target_user_id = view_user_id

            personal_is_completed = bool(
                db.query(func.count(TaskCompletion.id))
                .filter(TaskCompletion.task_id == task_id, TaskCompletion.user_id == target_user_id, TaskCompletion.is_completed == True)
                .scalar() or 0
            )
            personal_completion_count = (
                db.query(func.count(TaskCompletion.id))
                .filter(TaskCompletion.task_id == task_id, TaskCompletion.user_id == target_user_id, TaskCompletion.is_completed == True)
                .scalar()
            ) or 0

            if participants:
                completed_count = (
                    db.query(func.count(TaskCompletion.id))
                    .filter(TaskCompletion.task_id == task_id, TaskCompletion.user_id.in_(participants), TaskCompletion.is_completed == True)
                    .scalar()
                ) or 0
                aggregate_checkbox_progress = (
                    round(float(completed_count) / float(len(participants)), 4)
                    if len(participants) > 0 else None
                )
    except Exception:
        # 避免影响主流程：若统计异常则忽略个人统计
        personal_jielong_current_count = None
        personal_jielong_target_count = None
        personal_jielong_progress = None

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        assignment_type=task.assignment_type,
        priority=task.priority,
        tags=getattr(task, 'tags', None),
        assigned_to=getattr(task, 'assigned_to', None),
        target_group_id=getattr(task, 'target_group_id', None),
        target_identity=getattr(task, 'target_identity', None),
        target_amount=task.target_amount,
        target_quantity=task.target_quantity,
        current_amount=getattr(task, 'current_amount', None),
        current_quantity=getattr(task, 'current_quantity', None),
        jielong_target_count=task.jielong_target_count,
        jielong_current_count=getattr(task, 'jielong_current_count', None),
        jielong_config=task.jielong_config,
        due_date=task.due_date,
        status=task.status,
        is_completed=getattr(task, 'is_completed', None),
        created_by=task.created_by,
        created_at=task.created_at,
        updated_at=task.updated_at,
        personal_jielong_current_count=personal_jielong_current_count,
        personal_jielong_target_count=personal_jielong_target_count,
        personal_jielong_progress=personal_jielong_progress,
        aggregate_jielong_progress=aggregate_jielong_progress,
        aggregate_jielong_target_count=aggregate_jielong_target_count,
        participant_count=participant_count,
        personal_current_amount=personal_current_amount,
        personal_target_amount=personal_target_amount,
        personal_amount_progress=personal_amount_progress,
        aggregate_current_amount=aggregate_current_amount,
        aggregate_target_amount=aggregate_target_amount,
        aggregate_amount_progress=aggregate_amount_progress,
        personal_current_quantity=personal_current_quantity,
        personal_target_quantity=personal_target_quantity,
        personal_quantity_progress=personal_quantity_progress,
        aggregate_current_quantity=aggregate_current_quantity,
        aggregate_target_quantity=aggregate_target_quantity,
        aggregate_quantity_progress=aggregate_quantity_progress,
        personal_is_completed=personal_is_completed,
        personal_completion_count=personal_completion_count,
        completed_count=completed_count,
        aggregate_checkbox_progress=aggregate_checkbox_progress
    )

@app.put("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_request: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 检查权限
    if not current_user.is_admin and task.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    update_data = task_request.dict(exclude_unset=True)

    # 标准字段
    for field in ["title", "description", "priority", "due_date"]:
        if field in update_data:
            setattr(task, field, update_data[field])

    # 标签
    if "tags" in update_data:
        task.tags = update_data["tags"]

    # 分配类型与映射
    if "assignment_type" in update_data:
        task.assignment_type = update_data["assignment_type"]
        task.assigned_to = None
        task.target_group_id = None
        task.target_identity = None

        if task.assignment_type == TaskAssignmentType.USER:
            user_ids = update_data.get("assigned_user_ids") or []
            task.assigned_to = user_ids[0] if user_ids else current_user.id
        elif task.assignment_type == TaskAssignmentType.GROUP:
            group_ids = update_data.get("assigned_group_ids") or []
            task.target_group_id = group_ids[0] if group_ids else None
        elif task.assignment_type == TaskAssignmentType.IDENTITY:
            task.target_identity = update_data.get("target_identity")

    # 类型特定字段
    if "task_type" in update_data:
        task.task_type = update_data["task_type"]

    if task.task_type == TaskType.AMOUNT:
        if "target_amount" in update_data:
            task.target_amount = update_data["target_amount"]
    elif task.task_type == TaskType.QUANTITY:
        if "target_quantity" in update_data:
            task.target_quantity = update_data["target_quantity"]
    elif task.task_type == TaskType.JIELONG:
        if "jielong_target_count" in update_data:
            task.jielong_target_count = update_data["jielong_target_count"]
        if "jielong_config" in update_data:
            task.jielong_config = update_data["jielong_config"]
    
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=getattr(task.task_type, 'value', str(task.task_type)),
        assignment_type=getattr(task.assignment_type, 'value', str(task.assignment_type)),
        priority=task.priority,
        tags=task.tags,
        assigned_to=task.assigned_to,
        target_group_id=task.target_group_id,
        target_identity=task.target_identity,
        target_amount=task.target_amount,
        target_quantity=task.target_quantity,
        current_amount=task.current_amount,
        current_quantity=task.current_quantity,
        jielong_target_count=task.jielong_target_count,
        jielong_current_count=task.jielong_current_count,
        jielong_config=task.jielong_config,
        due_date=task.due_date,
        status=getattr(task.status, 'value', str(task.status)),
        is_completed=task.is_completed,
        created_by=task.created_by,
        created_at=task.created_at,
        updated_at=task.updated_at
    )

@app.delete("/api/v1/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 检查权限
    if not current_user.is_admin and task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能删除自己创建的任务"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "任务删除成功"}

# ==================== 日报管理 API ====================

@app.post("/api/v1/reports", response_model=DailyReportResponse)
async def create_report(
    report_request: DailyReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建日报"""
    # 检查当天是否已有日报
    work_date = report_request.work_date or date.today()
    existing_report = db.query(DailyReport).filter(
        DailyReport.user_id == current_user.id,
        DailyReport.work_date == work_date
    ).first()
    
    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当天已有日报，请更新现有日报"
        )
    
    report = DailyReport(
        user_id=current_user.id,
        work_date=work_date,
        title=report_request.title,
        content=report_request.content,
        work_summary=report_request.work_summary,
        work_hours=report_request.work_hours if report_request.work_hours is not None else 0.0,
        task_progress=report_request.task_progress,
        mood_score=report_request.mood_score if report_request.mood_score is not None else 0,
        efficiency_score=report_request.efficiency_score,
        call_count=report_request.call_count,
        call_duration=report_request.call_duration,
        achievements=report_request.achievements,
        challenges=report_request.challenges,
        tomorrow_plan=report_request.tomorrow_plan
    )
    # 若前端提供了任务卡片快照，则写入到 ai_analysis 中，键为 tasks_snapshot
    try:
        if getattr(report_request, "tasks_snapshot", None) is not None:
            report.ai_analysis = {"tasks_snapshot": report_request.tasks_snapshot}
    except Exception:
        # 忽略快照写入异常，确保创建流程不受影响
        report.ai_analysis = report.ai_analysis or None
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return DailyReportResponse(
        id=report.id,
        user_id=report.user_id,
        work_date=report.work_date or date.today(),
        title=report.title or "",
        content=report.content or "",
        work_summary=report.work_summary,
        work_hours=(report.work_hours if report.work_hours is not None else 0.0),
        task_progress=report.task_progress or "",
        mood_score=(report.mood_score if report.mood_score is not None else 0),
        efficiency_score=(report.efficiency_score if report.efficiency_score is not None else 0),
        call_count=(report.call_count if report.call_count is not None else 0),
        call_duration=(report.call_duration if report.call_duration is not None else 0),
        achievements=report.achievements or "",
        challenges=report.challenges or "",
        tomorrow_plan=report.tomorrow_plan or "",
        ai_analysis=report.ai_analysis or {},
        created_at=report.created_at,
        updated_at=report.updated_at
    )

@app.get("/api/v1/reports", response_model=List[DailyReportResponse])
async def get_reports(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    group_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取日报列表"""
    query = db.query(DailyReport)
    
    # 统一的可见性过滤
    query = apply_visibility_filters(query, current_user, DailyReport)

    # 超级管理员：可按用户或组筛选任意范围
    if getattr(current_user, "is_super_admin", False):
        if user_id:
            query = query.filter(DailyReport.user_id == user_id)
        if group_id:
            # 使用用户ID集合过滤，避免重复 join 造成 ORM 冲突
            group_user_ids = _get_group_user_ids(db, group_id)
            if group_user_ids:
                query = query.filter(DailyReport.user_id.in_(group_user_ids))
            else:
                # 空组直接返回空结果集
                query = query.filter(DailyReport.user_id == -1)
    # 管理员：仅限本组
    elif getattr(current_user, "is_admin", False):
        if user_id:
            # 仅允许筛选本组用户的ID；apply_visibility_filters 已限定本组
            query = query.filter(DailyReport.user_id == user_id)
        if group_id is not None:
            if current_user.group_id is None or group_id != current_user.group_id:
                # 非本组ID则拒绝
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限查看其他组的日报")
            # 已通过 apply_visibility_filters 限定为本组，无需重复 join 过滤

    # 日期过滤
    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        query = query.filter(DailyReport.work_date >= start_date_obj)
    if end_date:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        query = query.filter(DailyReport.work_date <= end_date_obj)
    
    # 分页
    offset = (page - 1) * size
    try:
        reports = query.order_by(DailyReport.work_date.desc()).offset(offset).limit(size).all()
        mapped = []
        for r in reports:
            # 防御性映射：兜底必填字段，避免历史脏数据导致响应验证错误
            mapped.append(DailyReportResponse(
                id=r.id,
                user_id=r.user_id,
                work_date=r.work_date or date.today(),
                title=r.title or "",
                content=r.content or "",
                work_summary=r.work_summary,  # 可选字段允许为 None
                work_hours=(r.work_hours if r.work_hours is not None else 0.0),
                task_progress=r.task_progress or "",
                mood_score=(r.mood_score if r.mood_score is not None else 0),
                efficiency_score=(r.efficiency_score if r.efficiency_score is not None else 0),
                call_count=(r.call_count if r.call_count is not None else 0),
                call_duration=(r.call_duration if r.call_duration is not None else 0),
                achievements=r.achievements or "",
                challenges=r.challenges or "",
                tomorrow_plan=r.tomorrow_plan or "",
                ai_analysis=(r.ai_analysis if isinstance(r.ai_analysis, dict) else {}),
                created_at=r.created_at,
                updated_at=r.updated_at
            ))
        return mapped
    except Exception as e:
        # 打印调试信息，便于定位 500 来源
        logger.error(
            "[GET /reports] Failed to list reports | user_id=%s role=%s group_id=%s start=%s end=%s error=%s",
            getattr(current_user, "id", None), getattr(current_user, "role", None), group_id, start_date, end_date, str(e)
        )
        raise

@app.get("/api/v1/reports/{report_id}", response_model=DailyReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个日报"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日报不存在"
        )
    
    # 检查权限（统一使用模型方法）
    if not current_user.is_admin and not report.is_assigned_to_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    return DailyReportResponse(
        id=report.id,
        user_id=report.user_id,
        work_date=report.work_date,
        title=report.title,
        content=report.content,
        work_summary=report.work_summary,
        work_hours=report.work_hours,
        task_progress=report.task_progress,
        mood_score=report.mood_score,
        efficiency_score=report.efficiency_score,
        call_count=report.call_count,
        call_duration=report.call_duration,
        achievements=report.achievements,
        challenges=report.challenges,
        tomorrow_plan=report.tomorrow_plan,
        ai_analysis=report.ai_analysis or {},
        created_at=report.created_at,
        updated_at=report.updated_at
    )

@app.post("/api/v1/reports/{report_id}/build-snapshot", response_model=DailyReportResponse)
async def build_report_tasks_snapshot(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据日报对应用户与日期，自动构建并保存任务卡片明细快照。
    - 分类：今日完成、今日到期、正在进行（未完成）。
    - 权限：管理员（含超管）可为任意用户构建；普通用户仅能为自己的日报构建。
    """
    # 获取日报
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="日报不存在")

    # 权限检查
    if not current_user.is_admin and not report.is_assigned_to_user(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

    # 获取报告所属用户
    target_user = db.query(User).filter(User.id == report.user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告用户不存在")

    # 可见任务过滤（ALL / USER / GROUP / IDENTITY）
    visibility_filter = or_(
        Task.assignment_type == TaskAssignmentType.ALL,
        and_(Task.assignment_type == TaskAssignmentType.USER, Task.assigned_to == target_user.id),
        and_(Task.assignment_type == TaskAssignmentType.GROUP, Task.target_group_id == target_user.group_id),
        and_(Task.assignment_type == TaskAssignmentType.IDENTITY, Task.target_identity == target_user.identity_type)
    )
    tasks = db.query(Task).filter(visibility_filter).all()

    # 工具：按日期比较（忽略时区，仅按日期）
    def is_same_day(dt, d):
        try:
            return (dt is not None) and (dt.date() == d)
        except Exception:
            return False

    # 后端快照映射，尽量补充分配对象展示名
    def map_task_for_snapshot(t: Task):
        assigned_to_username = None
        target_group_name = None
        if t.assignment_type == TaskAssignmentType.USER and t.assigned_to:
            u = db.query(User).filter(User.id == t.assigned_to).first()
            assigned_to_username = u.username if u else None
        if t.assignment_type == TaskAssignmentType.GROUP and t.target_group_id:
            g = db.query(UserGroup).filter(UserGroup.id == t.target_group_id).first()
            target_group_name = g.name if g else None
        return {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "task_type": (t.task_type.value if hasattr(t.task_type, "value") else str(t.task_type)),
            "assignment_type": (t.assignment_type.value if hasattr(t.assignment_type, "value") else str(t.assignment_type)),
            "priority": (t.priority.value if hasattr(t.priority, "value") else str(t.priority)),
            "assigned_to": t.assigned_to,
            "assigned_to_username": assigned_to_username,
            "target_group_id": t.target_group_id,
            "target_group_name": target_group_name,
            "target_identity": t.target_identity,
            "target_amount": t.target_amount,
            "current_amount": t.current_amount,
            "target_quantity": t.target_quantity,
            "current_quantity": t.current_quantity,
            "jielong_target_count": t.jielong_target_count,
            "jielong_current_count": t.jielong_current_count,
            "jielong_config": t.jielong_config,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "status": (t.status.value if hasattr(t.status, "value") else str(t.status)),
            "is_completed": t.is_completed,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }

    work_date = report.work_date
    completed_today = [map_task_for_snapshot(t) for t in tasks if is_same_day(t.updated_at, work_date) and ((t.status == TaskStatus.DONE) or (t.is_completed is True))]
    due_today = [map_task_for_snapshot(t) for t in tasks if (t.due_date is not None) and is_same_day(t.due_date, work_date)]
    ongoing_uncompleted = [map_task_for_snapshot(t) for t in tasks if not ((t.status == TaskStatus.DONE) or (t.is_completed is True)) and ((t.due_date is None) or (t.due_date.date() > work_date))]
    overdue_uncompleted = [map_task_for_snapshot(t) for t in tasks if not ((t.status == TaskStatus.DONE) or (t.is_completed is True)) and (t.due_date is not None) and (t.due_date.date() <= work_date)]

    snapshot = {
        "completed_today": completed_today,
        "due_today": due_today,
        "ongoing_uncompleted": ongoing_uncompleted,
        "overdue_uncompleted": overdue_uncompleted,
        "work_date": work_date.isoformat() if work_date else None,
        "user_id": report.user_id,
        "username": target_user.username,
    }

    # 持久化到 ai_analysis.tasks_snapshot
    try:
        ai = report.ai_analysis if isinstance(report.ai_analysis, dict) else {}
        ai["tasks_snapshot"] = snapshot
        report.ai_analysis = ai
        db.add(report)
        db.commit()
        db.refresh(report)
    except Exception as e:
        logger.error(f"[build-snapshot] Persist failed for report_id={report_id}: {e}")
        raise HTTPException(status_code=500, detail="构建任务快照失败")

    return DailyReportResponse(
        id=report.id,
        user_id=report.user_id,
        work_date=report.work_date,
        title=report.title,
        content=report.content,
        work_summary=report.work_summary,
        work_hours=report.work_hours,
        task_progress=report.task_progress,
        mood_score=report.mood_score,
        efficiency_score=report.efficiency_score,
        call_count=report.call_count,
        call_duration=report.call_duration,
        achievements=report.achievements,
        challenges=report.challenges,
        tomorrow_plan=report.tomorrow_plan,
        ai_analysis=report.ai_analysis or {},
        created_at=report.created_at,
        updated_at=report.updated_at
    )

@app.put("/api/v1/reports/{report_id}", response_model=DailyReportResponse)
async def update_report(
    report_id: int,
    report_request: DailyReportUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新日报"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日报不存在"
        )
    
    # 检查权限
    if not current_user.is_admin and report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能更新自己的日报"
        )
    
    # 更新字段
    payload = report_request.dict(exclude_unset=True)
    # 非结构化字段直接赋值
    for field, value in {k: v for k, v in payload.items() if k != "tasks_snapshot"}.items():
        setattr(report, field, value)

    # 若更新包含任务快照，写入到 ai_analysis.tasks_snapshot
    if "tasks_snapshot" in payload:
        try:
            current_ai = report.ai_analysis if isinstance(report.ai_analysis, dict) else {}
            current_ai["tasks_snapshot"] = payload["tasks_snapshot"]
            report.ai_analysis = current_ai
        except Exception:
            # 出错则忽略，不影响其它字段更新
            pass
    
    report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(report)
    
    return DailyReportResponse(
        id=report.id,
        user_id=report.user_id,
        work_date=report.work_date,
        title=report.title,
        content=report.content,
        work_summary=report.work_summary,
        work_hours=report.work_hours,
        task_progress=report.task_progress,
        mood_score=report.mood_score,
        efficiency_score=report.efficiency_score,
        call_count=report.call_count,
        call_duration=report.call_duration,
        achievements=report.achievements,
        challenges=report.challenges,
        tomorrow_plan=report.tomorrow_plan,
        ai_analysis=report.ai_analysis or {},
        created_at=report.created_at,
        updated_at=report.updated_at
    )

@app.delete("/api/v1/reports/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除日报"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日报不存在"
        )
    
    # 检查权限
    if not current_user.is_admin and report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能删除自己的日报"
        )
    
    db.delete(report)
    db.commit()
    
    return {"message": "日报删除成功"}

# ==================== AI 分析日报 ====================

@app.post("/api/v1/reports/{report_id}/ai-analysis")
async def analyze_report_with_ai(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI 分析日报"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日报不存在"
        )
    
    # 检查权限
    if not current_user.is_admin and report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 模拟 AI 分析结果
    analysis_result = {
        "emotion_analysis": {
            "overall_mood": "积极",
            "mood_score": report.mood_score,
            "key_emotions": ["满意", "专注", "有成就感"]
        },
        "efficiency_analysis": {
            "efficiency_score": report.efficiency_score,
            "productivity_level": "高效" if report.efficiency_score >= 8 else "中等" if report.efficiency_score >= 6 else "需改进",
            "suggestions": ["保持当前工作节奏", "适当休息避免疲劳"]
        },
        "work_summary": {
            "key_achievements": ["完成重要任务", "团队协作良好"],
            "areas_for_improvement": ["时间管理可以更优化"],
            "next_day_focus": ["继续推进项目进度"]
        }
    }
    
    return {
        "report_id": report_id,
        "analysis": analysis_result,
        "analyzed_at": datetime.now().isoformat()
    }

# ==================== 统计分析 API ====================

@app.get("/api/v1/stats/overview")
async def get_stats_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取统计概览"""
    try:
        # 根据用户权限获取数据
        if current_user.role == "user":
            # 普通用户只获取自己的数据
            tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
            reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
        elif current_user.role == "super_admin":
            # 超级管理员可以查看所有数据
            tasks = db.query(Task).all()
            reports = db.query(DailyReport).all()
        elif current_user.role == "admin":
            # 普通管理员只能查看自己组织的数据
            if current_user.organization:
                # 获取组织内的用户
                org_users = db.query(User).filter(User.organization == current_user.organization).all()
                org_user_ids = [u.id for u in org_users]
                tasks = db.query(Task).filter(Task.assigned_to.in_(org_user_ids)).all()
                reports = db.query(DailyReport).filter(DailyReport.user_id.in_(org_user_ids)).all()
            else:
                # 如果没有组织信息，只获取自己的数据
                tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
                reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
        else:
            # 默认情况，只获取自己的数据
            tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
            reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()

        if not reports:
            return {
                "avgCompletionTime": 0,
                "weeklyCompletionRate": 0,
                "totalWorkHours": 0
            }
        
        # 计算平均工作时间
        total_hours = sum(report.work_hours for report in reports)
        avg_hours = total_hours / len(reports) if reports else 0
        
        # 计算平均效率评分作为完成率
        avg_efficiency = sum(report.efficiency_score for report in reports) / len(reports) if reports else 0
        completion_rate = (avg_efficiency / 10) * 100  # 转换为百分比
        
        return {
            "avgCompletionTime": round(avg_hours, 1),
            "weeklyCompletionRate": round(completion_rate, 1),
            "totalWorkHours": round(total_hours, 1)
        }
    except Exception as e:
        print(f"获取统计失败: {e}")
        # 返回默认值
        return {
            "avgCompletionTime": 4.5,
            "weeklyCompletionRate": 85,
            "totalWorkHours": 42
        }

# ==================== 数据分析API ====================

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取仪表盘数据"""
    # 根据用户权限获取数据
    if current_user.role == "user":
        # 普通用户只获取自己的数据
        tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
        reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
    elif current_user.role == "super_admin":
        # 超级管理员可以查看所有数据
        tasks = db.query(Task).all()
        reports = db.query(DailyReport).all()
    elif current_user.role == "admin":
        # 普通管理员只能查看自己组织的数据
        if current_user.organization:
            # 获取组织内的用户
            org_users = db.query(User).filter(User.organization == current_user.organization).all()
            org_user_ids = [u.id for u in org_users]
            tasks = db.query(Task).filter(Task.assigned_to.in_(org_user_ids)).all()
            reports = db.query(DailyReport).filter(DailyReport.user_id.in_(org_user_ids)).all()
        else:
            # 如果没有组织信息，只获取自己的数据
            tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
            reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
    else:
        # 默认情况，只获取自己的数据
        tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
        reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()

    # 计算任务统计
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "done"])
    pending_tasks = len([t for t in tasks if t.status == "pending"])
    processing_tasks = len([t for t in tasks if t.status == "processing"])

    # 计算日报统计
    total_reports = len(reports)
    avg_mood = sum(r.mood_score for r in reports) / total_reports if total_reports > 0 else 0
    avg_efficiency = sum(r.efficiency_score for r in reports) / total_reports if total_reports > 0 else 0
    total_work_hours = sum(r.work_hours for r in reports)

    # 获取最近的任务和日报
    recent_tasks = sorted(tasks, key=lambda x: x.created_at, reverse=True)[:5]
    recent_reports = sorted(reports, key=lambda x: x.created_at, reverse=True)[:5]

    return {
        "task_stats": {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks,
            "processing": processing_tasks,
            "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2)
        },
        "report_stats": {
            "total": total_reports,
            "avg_mood": round(avg_mood, 2),
            "avg_efficiency": round(avg_efficiency, 2),
            "total_work_hours": round(total_work_hours, 2)
        },
        "recent_tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "created_at": t.created_at.isoformat() if t.created_at else None
            } for t in recent_tasks
        ],
        "recent_reports": [
            {
                "id": r.id,
                "report_date": r.report_date.isoformat() if r.report_date else None,
                "mood_score": r.mood_score,
                "efficiency_score": r.efficiency_score,
                "work_hours": r.work_hours,
                "work_summary": r.work_summary,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in recent_reports
        ]
    }

@app.get("/api/v1/analytics/task-stats")
async def get_task_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取任务统计数据"""
    # 根据用户权限获取数据
    if current_user.role == "user":
        tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
    else:
        tasks = db.query(Task).all()

    # 按状态统计
    status_stats = {}
    for task in tasks:
        status = task.status
        status_stats[status] = status_stats.get(status, 0) + 1

    # 按优先级统计
    priority_stats = {}
    for task in tasks:
        priority = task.priority or "medium"
        priority_stats[priority] = priority_stats.get(priority, 0) + 1

    # 按任务类型统计
    type_stats = {}
    for task in tasks:
        task_type = task.task_type or "checkbox"
        type_stats[task_type] = type_stats.get(task_type, 0) + 1

    return {
        "status_distribution": [
            {"name": status, "value": count} for status, count in status_stats.items()
        ],
        "priority_distribution": [
            {"name": priority, "value": count} for priority, count in priority_stats.items()
        ],
        "type_distribution": [
            {"name": task_type, "value": count} for task_type, count in type_stats.items()
        ]
    }

@app.get("/api/v1/tasks/stats/summary")
async def get_task_stats_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取任务统计摘要"""
    # 根据用户权限获取数据
    if current_user.role == "user":
        tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
        reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
    else:
        tasks = db.query(Task).all()
        reports = db.query(DailyReport).all()

    # 计算任务统计
    pending_tasks = len([t for t in tasks if t.status == "pending"])
    in_progress_tasks = len([t for t in tasks if t.status == "processing"])
    completed_tasks = len([t for t in tasks if t.status == "done"])
    
    # 计算本周日报数量
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    reports_this_week = len([r for r in reports if r.created_at >= week_start])

    return {
        "total": len(tasks),
        "pending": pending_tasks,
        "processing": in_progress_tasks,
        "done": completed_tasks,
        "reportsThisWeek": reports_this_week
    }

@app.get("/api/v1/reports/stats/summary")
async def get_reports_stats_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取日报统计摘要"""
    # 根据用户权限获取数据
    if current_user.role == "user":
        reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
    else:
        reports = db.query(DailyReport).all()

    # 计算日报统计
    total_reports = len(reports)
    
    # 计算平均情绪分数
    avg_emotion_score = sum(r.mood_score for r in reports) / total_reports if total_reports > 0 else 0
    
    # 计算平均效率分数
    avg_efficiency_score = sum(r.efficiency_score for r in reports) / total_reports if total_reports > 0 else 0
    
    # 计算总工作时长
    total_work_hours = sum(r.work_hours for r in reports)
    
    # 计算本周日报数量
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    reports_this_week = len([r for r in reports if r.created_at >= week_start])

    return {
        "total_reports": total_reports,
        "avg_emotion_score": round(avg_emotion_score, 1),
        "avg_efficiency_score": round(avg_efficiency_score, 1),
        "total_work_hours": total_work_hours,
        "reports_this_week": reports_this_week
    }

@app.get("/api/v1/tasks/weekly-trend")
async def get_weekly_task_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取本周任务趋势"""
    # 根据用户权限获取数据
    if current_user.role == "user":
        tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
    else:
        tasks = db.query(Task).all()

    # 计算本周每天的任务数量
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    
    weekly_data = []
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # 统计当天创建的任务数量
        day_tasks = [t for t in tasks if day_start <= t.created_at < day_end]
        
        weekly_data.append({
            "date": weekdays[i],
            "count": len(day_tasks)
        })
    
    return weekly_data

# ==================== 任务同步（前端快捷参与/勾选） ====================
@app.post("/api/v1/task-sync/sync-task-to-report")
async def sync_task_to_report(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    前端快捷参与入口：金额/数量任务记录一次进度。
    请求体示例：{"task_id": 1, "amount": 100.5, "remark": "..."}
    或：{"task_id": 2, "quantity": 3, "remark": "..."}
    """
    task_id = payload.get("task_id")
    if not task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 task_id")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    # 权限：管理员或被分配用户
    if not (getattr(current_user, "is_admin", False) or task.is_assigned_to_user(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限参与该任务")

    # 解析数值（兼容 Enum 与大小写差异）
    task_type_val = getattr(task.task_type, "value", task.task_type)
    task_type_val = str(task_type_val).lower()
    value = payload.get("amount") if task_type_val == "amount" else payload.get("quantity")
    if value is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少进度数值")

    updated_task = task_crud.log_task_progress(db=db, task_id=task_id, user_id=current_user.id, value=float(value))
    if not updated_task:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="记录进度失败")

    # 返回简单确认；前端仅需 200 状态即可刷新
    return {"message": "ok"}


@app.put("/api/v1/task-sync/sync-task-to-report/{task_id}")
async def toggle_checkbox_task(
    task_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """前端勾选任务快捷切换完成状态。请求体：{"is_completed": true}"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    if task.task_type != "checkbox":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持勾选类型任务")

    # 权限：管理员或被分配用户
    if not (getattr(current_user, "is_admin", False) or task.is_assigned_to_user(current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限操作该任务")

    is_completed = bool(payload.get("is_completed"))
    task.is_completed = is_completed
    task.updated_at = datetime.now()
    try:
        db.commit()
        db.refresh(task)
        return {"message": "ok", "is_completed": task.is_completed}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新失败: {e}")

# ==================== 管理员指标 API ====================

@app.get("/api/v1/admin/metrics/stats")
async def get_admin_metrics_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取管理员指标统计"""
    # 检查管理员权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    try:
        # 根据用户权限获取数据
        if current_user.role == "super_admin":
            # 超级管理员可以查看所有数据
            users = db.query(User).all()
            tasks = db.query(Task).all()
            reports = db.query(DailyReport).all()
        elif current_user.role == "admin":
            # 普通管理员只能查看自己组织的数据
            if current_user.organization:
                # 获取组织内的用户
                users = db.query(User).filter(User.organization == current_user.organization).all()
                user_ids = [u.id for u in users]
                tasks = db.query(Task).filter(Task.assigned_to.in_(user_ids)).all()
                reports = db.query(DailyReport).filter(DailyReport.user_id.in_(user_ids)).all()
            else:
                # 如果没有组织信息，只获取自己的数据
                users = [current_user]
                tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
                reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
        else:
            # 默认情况，只获取自己的数据
            users = [current_user]
            tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
            reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
        
        # 计算统计数据
        total_users = len(users)
        active_users = len([u for u in users if u.is_active])
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == "done"])
        total_reports = len(reports)
        
        # 计算完成率
        task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 计算平均工作时间
        avg_work_hours = sum(r.work_hours for r in reports) / len(reports) if reports else 0
        
        return {
            "totalUsers": total_users,
            "activeUsers": active_users,
            "totalTasks": total_tasks,
            "completedTasks": completed_tasks,
            "totalReports": total_reports,
            "taskCompletionRate": round(task_completion_rate, 1),
            "avgWorkHours": round(avg_work_hours, 1)
        }
    except Exception as e:
        print(f"获取管理员统计失败: {e}")
        # 返回默认值
        return {
            "totalUsers": 0,
            "activeUsers": 0,
            "totalTasks": 0,
            "completedTasks": 0,
            "totalReports": 0,
            "taskCompletionRate": 0,
            "avgWorkHours": 0
        }

# ==================== 新版数据分析 API ====================

def _parse_date_range(start_date: Optional[str], end_date: Optional[str]) -> (date, date):
    """解析日期范围，默认最近一月"""
    if start_date and end_date:
        try:
            return date.fromisoformat(start_date), date.fromisoformat(end_date)
        except Exception:
            pass
    today = date.today()
    first = (today.replace(day=1))
    # 上月最后一天 = 本月1号 - 1天，但我们取最近一月到今天
    return first, today

def _get_group_user_ids(db: Session, group_id: Optional[int]) -> List[int]:
    if not group_id:
        return []
    users = db.query(User).filter(User.group_id == group_id).all()
    return [u.id for u in users]

def _visible_tasks_query(db: Session, current_user: User, start_d: date, end_d: date, group_id: Optional[int]):
    q = db.query(Task)
    # 时间范围：按创建时间或截止时间在范围内
    start_dt = datetime.combine(start_d, datetime.min.time())
    end_dt = datetime.combine(end_d, datetime.max.time())
    q = q.filter(
        or_(
            and_(Task.created_at != None, Task.created_at >= start_dt, Task.created_at <= end_dt),
            and_(Task.due_date != None, Task.due_date >= start_dt, Task.due_date <= end_dt)
        )
    )
    # 组过滤（管理员/超管）
    if group_id and (current_user.is_admin or current_user.is_super_admin):
        group_user_ids = _get_group_user_ids(db, group_id)
        if group_user_ids:
            q = q.filter(
                or_(
                    Task.assigned_to.in_(group_user_ids),
                    Task.target_group_id == group_id
                )
            )
    # 权限可见性
    q = apply_visibility_filters(q, Task, current_user)
    return q

def _visible_reports_query(db: Session, current_user: User, start_d: date, end_d: date, group_id: Optional[int]):
    q = db.query(DailyReport)
    q = q.filter(DailyReport.work_date >= start_d, DailyReport.work_date <= end_d)
    if group_id and (current_user.is_admin or current_user.is_super_admin):
        group_user_ids = _get_group_user_ids(db, group_id)
        if group_user_ids:
            q = q.filter(DailyReport.user_id.in_(group_user_ids))
    q = apply_visibility_filters(q, DailyReport, current_user)
    return q

def _compute_dataset_fingerprint(tasks: List[Task], reports: List[DailyReport], scope: Dict[str, Any]) -> str:
    """根据任务/日报ID、更新时间和范围参数生成指纹，用于结果复用"""
    task_ids = sorted([t.id for t in tasks])
    report_ids = sorted([r.id for r in reports])
    last_task_update = max([t.updated_at or t.created_at for t in tasks], default=datetime.fromtimestamp(0))
    last_report_update = max([r.updated_at or r.created_at for r in reports], default=datetime.fromtimestamp(0))
    payload = {
        "task_ids": task_ids,
        "report_ids": report_ids,
        "last_task_update": (last_task_update.isoformat() if isinstance(last_task_update, datetime) else str(last_task_update)),
        "last_report_update": (last_report_update.isoformat() if isinstance(last_report_update, datetime) else str(last_report_update)),
        "scope": scope,
    }
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

@app.get("/api/v1/analytics/stats")
async def analytics_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """统计卡片：任务、完成率、日报、平均情感分"""
    s, e = _parse_date_range(start_date, end_date)
    tasks_q = _visible_tasks_query(db, current_user, s, e, group_id)
    reports_q = _visible_reports_query(db, current_user, s, e, group_id)
    tasks = tasks_q.all()
    reports = reports_q.all()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if (t.status == TaskStatus.DONE or (isinstance(t.status, str) and t.status == "done")))
    completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks else 0, 1)
    total_reports = len(reports)
    avg_emotion = round((sum(r.mood_score for r in reports) / total_reports) if total_reports else 0, 2)
    return {
        "totalTasks": total_tasks,
        "completedTasks": completed_tasks,
        "completionRate": completion_rate,
        "totalReports": total_reports,
        "avgEmotionScore": avg_emotion,
    }

# 兼容前端旧路径（无版本前缀）
@app.get("/analytics/stats")
async def analytics_stats_alias(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_stats(start_date, end_date, group_id, db, current_user)

@app.get("/api/v1/analytics/charts")
async def analytics_charts(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """图表数据：任务趋势、状态分布、优先级、情绪趋势、AI使用"""
    s, e = _parse_date_range(start_date, end_date)
    tasks_q = _visible_tasks_query(db, current_user, s, e, group_id)
    reports_q = _visible_reports_query(db, current_user, s, e, group_id)
    # 任务趋势（每日已完成数与新增数）
    date_cursor = s
    trend = []
    while date_cursor <= e:
        day_start = datetime.combine(date_cursor, datetime.min.time())
        day_end = datetime.combine(date_cursor, datetime.max.time())
        created_count = tasks_q.filter(Task.created_at >= day_start, Task.created_at <= day_end).count()
        completed_count = tasks_q.filter(
            or_(
                Task.status == TaskStatus.DONE,
                (isinstance(Task.status, str) and Task.status == "done")
            ),
            Task.updated_at != None,
            Task.updated_at >= day_start,
            Task.updated_at <= day_end
        ).count()
        trend.append({
            "date": date_cursor.isoformat(),
            "created": created_count,
            "completed": completed_count
        })
        date_cursor = date_cursor + timedelta(days=1)
    # 状态分布
    status_distribution = defaultdict(int)
    for t in tasks_q.all():
        status = t.status.value if hasattr(t.status, "value") else str(t.status)
        status_distribution[status] += 1
    status_data = [{"name": k, "value": v} for k, v in status_distribution.items()]
    # 优先级分布
    priority_map = {"urgent": "高优先级", "high": "高优先级", "medium": "中优先级", "low": "低优先级"}
    priority_distribution = defaultdict(int)
    for t in tasks_q.all():
        pr = t.priority.value if hasattr(t.priority, "value") else str(t.priority or "medium")
        priority_distribution[priority_map.get(pr, "中优先级")] += 1
    priority_data = [{"priority": k, "count": v} for k, v in priority_distribution.items()]
    # 情感趋势（日报）
    emotion_trend = []
    rep_by_date = defaultdict(list)
    for r in reports_q.all():
        rep_by_date[r.work_date].append(r)
    cursor = s
    while cursor <= e:
        reps = rep_by_date.get(cursor, [])
        avg = (sum(x.mood_score for x in reps) / len(reps)) if reps else 0
        # 前端期望 0-1 范围，这里简单缩放（十分制 -> 小数）
        score = round(avg / 10.0, 2)
        emotion_trend.append({"date": cursor.isoformat(), "score": score})
        cursor = cursor + timedelta(days=1)
    # AI 使用统计
    start_dt = datetime.combine(s, datetime.min.time())
    end_dt = datetime.combine(e, datetime.max.time())
    ai_total_calls = db.query(AICallLog).filter(AICallLog.created_at >= start_dt, AICallLog.created_at <= end_dt).count()
    ai_total_tokens = (db.query(func.sum(AICallLog.request_tokens)).filter(AICallLog.created_at >= start_dt, AICallLog.created_at <= end_dt).scalar() or 0) + \
                     (db.query(func.sum(AICallLog.response_tokens)).filter(AICallLog.created_at >= start_dt, AICallLog.created_at <= end_dt).scalar() or 0)
    ai_total_cost = db.query(func.sum(AICallLog.cost)).filter(AICallLog.created_at >= start_dt, AICallLog.created_at <= end_dt).scalar() or 0.0
    ai_avg_proc_ms = db.query(func.avg(AICallLog.duration_ms)).filter(AICallLog.created_at >= start_dt, AICallLog.created_at <= end_dt).scalar() or 0.0
    ai_stats = {
        "total_calls": ai_total_calls,
        "total_tokens": int(ai_total_tokens or 0),
        "total_cost": float(ai_total_cost or 0),
        "avg_processing_time": round((ai_avg_proc_ms or 0) / 1000.0, 3),
    }
    return {
        "taskTrend": trend,
        "taskStatus": status_data,
        "priorityDistribution": priority_data,
        "emotionTrend": emotion_trend,
        "ai_stats": ai_stats,
    }

# 兼容前端旧路径（无版本前缀）
@app.get("/analytics/charts")
async def analytics_charts_alias(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_charts(start_date, end_date, group_id, db, current_user)

@app.get("/api/v1/analytics/user-performance")
async def analytics_user_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """管理员/超管：用户绩效排行"""
    if not (current_user.is_admin or current_user.is_super_admin):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    s, e = _parse_date_range(start_date, end_date)
    # 选取用户范围
    if group_id:
        user_ids = _get_group_user_ids(db, group_id)
        users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
    else:
        users = db.query(User).all() if current_user.is_super_admin else db.query(User).filter(User.group_id == current_user.group_id).all()
    results = []
    for u in users:
        t_q = _visible_tasks_query(db, u if u.is_admin else current_user, s, e, group_id)
        # 注意：apply_visibility_filters 按当前用户可见性过滤，这里使用当前请求用户可见的数据
        t_q = t_q.filter(or_(Task.assigned_to == u.id, Task.created_by == u.id))
        r_q = _visible_reports_query(db, current_user, s, e, group_id).filter(DailyReport.user_id == u.id)
        total_tasks = t_q.count()
        completed_tasks = t_q.filter(
            or_(Task.status == TaskStatus.DONE, (isinstance(Task.status, str) and Task.status == "done"))
        ).count()
        completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks else 0, 1)
        total_reports = r_q.count()
        avg_emotion = r_q.with_entities(func.avg(DailyReport.mood_score)).scalar() or 0
        results.append({
            "username": u.username,
            "totalTasks": total_tasks,
            "completedTasks": completed_tasks,
            "completionRate": completion_rate,
            "totalReports": total_reports,
            "avgEmotionScore": round(avg_emotion / 10.0, 2),
        })
    # 排序：完成率、已完成任务数、日报数
    results.sort(key=lambda x: (x["completionRate"], x["completedTasks"], x["totalReports"]), reverse=True)
    return results

# 兼容前端旧路径（无版本前缀）
@app.get("/analytics/user-performance")
async def analytics_user_performance_alias(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_user_performance(start_date, end_date, group_id, db, current_user)

@app.get("/api/v1/analytics/ai-insights")
async def analytics_ai_insights(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI洞察：基于权限与筛选的数据集进行分析，并结果留存与复用"""
    s, e = _parse_date_range(start_date, end_date)
    tasks = _visible_tasks_query(db, current_user, s, e, group_id).all()
    reports = _visible_reports_query(db, current_user, s, e, group_id).all()

    # 构造范围参数用于指纹/复用
    scope_params = {
        "start_date": s.isoformat(),
        "end_date": e.isoformat(),
        "group_id": group_id,
        "viewer_id": current_user.id,
        "role": current_user.role,
    }
    fingerprint = _compute_dataset_fingerprint(tasks, reports, scope_params)

    # 选择活跃的AI功能（优先 CUSTOM 作为数据洞察）
    ai_function = db.query(AIFunction).filter(AIFunction.is_active == True).order_by(AIFunction.created_at.desc()).first()

    # 查找可复用的调用记录
    reused_response = None
    if ai_function:
        prior_logs = db.query(AICallLog).filter(
            AICallLog.function_id == ai_function.id,
            AICallLog.user_id == current_user.id,
            AICallLog.status == CallStatus.SUCCESS,
        ).order_by(AICallLog.created_at.desc()).limit(5).all()
        for prior in prior_logs:
            try:
                if prior.request_data and prior.request_data.get("fingerprint") == fingerprint and prior.response_data:
                    reused_response = prior.response_data
                    break
            except Exception:
                continue

    # 若无法复用，则生成新分析（模拟）并写入日志
    response_payload = None
    if not reused_response:
        # 统计情绪范围与平均
        moods = [r.mood_score for r in reports]
        emotion_stats = {
            "totalAnalyzed": len(reports),
            "avgEmotion": round((sum(moods) / len(moods)) / 10.0, 2) if moods else 0,
            "minEmotion": round((min(moods) / 10.0) if moods else 0, 2),
            "maxEmotion": round((max(moods) / 10.0) if moods else 0, 2),
        }
        # 常见关键词（简单规则：英文/数字/下划线词频；中文场景退化为空/少量）
        text_pool = []
        for r in reports:
            if r.content:
                text_pool.append(r.content)
            if r.work_summary:
                text_pool.append(r.work_summary)
            if r.task_progress:
                text_pool.append(r.task_progress)
        tokens = []
        for t in text_pool:
            tokens.extend(re.findall(r"[A-Za-z0-9_]{2,}", t))
        freq = defaultdict(int)
        for tok in tokens:
            freq[tok.lower()] += 1
        common_keywords = [{"keyword": k, "frequency": v} for k, v in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:20]]
        # 模型使用情况
        start_dt = datetime.combine(s, datetime.min.time())
        end_dt = datetime.combine(e, datetime.max.time())
        model_rows = db.query(AIAgent.model_name, func.count(AICallLog.id), func.avg(AICallLog.duration_ms)).\
            join(AICallLog, AIAgent.id == AICallLog.agent_id).\
            filter(AICallLog.created_at >= start_dt, AICallLog.created_at <= end_dt).\
            group_by(AIAgent.model_name).all()
        model_usage = [{
            "model": m or "未知模型",
            "count": int(c or 0),
            "avgProcessingTime": round((avg or 0) / 1000.0, 3)
        } for m, c, avg in model_rows]

        response_payload = {
            "emotion_stats": emotion_stats,
            "common_keywords": common_keywords,
            "model_usage": model_usage,
        }

        # 写日志（模拟AI调用）
        if ai_function:
            start_time = datetime.utcnow()
            call_log = AICallLog(
                function_id=ai_function.id,
                agent_id=ai_function.agent_id,
                user_id=current_user.id,
                request_data={
                    "fingerprint": fingerprint,
                    "scope": scope_params,
                    "dataset": {
                        "task_count": len(tasks),
                        "report_count": len(reports),
                    }
                },
                status=CallStatus.PENDING,
                duration_ms=0,
                started_at=start_time
            )
            db.add(call_log)
            db.commit()
            db.refresh(call_log)
            # 完成记录
            call_log.status = CallStatus.SUCCESS
            call_log.response_data = response_payload
            call_log.response_tokens = 0
            call_log.request_tokens = 0
            call_log.duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            call_log.completed_at = datetime.utcnow()
            db.commit()
    else:
        response_payload = reused_response

    return response_payload or {"emotion_stats": {"totalAnalyzed": 0, "avgEmotion": 0, "minEmotion": 0, "maxEmotion": 0}, "common_keywords": [], "model_usage": []}

# 兼容前端旧路径（无版本前缀）
@app.get("/analytics/ai-insights")
async def analytics_ai_insights_alias(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_ai_insights(start_date, end_date, group_id, db, current_user)

@app.get("/api/v1/admin/metrics")
async def get_admin_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """获取管理员指标列表"""
    # 检查管理员权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    try:
        # 模拟指标数据
        metrics = [
            {
                "id": 1,
                "name": "用户活跃率",
                "description": "用户日常使用情况",
                "value": 85.5,
                "unit": "%",
                "frequency": "daily",
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": 2,
                "name": "任务完成率",
                "description": "任务按时完成的比率",
                "value": 92.3,
                "unit": "%",
                "frequency": "weekly",
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # 分页
        start = (page - 1) * size
        end = start + size
        items = metrics[start:end]
        
        return {
            "items": items,
            "total": len(metrics),
            "page": page,
            "size": size
        }
    except Exception as e:
        print(f"获取指标列表失败: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "size": size
        }

# ==================== AI 管理 API ====================

# 智能体配置 CRUD
@app.post("/api/v1/ai/agents", response_model=AIAgentResponse)
async def create_ai_agent(
    agent_request: AIAgentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建智能体配置"""
    if not current_user.can_manage_ai():
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        agent = AIAgent(
            name=agent_request.name,
            description=agent_request.description,
            provider=agent_request.provider,
            model_name=agent_request.model_name,
            system_prompt=agent_request.system_prompt,
            temperature=agent_request.temperature,
            max_tokens=agent_request.max_tokens,
            is_active=agent_request.is_active,
            created_by=current_user.id
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        return AIAgentResponse(**agent.to_dict())
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建智能体失败: {str(e)}")

@app.get("/api/v1/ai/agents", response_model=List[AIAgentResponse])
async def get_ai_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取智能体列表"""
    try:
        agents = db.query(AIAgent).order_by(AIAgent.created_at.desc()).all()
        return [AIAgentResponse(**agent.to_dict()) for agent in agents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体列表失败: {str(e)}")

@app.get("/api/v1/ai/agents/{agent_id}", response_model=AIAgentResponse)
async def get_ai_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个智能体配置"""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    return AIAgentResponse(**agent.to_dict())

@app.put("/api/v1/ai/agents/{agent_id}", response_model=AIAgentResponse)
async def update_ai_agent(
    agent_id: int,
    agent_request: AIAgentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新智能体配置"""
    if not current_user.can_manage_ai():
        raise HTTPException(status_code=403, detail="权限不足")
    
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    try:
        for field, value in agent_request.dict(exclude_unset=True).items():
            setattr(agent, field, value)
        
        agent.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(agent)
        
        return AIAgentResponse(**agent.to_dict())
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新智能体失败: {str(e)}")

@app.delete("/api/v1/ai/agents/{agent_id}")
async def delete_ai_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除智能体配置"""
    if not current_user.can_manage_ai():
        raise HTTPException(status_code=403, detail="权限不足")
    
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    try:
        # 检查是否有AI功能正在使用此智能体
        functions_using_agent = db.query(AIFunction).filter(AIFunction.agent_id == agent_id).count()
        if functions_using_agent > 0:
            raise HTTPException(status_code=400, detail=f"无法删除：有 {functions_using_agent} 个AI功能正在使用此智能体")
        
        db.delete(agent)
        db.commit()
        return {"message": "智能体删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除智能体失败: {str(e)}")

# AI功能配置 CRUD
@app.post("/api/v1/ai/functions", response_model=AIFunctionResponse)
async def create_ai_function(
    function_request: AIFunctionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建AI功能配置"""
    if not current_user.can_manage_ai():
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 验证智能体是否存在
    if function_request.agent_id:
        agent = db.query(AIAgent).filter(AIAgent.id == function_request.agent_id).first()
        if not agent:
            raise HTTPException(status_code=400, detail="指定的智能体不存在")
    
    try:
        function = AIFunction(
            name=function_request.name,
            description=function_request.description,
            function_type=function_request.function_type,
            agent_id=function_request.agent_id,
            is_active=function_request.is_active,
            created_by=current_user.id
        )
        db.add(function)
        db.commit()
        db.refresh(function)
        
        return AIFunctionResponse(**function.to_dict())
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建AI功能失败: {str(e)}")

@app.get("/api/v1/ai/functions", response_model=List[AIFunctionResponse])
async def get_ai_functions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取AI功能列表"""
    try:
        functions = db.query(AIFunction).order_by(AIFunction.created_at.desc()).all()
        return [AIFunctionResponse(**func.to_dict()) for func in functions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI功能列表失败: {str(e)}")

@app.put("/api/v1/ai/functions/{function_id}", response_model=AIFunctionResponse)
async def update_ai_function(
    function_id: int,
    function_request: AIFunctionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新AI功能配置"""
    if not current_user.can_manage_ai():
        raise HTTPException(status_code=403, detail="权限不足")
    
    function = db.query(AIFunction).filter(AIFunction.id == function_id).first()
    if not function:
        raise HTTPException(status_code=404, detail="AI功能不存在")
    
    # 验证智能体是否存在
    if function_request.agent_id:
        agent = db.query(AIAgent).filter(AIAgent.id == function_request.agent_id).first()
        if not agent:
            raise HTTPException(status_code=400, detail="指定的智能体不存在")
    
    try:
        for field, value in function_request.dict(exclude_unset=True).items():
            setattr(function, field, value)
        
        function.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(function)
        
        return AIFunctionResponse(**function.to_dict())
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新AI功能失败: {str(e)}")

# AI调用记录
@app.get("/api/v1/ai/logs", response_model=PaginatedAICallLogResponse)
async def get_ai_call_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    function_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取AI调用记录"""
    try:
        query = db.query(AICallLog)
        
        # 过滤条件
        if function_id:
            query = query.filter(AICallLog.function_id == function_id)
        if status:
            query = query.filter(AICallLog.status == status)
        
        # 分页
        total = query.count()
        logs = query.order_by(AICallLog.created_at.desc()).offset((page - 1) * size).limit(size).all()
        
        # 构造响应数据
        log_items = []
        for log in logs:
            log_items.append(AICallLogResponse(
                id=log.id,
                function_id=log.function_id,
                function_name=log.function.name if log.function else None,
                function_type=log.function.function_type.value if log.function and log.function.function_type else None,
                agent_id=log.agent_id,
                agent_name=log.agent.name if log.agent else None,
                user_id=log.user_id,
                username=log.user.username if log.user else None,
                request_data=log.request_data,
                request_tokens=log.request_tokens,
                response_data=log.response_data,
                response_tokens=log.response_tokens,
                status=log.status.value if hasattr(log.status, 'value') else str(log.status),
                error_message=log.error_message,
                duration_ms=log.duration_ms,
                cost=log.cost,
                started_at=log.started_at,
                completed_at=log.completed_at,
                created_at=log.created_at
            ))
        
        return PaginatedAICallLogResponse(
            items=log_items,
            total=total,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取调用记录失败: {str(e)}")

@app.post("/api/v1/ai/call", response_model=AICallResponse)
async def call_ai_function(
    call_request: AICallRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """调用AI功能"""
    # 获取AI功能配置
    function = db.query(AIFunction).filter(
        AIFunction.id == call_request.function_id,
        AIFunction.is_active == True
    ).first()
    
    if not function:
        raise HTTPException(status_code=404, detail="AI功能不存在或已禁用")
    
    if not function.agent:
        raise HTTPException(status_code=400, detail="AI功能未配置智能体")
    
    # 创建调用记录
    input_text = call_request.input_data.get('input_text', str(call_request.input_data))
    start_time = datetime.utcnow()
    call_log = AICallLog(
        function_id=function.id,
        agent_id=function.agent_id,
        user_id=current_user.id,
        request_data=call_request.input_data,
        status=CallStatus.PENDING,
        duration_ms=0,  # 稍后更新
        started_at=start_time
    )
    db.add(call_log)
    db.commit()
    db.refresh(call_log)
    
    try:
        # 这里应该调用实际的AI服务
        # 暂时返回模拟响应
        response_data = {
            "response": f"[模拟AI响应] 功能: {function.name}, 输入: {input_text}",
            "analysis": "这是一个积极正面的文本，表达了愉快的情绪"
        }
        
        # 更新调用记录
        call_log.response_data = response_data
        call_log.status = CallStatus.SUCCESS
        call_log.completed_at = datetime.utcnow()
        call_log.duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        call_log.request_tokens = len(input_text)
        call_log.response_tokens = len(str(response_data))
        call_log.cost = 0.001  # 模拟费用
        
        db.commit()
        
        return AICallResponse(
            success=True,
            data=response_data,
            call_log_id=call_log.id
        )
        
    except Exception as e:
        # 更新调用记录为失败状态
        call_log.status = CallStatus.FAILED
        call_log.error_message = str(e)
        call_log.completed_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"AI调用失败: {str(e)}")

@app.get("/api/v1/ai/stats", response_model=AIStatsResponse)
async def get_ai_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取AI统计信息"""
    try:
        # 统计智能体数量
        total_agents = db.query(AIAgent).count()
        active_agents = db.query(AIAgent).filter(AIAgent.is_active == True).count()
        
        # 统计AI功能数量
        total_functions = db.query(AIFunction).count()
        active_functions = db.query(AIFunction).filter(AIFunction.is_active == True).count()
        
        # 统计调用次数
        total_calls = db.query(AICallLog).count()
        success_calls = db.query(AICallLog).filter(AICallLog.status == CallStatus.SUCCESS).count()
        failed_calls = db.query(AICallLog).filter(AICallLog.status == CallStatus.FAILED).count()
        
        # 统计今日调用次数
        today = datetime.utcnow().date()
        today_calls = db.query(AICallLog).filter(
            AICallLog.created_at >= today
        ).count()
        
        # 计算成功率
        success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0.0
        
        # 计算平均响应时间
        avg_duration = db.query(func.avg(AICallLog.duration_ms)).scalar() or 0.0
        
        # 计算总费用
        total_cost = db.query(func.sum(AICallLog.cost)).scalar() or 0.0
        
        # 按功能统计调用次数
        calls_by_function = {}
        function_stats = db.query(
            AIFunction.name, 
            func.count(AICallLog.id).label('count')
        ).join(AICallLog, AIFunction.id == AICallLog.function_id, isouter=True).group_by(AIFunction.name).all()
        
        for func_name, count in function_stats:
            calls_by_function[func_name or "未知"] = count or 0
        
        # 按状态统计调用次数
        calls_by_status = {}
        status_stats = db.query(
            AICallLog.status, 
            func.count(AICallLog.id).label('count')
        ).group_by(AICallLog.status).all()
        
        for status, count in status_stats:
            calls_by_status[status.value if hasattr(status, 'value') else str(status)] = count
        
        # 获取最近的调用记录
        recent_calls_query = db.query(AICallLog).order_by(AICallLog.created_at.desc()).limit(10)
        recent_calls = []
        for call in recent_calls_query:
            recent_calls.append(AICallLogResponse(
                id=call.id,
                function_id=call.function_id,
                function_name=call.function.name if call.function else None,
                function_type=call.function.function_type.value if call.function and call.function.function_type else None,
                agent_id=call.agent_id,
                agent_name=call.agent.name if call.agent else None,
                user_id=call.user_id,
                username=call.user.username if call.user else None,
                request_data=call.request_data,
                request_tokens=call.request_tokens,
                response_data=call.response_data,
                response_tokens=call.response_tokens,
                status=call.status.value if hasattr(call.status, 'value') else str(call.status),
                error_message=call.error_message,
                duration_ms=call.duration_ms,
                cost=call.cost,
                started_at=call.started_at,
                completed_at=call.completed_at,
                created_at=call.created_at
            ))
        
        return AIStatsResponse(
            total_calls=total_calls,
            success_calls=success_calls,
            failed_calls=failed_calls,
            success_rate=success_rate,
            avg_duration_ms=avg_duration,
            total_cost=total_cost,
            calls_by_function=calls_by_function,
            calls_by_status=calls_by_status,
            recent_calls=recent_calls
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

# ==================== 设置管理 API ====================

@app.get("/api/v1/settings/ai", response_model=AISettingsResponse)
async def get_ai_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取AI设置"""
    # 只有管理员可以查看AI设置
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看AI设置"
        )
    
    # 获取AI设置，如果不存在则创建默认设置
    ai_settings = db.query(AISettings).first()
    if not ai_settings:
        ai_settings = AISettings()
        db.add(ai_settings)
        db.commit()
        db.refresh(ai_settings)
    
    return ai_settings

@app.put("/api/v1/settings/ai", response_model=AISettingsResponse)
async def update_ai_settings(
    settings_data: AISettingsUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新AI设置"""
    # 只有管理员可以修改AI设置
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改AI设置"
        )
    
    # 获取或创建AI设置
    ai_settings = db.query(AISettings).first()
    if not ai_settings:
        ai_settings = AISettings()
        db.add(ai_settings)
    
    # 更新设置
    for field, value in settings_data.dict(exclude_unset=True).items():
        setattr(ai_settings, field, value)
    
    db.commit()
    db.refresh(ai_settings)
    
    return ai_settings

@app.get("/api/v1/settings/system", response_model=SystemSettingsResponse)
async def get_system_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取系统设置"""
    # 只有管理员可以查看系统设置
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看系统设置"
        )
    
    # 获取系统设置，如果不存在则创建默认设置
    system_settings = db.query(SystemSettings).first()
    if not system_settings:
        system_settings = SystemSettings()
        db.add(system_settings)
        db.commit()
        db.refresh(system_settings)
    
    return system_settings

@app.put("/api/v1/settings/system", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_data: SystemSettingsUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新系统设置"""
    # 只有管理员可以修改系统设置
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改系统设置"
        )
    
    # 获取或创建系统设置
    system_settings = db.query(SystemSettings).first()
    if not system_settings:
        system_settings = SystemSettings()
        db.add(system_settings)
    
    # 更新设置
    for field, value in settings_data.dict(exclude_unset=True).items():
        setattr(system_settings, field, value)
    
    db.commit()
    db.refresh(system_settings)
    
    return system_settings

# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """启动时初始化数据"""
    db = next(get_db())
    
    # 检查是否已存在 admin 用户
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if not existing_admin:
        # 创建默认超级管理员
        admin_user = User(
            username="admin",
            role="super_admin",
            identity_type="CC",  # 默认为CC身份
            organization="系统管理"
        )
        db.add(admin_user)
        db.commit()
        print("✓ 已创建默认超级管理员: admin")
        print("请使用用户名 'admin' 登录系统")
    else:
        # 确保该用户是超级管理员
        if existing_admin.role != "super_admin":
            existing_admin.role = "super_admin"
            if not existing_admin.identity_type:
                existing_admin.identity_type = "CC"  # 默认为CC身份
            db.commit()
            print("✓ 已将用户 'admin' 升级为超级管理员")
        else:
            print("✓ 超级管理员 'admin' 已存在")
    
    db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

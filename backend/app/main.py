# -*- coding: utf-8 -*-
"""
KillerApp Backend Main Application
FastAPI 主应用程序文件
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query, Request, Response, Body
from app.crud import task_crud
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, and_, or_, text
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
    User, Task, DailyReport, UserGroup, AIAgent, AIFunction, AIFunctionType,
    AICallLog, AISettings, SystemSettings, TaskStatus, CallStatus, TaskAssignmentType, JielongRecord, TaskType,
    TaskRecord, TaskCompletion, MonthlyGoal, NotificationRead
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
    AddMembersRequest, RemoveMemberRequest,
    MonthlyGoalUpsertRequest, MonthlyGoalResponse,
    AISystemKnowledgeResponse, AIChatRequest, AIChatResponse,
    AIAnswerRequest, AIAnswerResponse,
    NotificationReadSyncRequest, NotificationReadMapResponse
)
from .api.deps import apply_visibility_filters
from .api.v1.endpoints.tasks import router as tasks_v1_router
from .core.security import verify_password, get_password_hash

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 运行时迁移：为 daily_reports 表添加新增销售相关列（SQLite 兼容）
def _ensure_daily_report_sales_columns():
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        cols = [c['name'] for c in inspector.get_columns('daily_reports')]
        
        additions = [
            ("new_sign_count", "INTEGER DEFAULT 0"),
            ("new_sign_amount", "FLOAT DEFAULT 0.0"),
            ("renewal_count", "INTEGER DEFAULT 0"),
            ("upgrade_count", "INTEGER DEFAULT 0"),
            ("referral_count", "INTEGER DEFAULT 0"),
            ("referral_amount", "FLOAT DEFAULT 0.0"),
            ("renewal_amount", "FLOAT DEFAULT 0.0"),
            ("upgrade_amount", "FLOAT DEFAULT 0.0"),
        ]
        
        with engine.connect() as conn:
            for name, decl in additions:
                if name not in cols:
                    try:
                        conn.execute(text(f"ALTER TABLE daily_reports ADD COLUMN {name} {decl};"))
                        conn.commit()
                        logger.info(f"Added column daily_reports.{name}")
                    except Exception as e:
                        logger.warning(f"Failed to add column {name}: {e}")
    except Exception as e:
        logger.warning(f"DailyReport column ensure failed: {e}")

_ensure_daily_report_sales_columns()

# 运行时迁移：为 monthly_goals 表添加新增目标金额列（SQLite 兼容）
def _ensure_monthly_goal_target_columns():
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        cols = [c['name'] for c in inspector.get_columns('monthly_goals')]
        
        additions = [
            ("new_sign_target_amount", "FLOAT DEFAULT 0.0"),
            ("referral_target_amount", "FLOAT DEFAULT 0.0"),
            ("renewal_total_target_amount", "FLOAT DEFAULT 0.0"),
        ]
        
        with engine.connect() as conn:
            for name, decl in additions:
                if name not in cols:
                    try:
                        conn.execute(text(f"ALTER TABLE monthly_goals ADD COLUMN {name} {decl};"))
                        conn.commit()
                        logger.info(f"Added column monthly_goals.{name}")
                    except Exception as e:
                        logger.warning(f"Failed to add column {name}: {e}")
    except Exception as e:
        logger.warning(f"MonthlyGoal column ensure failed: {e}")

_ensure_monthly_goal_target_columns()

# 运行时迁移：确保 users 表存在 hashed_password 列
def _ensure_users_password_column():
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        cols = [c['name'] for c in inspector.get_columns('users')]
        
        if "hashed_password" not in cols:
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password TEXT;"))
                    conn.commit()
                    logger.info("Added column users.hashed_password")
            except Exception as e:
                logger.warning(f"Failed to add users.hashed_password: {e}")
    except Exception as e:
        logger.warning(f"Users password column ensure failed: {e}")

_ensure_users_password_column()

def _ensure_default_admin_user():
    try:
        db = SessionLocal()
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                role="super_admin",
                identity_type="sa",
                is_active=True,
                hashed_password=get_password_hash("admin123"))
            db.add(admin)
            db.commit()
        elif not admin.hashed_password:
            admin.hashed_password = get_password_hash("admin123")
            db.commit()

        demo = db.query(User).filter(User.username == "demo").first()
        if not demo:
            demo = User(
                username="demo",
                role="super_admin",
                identity_type="sa",
                is_active=True,
                hashed_password=get_password_hash("demo123"))
            db.add(demo)
            db.commit()
        db.close()
    except Exception as e:
        logger.warning(f"Default admin ensure failed: {e}")

_ensure_default_admin_user()

# 运行时初始化：确保默认功能点存在（若有默认智能体）
def _ensure_default_ai_functions():
    try:
        db = SessionLocal()
        # 查找默认智能体
        default_agent = db.query(AIAgent).filter(AIAgent.is_active == True, AIAgent.is_default == True).order_by(AIAgent.created_at.asc()).first()
        if not default_agent:
            # 若无默认智能体，则跳过
            db.close()
            return

        existing = {f.name for f in db.query(AIFunction).all()}
        need_create = []
        if "个人数据洞察" not in existing:
            need_create.append("个人数据洞察")
        if "团队数据洞察" not in existing:
            need_create.append("团队数据洞察")

        for name in need_create:
            func = AIFunction(
                name=name,
                description=("AI 输出组织：个人视角" if name == "个人数据洞察" else "AI 输出组织：团队视角"),
                function_type=AIFunctionType.CUSTOM,
                agent_id=default_agent.id,
                is_active=True,
                created_by=1  # 默认由系统创建；如无用户1，后续更新
            )
            db.add(func)
        if need_create:
            db.commit()
        db.close()
    except Exception as e:
        # 初始化失败不影响服务启动
        logger.warning(f"初始化默认AI功能失败: {e}")

_ensure_default_ai_functions()

# 创建 FastAPI 应用
app = FastAPI(
    title="KillerApp API",
    description="企业级任务管理和日报系统",
    version="1.0.0"
)

# 添加会话中间件
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "replace-this-in-prod"),
    max_age=86400
)

origins_env = os.getenv("ALLOWED_ORIGINS")
origins = [o.strip() for o in origins_env.split(",") if o.strip()] if origins_env else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    response: Response,
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
    
    # 密码验证
    if not user.hashed_password or not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
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
    
    # 记住我：设置 30 天的复活 Cookie（不含敏感信息，仅 user_id）
    if login_request.remember_me:
        response.set_cookie(
            key="remember_me_user_id",
            value=str(user.id),
            max_age=30 * 24 * 60 * 60,
            httponly=True
        )
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
async def logout(request: Request, response: Response):
    """用户登出"""
    request.session.clear()
    response.delete_cookie("remember_me_user_id")
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

@app.post("/api/v1/users", response_model=UserResponse)
async def create_user(
    user_request: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建用户（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )

    if not user_request.username or len(user_request.username) < 3:
        raise HTTPException(status_code=400, detail="用户名长度至少3位")
    if not user_request.password or len(user_request.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少6位")

    exists = db.query(User).filter(User.username == user_request.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")

    is_active_val = getattr(user_request, "is_active", True)
    new_user = User(
        username=user_request.username,
        role=user_request.role,
        identity_type=user_request.identity_type,
        organization=user_request.organization,
        group_id=user_request.group_id,
        is_active=is_active_val if is_active_val is not None else True,
        hashed_password=get_password_hash(user_request.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        identity_type=new_user.identity_type,
        full_identity=new_user.get_full_identity(),
        ai_knowledge_branch=new_user.get_ai_knowledge_branch(),
        organization=new_user.organization,
        group_id=new_user.group_id,
        group_name=new_user.group.name if new_user.group else None,
        is_active=new_user.is_active,
        is_admin=new_user.is_admin,
        is_super_admin=new_user.is_super_admin,
        created_at=new_user.created_at
    )

@app.get("/api/v1/users", response_model=PaginatedUserResponse)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
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
    # 过滤条件（兼容前端筛选）
    if search:
        query = query.filter(User.username.like(f"%{search}%"))
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
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
    
    # 更新字段（处理密码单独逻辑）
    update_data = user_request.dict(exclude_unset=True)
    # 若前端传入 password，则进行校验与哈希后写入 hashed_password
    if "password" in update_data:
        pwd = update_data.pop("password")
        if pwd:
            if len(pwd) < 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="密码长度至少6位"
                )
            user.hashed_password = get_password_hash(pwd)
    # 其余字段直接更新
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
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
        new_sign_count=report_request.new_sign_count,
        new_sign_amount=report_request.new_sign_amount,
        renewal_count=report_request.renewal_count,
        upgrade_count=report_request.upgrade_count,
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
        new_sign_count=(report.new_sign_count if report.new_sign_count is not None else 0),
        new_sign_amount=(report.new_sign_amount if report.new_sign_amount is not None else 0.0),
        referral_count=(getattr(report, 'referral_count', 0) or 0),
        referral_amount=(getattr(report, 'referral_amount', 0.0) or 0.0),
        renewal_count=(report.renewal_count if report.renewal_count is not None else 0),
        renewal_amount=(getattr(report, 'renewal_amount', 0.0) or 0.0),
        upgrade_count=(report.upgrade_count if report.upgrade_count is not None else 0),
        upgrade_amount=(getattr(report, 'upgrade_amount', 0.0) or 0.0),
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
                new_sign_count=(getattr(r, 'new_sign_count', 0) or 0),
                new_sign_amount=(getattr(r, 'new_sign_amount', 0.0) or 0.0),
                referral_count=(getattr(r, 'referral_count', 0) or 0),
                referral_amount=(getattr(r, 'referral_amount', 0.0) or 0.0),
                renewal_count=(getattr(r, 'renewal_count', 0) or 0),
                renewal_amount=(getattr(r, 'renewal_amount', 0.0) or 0.0),
                upgrade_count=(getattr(r, 'upgrade_count', 0) or 0),
                upgrade_amount=(getattr(r, 'upgrade_amount', 0.0) or 0.0),
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
        referral_count=(getattr(report, 'referral_count', 0) or 0),
        referral_amount=(getattr(report, 'referral_amount', 0.0) or 0.0),
        new_sign_count=(getattr(report, 'new_sign_count', 0) or 0),
        new_sign_amount=(getattr(report, 'new_sign_amount', 0.0) or 0.0),
        renewal_count=(getattr(report, 'renewal_count', 0) or 0),
        renewal_amount=(getattr(report, 'renewal_amount', 0.0) or 0.0),
        upgrade_count=(getattr(report, 'upgrade_count', 0) or 0),
        upgrade_amount=(getattr(report, 'upgrade_amount', 0.0) or 0.0),
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
        referral_count=(getattr(report, 'referral_count', 0) or 0),
        referral_amount=(getattr(report, 'referral_amount', 0.0) or 0.0),
        new_sign_count=(getattr(report, 'new_sign_count', 0) or 0),
        new_sign_amount=(getattr(report, 'new_sign_amount', 0.0) or 0.0),
        renewal_count=(getattr(report, 'renewal_count', 0) or 0),
        renewal_amount=(getattr(report, 'renewal_amount', 0.0) or 0.0),
        upgrade_count=(getattr(report, 'upgrade_count', 0) or 0),
        upgrade_amount=(getattr(report, 'upgrade_amount', 0.0) or 0.0),
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
        new_sign_count=(getattr(report, 'new_sign_count', 0) or 0),
        new_sign_amount=(getattr(report, 'new_sign_amount', 0.0) or 0.0),
        renewal_count=(getattr(report, 'renewal_count', 0) or 0),
        upgrade_count=(getattr(report, 'upgrade_count', 0) or 0),
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

# ==================== 通知已读同步 ====================
@app.get("/api/v1/notifications/read-map", response_model=NotificationReadMapResponse)
async def get_notification_read_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """返回当前用户已读通知ID列表，用于多端同步。"""
    records = db.query(NotificationRead).filter(NotificationRead.user_id == current_user.id).all()
    ids = [r.notification_id for r in records]
    return NotificationReadMapResponse(ids=ids)


@app.post("/api/v1/notifications/read")
async def sync_notification_read(
    payload: NotificationReadSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """同步已读通知ID；幂等插入，不会重复。"""
    ids = list(set(payload.ids or []))
    if not ids:
        return {"message": "ok", "saved": 0}

    # 查询已存在记录，避免重复
    existing = db.query(NotificationRead).\
        filter(NotificationRead.user_id == current_user.id, NotificationRead.notification_id.in_(ids)).\
        all()
    existing_ids = {r.notification_id for r in existing}

    to_create = [i for i in ids if i not in existing_ids]
    for nid in to_create:
        db.add(NotificationRead(user_id=current_user.id, notification_id=str(nid)))
    try:
        if to_create:
            db.commit()
        return {"message": "ok", "saved": len(to_create)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"同步失败: {e}")

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

# ==================== 系统维护 API ====================
@app.delete("/api/v1/system/purge")
async def purge_data_keep_admin(
    keep_admin_tasks: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if not getattr(current_user, "is_super_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限")

    admin = db.query(User).filter(User.username == "admin").first()
    if not admin or not getattr(admin, "is_super_admin", False):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="admin 超级管理员不存在或角色异常")

    admin_id = admin.id

    deleted = {
        "ai_call_logs": 0,
        "task_completions": 0,
        "task_records": 0,
        "daily_reports": 0,
        "jielong_records": 0,
        "tasks": 0,
        "users": 0,
        "user_groups": 0,
        "monthly_goals": 0,
        "notification_reads": 0,
        "ai_agents": 0,
        "ai_functions": 0,
    }

    try:
        q_logs = db.query(AICallLog).filter(AICallLog.user_id != admin_id)
        deleted["ai_call_logs"] = q_logs.count()
        q_logs.delete(synchronize_session=False)

        q_tc = db.query(TaskCompletion).filter(TaskCompletion.user_id != admin_id)
        deleted["task_completions"] = q_tc.count()
        q_tc.delete(synchronize_session=False)

        q_tr = db.query(TaskRecord).filter(TaskRecord.user_id != admin_id)
        deleted["task_records"] = q_tr.count()
        q_tr.delete(synchronize_session=False)

        q_reports = db.query(DailyReport).filter(DailyReport.user_id != admin_id)
        deleted["daily_reports"] = q_reports.count()
        q_reports.delete(synchronize_session=False)

        q_jr = db.query(JielongRecord).filter(JielongRecord.user_id != admin_id)
        deleted["jielong_records"] = q_jr.count()
        q_jr.delete(synchronize_session=False)

        if keep_admin_tasks:
            q_tasks = db.query(Task).filter(
                and_(
                    Task.created_by != admin_id,
                    or_(Task.assigned_to != admin_id, Task.assigned_to.is_(None)),
                )
            )
        else:
            q_tasks = db.query(Task)
        deleted["tasks"] = q_tasks.count()
        q_tasks.delete(synchronize_session=False)

        q_nr = db.query(NotificationRead).filter(NotificationRead.user_id != admin_id)
        deleted["notification_reads"] = q_nr.count()
        q_nr.delete(synchronize_session=False)

        q_goals = db.query(MonthlyGoal)
        deleted["monthly_goals"] = q_goals.count()
        q_goals.delete(synchronize_session=False)

        q_funcs = db.query(AIFunction)
        deleted["ai_functions"] = q_funcs.count()
        q_funcs.delete(synchronize_session=False)

        q_agents = db.query(AIAgent)
        deleted["ai_agents"] = q_agents.count()
        q_agents.delete(synchronize_session=False)

        q_users = db.query(User).filter(User.id != admin_id)
        deleted["users"] = q_users.count()
        q_users.delete(synchronize_session=False)

        deleted_groups = 0
        groups = db.query(UserGroup).all()
        for g in groups:
            member_count = db.query(User).filter(User.group_id == g.id).count()
            if member_count == 0:
                db.delete(g)
                deleted_groups += 1
        deleted["user_groups"] = deleted_groups

        db.commit()
        return {"message": "数据清理完成（保留 admin）", "deleted": deleted, "admin_id": admin_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"清理失败: {str(e)}")

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

def _get_user_ids_by_identity(db: Session, identity_types: List[str], group_id: Optional[int] = None) -> List[int]:
    """按身份类型（CC/SS/LP）获取用户ID集合，可选限定组。
    - identity_types: 例如 ["CC"], ["SS"], ["LP"], ["CC","SS"]
    - group_id: 管理员/超管可选，限定在某个组内
    """
    if not identity_types:
        return []
    normalized = [t.upper() for t in identity_types]
    q = db.query(User.id).filter(func.upper(User.identity_type).in_(normalized))
    if group_id:
        q = q.filter(User.group_id == group_id)
    rows = q.all()
    return [row[0] if isinstance(row, tuple) else row.id for row in rows]

def _resolve_scope_and_identities(
    db: Session,
    current_user: User,
    role_scope: Optional[str],
    user_id: Optional[int],
    group_id: Optional[int]
) -> (str, Optional[List[str]]):
    """根据权限与输入参数，计算有效的视角(scope)与身份过滤集合(identity_types)。
    - 仅超级管理员可自由指定 role_scope；
    - 管理员/普通用户忽略 role_scope：
      * 若指定 user_id，则按该用户身份过滤；
      * 否则按当前登录用户身份过滤；
    返回：有效 scope 字符串，以及用于过滤的身份类型列表（None 表示不限身份）。
    """
    # 超级管理员：尊重传入 role_scope；默认 ALL
    if getattr(current_user, "is_super_admin", False):
        scope = (role_scope or "ALL").upper()
        if scope in ("CC", "SS"):
            return scope, [scope]
        if scope in ("CC_SS",):
            return scope, ["CC", "SS"]
        if scope == "LP":
            return scope, ["LP"]
        return "ALL", None

    # 非超管：忽略 role_scope，按用户身份确定
    target_identity = None
    if user_id:
        target = db.query(User).filter(User.id == user_id).first()
        target_identity = (getattr(target, "identity_type", "") or "").upper() if target else None
    if not target_identity:
        target_identity = (getattr(current_user, "identity_type", "") or "").upper()

    if target_identity in ("CC", "SS"):
        return target_identity, [target_identity]
    if target_identity == "LP":
        return "LP", ["LP"]

    # 身份未知时，保守地不做身份聚合（返回空集合以避免越权聚合）
    # 这里返回一个不会匹配任何身份的列表以确保结果为空，避免非超管看到跨身份数据。
    return "UNKNOWN", ["__NO_MATCH__"]

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

# ==================== 月度目标接口 ====================
@app.get("/api/v1/goals/monthly", response_model=List[MonthlyGoalResponse])
async def get_monthly_goals(
    identity_type: Optional[str] = Query(None, description="身份类型：CC/SS"),
    scope: Optional[str] = Query(None, description="目标作用域：global/group/user"),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    today = date.today()
    y = year or today.year
    m = month or today.month

    q = db.query(MonthlyGoal).filter(MonthlyGoal.year == y, MonthlyGoal.month == m)

    if identity_type:
        q = q.filter(func.upper(MonthlyGoal.identity_type) == identity_type.upper())
    if scope:
        q = q.filter(func.lower(MonthlyGoal.scope) == scope.lower())
    if group_id is not None:
        q = q.filter(MonthlyGoal.group_id == group_id)
    if user_id is not None:
        q = q.filter(MonthlyGoal.user_id == user_id)

    # 权限限制：普通用户仅能查看自己的 user 级别或所在组的 group 级别；global 仅管理员以上
    if not (current_user.is_admin or current_user.is_super_admin):
        # 明确禁止 global
        q = q.filter(MonthlyGoal.scope.in_(["group", "user"]))

        # 限制 group 范围
        if group_id is not None and current_user.group_id != group_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看其他组的目标")
        # 限制 user 范围
        if user_id is not None and current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看其他用户的目标")

        # 若未显式指定 scope/group/user，则默认返回本人 user 级目标
        if scope is None and user_id is None and group_id is None:
            q = q.filter(MonthlyGoal.scope == "user", MonthlyGoal.user_id == current_user.id)

    goals = q.order_by(MonthlyGoal.scope.desc()).all()
    return [MonthlyGoalResponse(
        id=g.id,
        identity_type=g.identity_type,
        scope=g.scope,
        year=g.year,
        month=g.month,
        group_id=g.group_id,
        user_id=g.user_id,
        amount_target=g.amount_target,
        new_sign_target_amount=g.new_sign_target_amount,
        referral_target_amount=g.referral_target_amount,
        renewal_total_target_amount=g.renewal_total_target_amount,
        renewal_target_count=g.renewal_target_count,
        upgrade_target_count=g.upgrade_target_count,
        notes=g.notes,
        created_at=g.created_at,
        updated_at=g.updated_at
    ) for g in goals]

@app.post("/api/v1/goals/monthly", response_model=MonthlyGoalResponse)
async def upsert_monthly_goal(
    payload: MonthlyGoalUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 仅管理员或超级管理员可设置目标
    if not (current_user.is_admin or current_user.is_super_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")

    identity_norm = (payload.identity_type or "").upper()
    scope_norm = (payload.scope or "").lower()
    if scope_norm not in ("global", "group", "user"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scope 取值必须为 global/group/user")
    if scope_norm == "group" and not payload.group_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="group 级目标必须提供 group_id")
    if scope_norm == "user" and not payload.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user 级目标必须提供 user_id")

    # 管理员权限限制：不可设置 global；仅能维护本组 group/user
    if current_user.is_admin and not current_user.is_super_admin:
        if scope_norm == "global":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员不可设置 global 目标")
        if payload.group_id is not None and payload.group_id != current_user.group_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员仅能维护本组目标")
        if payload.user_id is not None:
            target_user = db.query(User).filter(User.id == payload.user_id).first()
            if not target_user or target_user.group_id != current_user.group_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员仅能维护本组用户目标")

    y = int(payload.year)
    m = int(payload.month)

    q = db.query(MonthlyGoal).filter(
        func.upper(MonthlyGoal.identity_type) == identity_norm,
        func.lower(MonthlyGoal.scope) == scope_norm,
        MonthlyGoal.year == y,
        MonthlyGoal.month == m
    )
    if payload.group_id:
        q = q.filter(MonthlyGoal.group_id == payload.group_id)
    if payload.user_id:
        q = q.filter(MonthlyGoal.user_id == payload.user_id)

    existing = q.first()
    if existing:
        existing.amount_target = float(payload.amount_target or 0.0)
        # 新增细分目标字段更新
        try:
            existing.new_sign_target_amount = float(getattr(payload, "new_sign_target_amount", 0.0) or 0.0)
            existing.referral_target_amount = float(getattr(payload, "referral_target_amount", 0.0) or 0.0)
            existing.renewal_total_target_amount = float(getattr(payload, "renewal_total_target_amount", 0.0) or 0.0)
        except Exception:
            # 兼容早期请求未携带字段
            existing.new_sign_target_amount = existing.new_sign_target_amount or 0.0
            existing.referral_target_amount = existing.referral_target_amount or 0.0
            existing.renewal_total_target_amount = existing.renewal_total_target_amount or 0.0
        existing.renewal_target_count = int(payload.renewal_target_count or 0)
        existing.upgrade_target_count = int(payload.upgrade_target_count or 0)
        existing.notes = payload.notes
        db.add(existing)
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        target = MonthlyGoal(
            identity_type=identity_norm,
            scope=scope_norm,
            year=y,
            month=m,
            group_id=payload.group_id,
            user_id=payload.user_id,
            amount_target=float(payload.amount_target or 0.0),
            new_sign_target_amount=float(getattr(payload, "new_sign_target_amount", 0.0) or 0.0),
            referral_target_amount=float(getattr(payload, "referral_target_amount", 0.0) or 0.0),
            renewal_total_target_amount=float(getattr(payload, "renewal_total_target_amount", 0.0) or 0.0),
            renewal_target_count=int(payload.renewal_target_count or 0),
            upgrade_target_count=int(payload.upgrade_target_count or 0),
            notes=payload.notes
        )
        db.add(target)
        db.commit()
        db.refresh(target)

    return MonthlyGoalResponse(
        id=target.id,
        identity_type=target.identity_type,
        scope=target.scope,
        year=target.year,
        month=target.month,
        group_id=target.group_id,
        user_id=target.user_id,
        amount_target=target.amount_target,
        new_sign_target_amount=target.new_sign_target_amount,
        referral_target_amount=target.referral_target_amount,
        renewal_total_target_amount=target.renewal_total_target_amount,
        renewal_target_count=target.renewal_target_count,
        upgrade_target_count=target.upgrade_target_count,
        notes=target.notes,
        created_at=target.created_at,
        updated_at=target.updated_at
    )

# 别名路由：符合规划 /api/v1/analytics/goals/monthly
@app.get("/api/v1/analytics/goals/monthly", response_model=List[MonthlyGoalResponse])
async def analytics_get_monthly_goals(
    identity_type: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    today = date.today()
    y = year or today.year
    m = month or today.month

    q = db.query(MonthlyGoal).filter(MonthlyGoal.year == y, MonthlyGoal.month == m)

    if identity_type:
        q = q.filter(func.upper(MonthlyGoal.identity_type) == identity_type.upper())
    if scope:
        q = q.filter(func.lower(MonthlyGoal.scope) == scope.lower())
    if group_id is not None:
        q = q.filter(MonthlyGoal.group_id == group_id)
    if user_id is not None:
        q = q.filter(MonthlyGoal.user_id == user_id)

    if not (current_user.is_admin or current_user.is_super_admin):
        q = q.filter(MonthlyGoal.scope.in_(["group", "user"]))
        if group_id is not None and current_user.group_id != group_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看其他组的目标")
        if user_id is not None and current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看其他用户的目标")
        if scope is None and user_id is None and group_id is None:
            q = q.filter(MonthlyGoal.scope == "user", MonthlyGoal.user_id == current_user.id)
    elif current_user.is_admin and not current_user.is_super_admin:
        # 管理员可查本组 group/user，禁止 global
        q = q.filter(MonthlyGoal.scope.in_(["group", "user"]))
        admin_gid = current_user.group_id
        if group_id is None and user_id is None:
            q = q.filter(MonthlyGoal.group_id == admin_gid)
        if group_id is not None and group_id != admin_gid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员不可跨组查看目标")
        if user_id is not None:
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user or target_user.group_id != admin_gid:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员仅能查看本组用户目标")

    goals = q.order_by(MonthlyGoal.scope.desc()).all()
    return [MonthlyGoalResponse(
        id=g.id,
        identity_type=g.identity_type,
        scope=g.scope,
        year=g.year,
        month=g.month,
        group_id=g.group_id,
        user_id=g.user_id,
        amount_target=g.amount_target,
        new_sign_target_amount=g.new_sign_target_amount,
        referral_target_amount=g.referral_target_amount,
        renewal_total_target_amount=g.renewal_total_target_amount,
        renewal_target_count=g.renewal_target_count,
        upgrade_target_count=g.upgrade_target_count,
        notes=g.notes,
        created_at=g.created_at,
        updated_at=g.updated_at
    ) for g in goals]

@app.put("/api/v1/analytics/goals/monthly", response_model=MonthlyGoalResponse)
async def analytics_upsert_monthly_goal(
    payload: MonthlyGoalUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await upsert_monthly_goal(payload, db, current_user)

# ==================== 新增：Summary 聚合（含月度目标对齐） ====================
@app.get("/api/v1/analytics/summary")
async def analytics_summary(
    identity_type: str = Query(..., description="身份类型：CC/SS"),
    scope: Optional[str] = Query(None, description="目标作用域：global/group/user（用于提示）"),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    import calendar
    today = date.today()
    y = year or today.year
    m = month or today.month
    month_start = date(y, m, 1)
    last_day = calendar.monthrange(y, m)[1]
    month_end = date(y, m, last_day)

    # 可见范围：管理员仅本组；普通用户仅自己；超管任意
    reports_month_q = _visible_reports_query(db, current_user, month_start, month_end, group_id)
    reports_today_q = _visible_reports_query(db, current_user, today, today, group_id)

    # 身份过滤
    identity_norm = identity_type.upper()
    uid_pool = _get_user_ids_by_identity(db, [identity_norm], group_id)
    if uid_pool:
        reports_month_q = reports_month_q.filter(DailyReport.user_id.in_(uid_pool))
        reports_today_q = reports_today_q.filter(DailyReport.user_id.in_(uid_pool))

    if user_id:
        reports_month_q = reports_month_q.filter(DailyReport.user_id == user_id)
        reports_today_q = reports_today_q.filter(DailyReport.user_id == user_id)

    month_reports = reports_month_q.all()
    today_reports = reports_today_q.all()

    def _sum_int(reports, attr: str) -> int:
        return int(sum((getattr(r, attr, 0) or 0) for r in reports))
    def _sum_float(reports, attr: str) -> float:
        return float(sum((getattr(r, attr, 0.0) or 0.0) for r in reports))

    # CC 指标
    cc_month = {
        "new_sign_count": _sum_int(month_reports, "new_sign_count"),
        "new_sign_amount": round(_sum_float(month_reports, "new_sign_amount"), 2),
        "referral_count": _sum_int(month_reports, "referral_count"),
        "referral_amount": round(_sum_float(month_reports, "referral_amount"), 2)
    }
    cc_today = {
        "new_sign_count": _sum_int(today_reports, "new_sign_count"),
        "new_sign_amount": round(_sum_float(today_reports, "new_sign_amount"), 2),
        "referral_count": _sum_int(today_reports, "referral_count"),
        "referral_amount": round(_sum_float(today_reports, "referral_amount"), 2)
    }
    cc_month["actual_amount"] = round(cc_month["new_sign_amount"] + cc_month["referral_amount"], 2)
    cc_today["actual_amount"] = round(cc_today["new_sign_amount"] + cc_today["referral_amount"], 2)

    # SS 指标
    ss_month = {
        "renewal_count": _sum_int(month_reports, "renewal_count"),
        "renewal_amount": round(_sum_float(month_reports, "renewal_amount"), 2),
        "upgrade_count": _sum_int(month_reports, "upgrade_count"),
        "upgrade_amount": round(_sum_float(month_reports, "upgrade_amount"), 2)
    }
    ss_today = {
        "renewal_count": _sum_int(today_reports, "renewal_count"),
        "renewal_amount": round(_sum_float(today_reports, "renewal_amount"), 2),
        "upgrade_count": _sum_int(today_reports, "upgrade_count"),
        "upgrade_amount": round(_sum_float(today_reports, "upgrade_amount"), 2)
    }
    ss_month["actual_amount"] = round(ss_month["renewal_amount"] + ss_month["upgrade_amount"], 2)
    ss_today["actual_amount"] = round(ss_today["renewal_amount"] + ss_today["upgrade_amount"], 2)

    # 选择目标（user > group > global）
    monthly_goal = None
    if identity_norm in ("CC", "SS"):
        if user_id:
            monthly_goal = db.query(MonthlyGoal).filter(
                func.upper(MonthlyGoal.identity_type) == identity_norm,
                MonthlyGoal.scope == "user",
                MonthlyGoal.user_id == user_id,
                MonthlyGoal.year == y,
                MonthlyGoal.month == m
            ).first()
        if not monthly_goal and group_id:
            monthly_goal = db.query(MonthlyGoal).filter(
                func.upper(MonthlyGoal.identity_type) == identity_norm,
                MonthlyGoal.scope == "group",
                MonthlyGoal.group_id == group_id,
                MonthlyGoal.year == y,
                MonthlyGoal.month == m
            ).first()
        if not monthly_goal:
            monthly_goal = db.query(MonthlyGoal).filter(
                func.upper(MonthlyGoal.identity_type) == identity_norm,
                MonthlyGoal.scope == "global",
                MonthlyGoal.year == y,
                MonthlyGoal.month == m
            ).first()

    goal_payload = None
    amount_rate = None
    renewal_rate = None
    upgrade_rate = None
    # 新增细分成就率：CC的新单与转介绍、SS的总续费
    new_sign_achievement_rate = None
    referral_achievement_rate = None
    total_renewal_achievement_rate = None
    progress_display = {
        "amount_rate": "—",
        "renewal_rate": "—",
        "upgrade_rate": "—",
        "new_sign_achievement_rate": "—",
        "referral_achievement_rate": "—",
        "total_renewal_achievement_rate": "—",
    }
    goal_status = None
    if monthly_goal:
        goal_payload = {
            "identity_type": monthly_goal.identity_type,
            "scope": monthly_goal.scope,
            "year": monthly_goal.year,
            "month": monthly_goal.month,
            "amount_target": monthly_goal.amount_target,
            # 为前端计算新增达成率提供目标字段
            "new_sign_target_amount": getattr(monthly_goal, "new_sign_target_amount", 0.0),
            "referral_target_amount": getattr(monthly_goal, "referral_target_amount", 0.0),
            "renewal_total_target_amount": getattr(monthly_goal, "renewal_total_target_amount", 0.0),
            "renewal_target_count": monthly_goal.renewal_target_count,
            "upgrade_target_count": monthly_goal.upgrade_target_count,
        }
        # 金额目标达成率
        actual_amount = cc_month["actual_amount"] if identity_norm == "CC" else ss_month["actual_amount"]
        if (monthly_goal.amount_target or 0) > 0:
            amount_rate = round((actual_amount / monthly_goal.amount_target) * 100.0, 2)
            progress_display["amount_rate"] = f"{amount_rate}%"
        else:
            goal_status = "未设目标"
        # 身份细分目标达成率
        if identity_norm == "CC":
            # 新单目标达成率
            if (monthly_goal.new_sign_target_amount or 0) > 0:
                try:
                    new_sign_achievement_rate = round((cc_month["new_sign_amount"] / monthly_goal.new_sign_target_amount) * 100.0, 2)
                    progress_display["new_sign_achievement_rate"] = f"{new_sign_achievement_rate}%"
                except Exception:
                    new_sign_achievement_rate = None
            # 转介绍目标达成率
            if (monthly_goal.referral_target_amount or 0) > 0:
                try:
                    referral_achievement_rate = round((cc_month["referral_amount"] / monthly_goal.referral_target_amount) * 100.0, 2)
                    progress_display["referral_achievement_rate"] = f"{referral_achievement_rate}%"
                except Exception:
                    referral_achievement_rate = None
        # SS 人数与总续费目标
        if identity_norm == "SS":
            if (monthly_goal.renewal_target_count or 0) > 0:
                renewal_rate = round((ss_month["renewal_count"] / monthly_goal.renewal_target_count) * 100.0, 2)
                progress_display["renewal_rate"] = f"{renewal_rate}%"
            if (monthly_goal.upgrade_target_count or 0) > 0:
                upgrade_rate = round((ss_month["upgrade_count"] / monthly_goal.upgrade_target_count) * 100.0, 2)
                progress_display["upgrade_rate"] = f"{upgrade_rate}%"
            # 总续费（续费+升舱）目标达成率
            total_actual_renewal = (ss_month.get("renewal_amount", 0.0) or 0.0) + (ss_month.get("upgrade_amount", 0.0) or 0.0)
            if (monthly_goal.renewal_total_target_amount or 0) > 0:
                try:
                    total_renewal_achievement_rate = round((total_actual_renewal / monthly_goal.renewal_total_target_amount) * 100.0, 2)
                    progress_display["total_renewal_achievement_rate"] = f"{total_renewal_achievement_rate}%"
                except Exception:
                    total_renewal_achievement_rate = None
    else:
        goal_status = "未设目标"

    # 根据身份返回对应结构
    if identity_norm == "CC":
        return {
            "period": {"year": y, "month": m, "today": today.isoformat()},
            "identity_type": "CC",
            "goal": goal_payload,
            "goal_status": goal_status,
            "today": cc_today,
            "month": cc_month,
            "progress": {
                "amount_rate": amount_rate,
                "new_sign_achievement_rate": new_sign_achievement_rate,
                "referral_achievement_rate": referral_achievement_rate,
            },
            "progress_display": {
                "amount_rate": progress_display["amount_rate"],
                "new_sign_achievement_rate": progress_display["new_sign_achievement_rate"],
                "referral_achievement_rate": progress_display["referral_achievement_rate"],
            },
            "meta": {"group_id": group_id, "user_id": user_id}
        }
    else:
        return {
            "period": {"year": y, "month": m, "today": today.isoformat()},
            "identity_type": "SS",
            "goal": goal_payload,
            "goal_status": goal_status,
            "today": ss_today,
            "month": ss_month,
            "progress": {
                "amount_rate": amount_rate,
                "renewal_rate": renewal_rate,
                "upgrade_rate": upgrade_rate,
                "total_renewal_achievement_rate": total_renewal_achievement_rate,
            },
            "progress_display": progress_display,
            "meta": {"group_id": group_id, "user_id": user_id}
        }

# ==================== 新增：Trend 时间序列（日报聚合） ====================
@app.get("/api/v1/analytics/trend")
async def analytics_trend(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    identity_type: Optional[str] = Query(None, description="身份类型：CC/SS，可选"),
    metrics: Optional[List[str]] = Query(None, description="指标列表：new_sign_count/new_sign_amount/referral_count/referral_amount/renewal_count/renewal_amount/upgrade_count/upgrade_amount"),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    s, e = _parse_date_range(start_date, end_date)
    reports_q = _visible_reports_query(db, current_user, s, e, group_id)

    # 身份过滤（如提供）
    ids = None
    if identity_type:
        ids = _get_user_ids_by_identity(db, [identity_type.upper()], group_id)
        if ids:
            reports_q = reports_q.filter(DailyReport.user_id.in_(ids))
    if user_id:
        reports_q = reports_q.filter(DailyReport.user_id == user_id)

    reports = reports_q.order_by(DailyReport.work_date.asc()).all()
    default_metrics = [
        "new_sign_count","new_sign_amount",
        "referral_count","referral_amount",
        "renewal_count","renewal_amount",
        "upgrade_count","upgrade_amount"
    ]
    metrics = metrics or default_metrics

    agg: Dict[str, Dict[str, Any]] = {}
    for r in reports:
        dstr = r.work_date.isoformat() if r.work_date else None
        if not dstr:
            continue
        bucket = agg.setdefault(dstr, {k: 0 for k in metrics})
        for k in metrics:
            val = getattr(r, k, 0)
            bucket[k] += val or 0

    series = []
    for dstr in sorted(agg.keys()):
        entry = {"date": dstr}
        for k in metrics:
            v = agg[dstr][k]
            # 金额类保留两位
            if k.endswith("_amount"):
                entry[k] = round(float(v), 2)
            else:
                entry[k] = int(v)
        series.append(entry)

    return {
        "period": {"start": s.isoformat(), "end": e.isoformat()},
        "identity_type": identity_type,
        "metrics": metrics,
        "series": series,
        "meta": {"group_id": group_id, "user_id": user_id, "days": len(series)}
    }
# =============== 新增：统一 Analytics 数据接口（含角色视角） ===============
@app.get("/api/v1/analytics/data")
async def analytics_data(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    role_scope: Optional[str] = Query(None, description="视角：CC / SS / LP / ALL（兼容 CC_SS）"),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """返回前端聚合指标与兼容旧版统计卡。
    - role_scope: CC_SS / LP / ALL
    - group_id: 管理员/超管可选，限定组范围
    """
    s, e = _parse_date_range(start_date, end_date)
    tasks_q = _visible_tasks_query(db, current_user, s, e, group_id)
    reports_q = _visible_reports_query(db, current_user, s, e, group_id)

    # 根据视角与权限确定数据集（个人 vs 团队/全体）
    # 普通用户默认仅个人数据；管理员/超管按 group_id 或全体可见范围
    def _personal_task_query(q: Any) -> Any:
        return q.filter(or_(Task.assigned_to == current_user.id, Task.created_by == current_user.id))

    def _personal_report_query(q: Any) -> Any:
        return q.filter(DailyReport.user_id == current_user.id)

    scope, identity_types = _resolve_scope_and_identities(db, current_user, role_scope, user_id, group_id)

    # 个人视角仅在非管理员且未指定 group_id 时应用
    if not (getattr(current_user, "is_admin", False) or getattr(current_user, "is_super_admin", False)) and not group_id:
        tasks_q_scoped = _personal_task_query(tasks_q)
        reports_q_scoped = _personal_report_query(reports_q)
    else:
        tasks_q_scoped = tasks_q
        reports_q_scoped = reports_q

    # 身份过滤（CC/SS/LP）与单用户过滤
    if identity_types:
        # 对非超管，忽略 group_id 限制；管理员可按组限制
        ids = _get_user_ids_by_identity(db, identity_types, group_id if (getattr(current_user, "is_admin", False) or getattr(current_user, "is_super_admin", False)) else None)
        if ids:
            tasks_q_scoped = tasks_q_scoped.filter(or_(Task.assigned_to.in_(ids), Task.created_by.in_(ids)))
            reports_q_scoped = reports_q_scoped.filter(DailyReport.user_id.in_(ids))
        else:
            # 无匹配用户时，直接返回空数据集
            tasks_q_scoped = tasks_q_scoped.filter(Task.id == -1)
            reports_q_scoped = reports_q_scoped.filter(DailyReport.id == -1)

    if user_id:
        tasks_q_scoped = tasks_q_scoped.filter(or_(Task.assigned_to == user_id, Task.created_by == user_id))
        reports_q_scoped = reports_q_scoped.filter(DailyReport.user_id == user_id)

    tasks = tasks_q_scoped.all()
    reports = reports_q_scoped.all()

    # 通用统计卡（兼容旧接口）
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if (t.status == TaskStatus.DONE or (isinstance(t.status, str) and t.status == "done")))
    completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks else 0, 1)
    total_reports = len(reports)
    avg_emotion = round((sum((r.mood_score or 0) for r in reports) / total_reports) if total_reports else 0, 2)

    # 期间天数与提交天数
    total_days = (e - s).days + 1
    submitted_days = len({r.work_date for r in reports}) if reports else 0
    report_submission_rate = round((submitted_days / total_days * 100) if total_days else 0, 1)

    # 指标计算工具
    amount_tasks = [t for t in tasks if (getattr(t.task_type, 'value', str(t.task_type)) == 'amount')]
    quantity_tasks = [t for t in tasks if (getattr(t.task_type, 'value', str(t.task_type)) == 'quantity')]
    checkbox_tasks = [t for t in tasks if (getattr(t.task_type, 'value', str(t.task_type)) == 'checkbox')]

    sales_target = float(sum(t.target_amount or 0 for t in amount_tasks))
    # 使用日报的实际业务数据作为实际业绩
    sales_actual = float(sum(getattr(r, 'new_sign_amount', 0.0) or 0.0 for r in reports))
    sales_ach_rate = round((sales_actual / sales_target * 100) if sales_target else 0, 2)
    deal_count = int(sum(getattr(r, 'new_sign_count', 0) or 0 for r in reports))
    renewal_count_total = int(sum(getattr(r, 'renewal_count', 0) or 0 for r in reports))
    upgrade_count_total = int(sum(getattr(r, 'upgrade_count', 0) or 0 for r in reports))

    call_count_total = int(sum(getattr(r, 'call_count', 0) or 0 for r in reports))
    call_duration_total = float(sum(getattr(r, 'call_duration', 0.0) or 0.0 for r in reports))
    followup_feedback = sum(1 for r in reports if (getattr(r, 'task_progress', None) or getattr(r, 'work_summary', None)))

    # LP 视角相关（用现有字段近似）
    satisfaction_avg = round((sum((getattr(r, 'mood_score', 0) or 0) for r in reports) / total_reports) if total_reports else 0, 2)
    lp_service_coverage = report_submission_rate

    # ALL 视角相关
    # AI 使用统计
    start_dt = datetime.combine(s, datetime.min.time())
    end_dt = datetime.combine(e, datetime.max.time())
    ai_total_calls = db.query(AICallLog).filter(AICallLog.created_at >= start_dt, AICallLog.created_at <= end_dt).count()

    metrics_payload: Dict[str, Any] = {}
    if scope in ("CC", "SS", "CC_SS"):
        metrics_payload = {
            "task_completion_rate": completion_rate,
            "sales_target": round(sales_target, 2),
            "sales_actual": round(sales_actual, 2),
            "sales_achievement_rate": sales_ach_rate,
            "touch_count": call_count_total,
            "touch_coverage": report_submission_rate,
            "referral_count": 0,  # 数据暂缺
            "report_submission_rate": report_submission_rate,
            "call_count": call_count_total,
            "call_duration": round(call_duration_total, 1),
            "deal_count": deal_count,
            "followup_feedback": followup_feedback,
            # 新增业务指标
            "renewal_count": renewal_count_total,
            "upgrade_count": upgrade_count_total,
        }
    elif scope == "LP":
        metrics_payload = {
            "service_count": call_count_total,
            "service_touch_rate": report_submission_rate,
            "satisfaction_score": satisfaction_avg,  # 以 mood_score 近似
            "iur_completion_rate": None,  # 数据暂缺
            "complaint_count": None,      # 数据暂缺
            "followup_quality": None,     # 数据暂缺
        }
    else:  # ALL 或非识别/未知（统一走汇总视角，以当前可见范围为准）
        # 汇总视角采用全局/当前权限可见汇总数据
        total_sales_all = sales_actual
        avg_task_completion = completion_rate
        overall_satisfaction = round(avg_emotion / 10.0, 2)  # 0-1 区间（近似）
        metrics_payload = {
            "total_sales_all": round(total_sales_all, 2),
            "avg_sales_achievement": sales_ach_rate,
            "avg_task_completion": avg_task_completion,
            # 统一前端键名别名：与 CC/SS 视角保持一致
            "task_completion_rate": avg_task_completion,
            "customer_growth_rate": None,  # 暂缺
            "lp_service_coverage": lp_service_coverage,
            # 统一前端键名别名：报告提交率
            "report_submission_rate": lp_service_coverage,
            "renewal_rate_total": None,    # 暂缺
            "referral_growth": None,       # 暂缺
            "overall_satisfaction": overall_satisfaction,
            "team_gap_rate": None,         # 暂缺
            "ai_usage_total": ai_total_calls,
            # 新增业务指标
            "renewal_count_total": renewal_count_total,
            "upgrade_count_total": upgrade_count_total,
        }

    return {
        "metrics": metrics_payload,
        "stats": {
            "totalTasks": total_tasks,
            "completedTasks": completed_tasks,
            "completionRate": completion_rate,
            "totalReports": total_reports,
            "avgEmotionScore": avg_emotion,
        }
    }

# 兼容前端旧路径（无版本前缀）
@app.get("/analytics/data")
async def analytics_data_alias(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    role_scope: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_data(start_date, end_date, role_scope, group_id, user_id, db, current_user)

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
    role_scope: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """图表数据：任务趋势、状态分布、优先级、情绪趋势、AI使用"""
    s, e = _parse_date_range(start_date, end_date)
    tasks_q = _visible_tasks_query(db, current_user, s, e, group_id)
    reports_q = _visible_reports_query(db, current_user, s, e, group_id)
    # 身份与单用户过滤（仅超管可指定 role_scope）
    scope, identity_types = _resolve_scope_and_identities(db, current_user, role_scope, user_id, group_id)

    if identity_types:
        ids = _get_user_ids_by_identity(db, identity_types, group_id if (getattr(current_user, "is_admin", False) or getattr(current_user, "is_super_admin", False)) else None)
        if ids:
            tasks_q = tasks_q.filter(or_(Task.assigned_to.in_(ids), Task.created_by.in_(ids)))
            reports_q = reports_q.filter(DailyReport.user_id.in_(ids))
        else:
            tasks_q = tasks_q.filter(Task.id == -1)
            reports_q = reports_q.filter(DailyReport.id == -1)

    if user_id:
        tasks_q = tasks_q.filter(or_(Task.assigned_to == user_id, Task.created_by == user_id))
        reports_q = reports_q.filter(DailyReport.user_id == user_id)
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
    role_scope: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_charts(start_date, end_date, role_scope, group_id, user_id, db, current_user)

@app.get("/api/v1/analytics/user-performance")
async def analytics_user_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    role_scope: Optional[str] = Query(None),
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
        base_q = db.query(User).filter(User.id.in_(user_ids)) if user_ids else db.query(User).filter(User.id == -1)
    else:
        base_q = db.query(User) if current_user.is_super_admin else db.query(User).filter(User.group_id == current_user.group_id)

    # 按视角身份过滤：仅超管可自由选择；管理员固定为自身身份
    if current_user.is_super_admin:
        scope = (role_scope or "ALL").upper()
        if scope in ("CC", "SS"):
            identity_types = [scope]
        elif scope == "CC_SS":
            identity_types = ["CC", "SS"]
        elif scope == "LP":
            identity_types = ["LP"]
        else:
            identity_types = None
    else:
        idt = (getattr(current_user, "identity_type", "") or "").upper()
        identity_types = [idt] if idt in ("CC", "SS", "LP") else ["__NO_MATCH__"]

    if identity_types:
        base_q = base_q.filter(func.upper(User.identity_type).in_([t.upper() for t in identity_types]))

    users = base_q.all()
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
    role_scope: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_user_performance(start_date, end_date, role_scope, group_id, db, current_user)

@app.get("/api/v1/analytics/ranking")
async def analytics_ranking(
    metric_key: Optional[str] = Query(None, description="排名指标键"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    role_scope: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if not metric_key:
        return {"top_10": [], "current_user_rank": None}

    s, e = _parse_date_range(start_date, end_date)
    tasks_q = _visible_tasks_query(db, current_user, s, e, group_id)
    reports_q = _visible_reports_query(db, current_user, s, e, group_id)

    scope, identity_types = _resolve_scope_and_identities(db, current_user, role_scope, user_id, group_id)

    # 针对不同指标限定适用的身份类型，避免与指标不关联的用户出现在榜单
    metric_identity_map = {
        # 通用（所有身份）：任务完成率、日报提交率
        "task_completion_rate": None,
        "report_submission_rate": None,
        # 销售总额：CC+SS 都参与
        "period_sales_amount": ["CC", "SS"],
        # 仅 CC 相关的指标
        "period_new_sign_amount": ["CC"],
        "new_sign_count": ["CC"],
        "period_referral_amount": ["CC"],
        "referral_count": ["CC"],
        "sales_achievement_rate": ["CC"],
        "new_sign_achievement_rate": ["CC"],
        "referral_achievement_rate": ["CC"],
        # 仅 SS 相关的指标
        "period_total_renewal_amount": ["SS"],
        "period_upgrade_amount": ["SS"],
        "upgrade_count": ["SS"],
        "total_renewal_achievement_rate": ["SS"],
        "upgrade_rate": ["SS"],
    }
    supported_identities = metric_identity_map.get(metric_key)
    if supported_identities is not None:
        # 若上游未限定身份（ALL 场景），则以指标适配身份为准；否则取交集
        if identity_types is None:
            identity_types = supported_identities
        else:
            identity_types = [t for t in identity_types if t.upper() in {s.upper() for s in supported_identities}]

    def _users_for_ranking() -> List[User]:
        base_q = db.query(User)
        if current_user.is_super_admin:
            if group_id:
                base_q = base_q.filter(User.group_id == group_id)
        elif current_user.is_admin:
            grp = group_id or current_user.group_id
            if grp:
                base_q = base_q.filter(User.group_id == grp)
        else:
            base_q = base_q.filter(User.id == current_user.id)

        if identity_types:
            base_q = base_q.filter(func.upper(User.identity_type).in_([t.upper() for t in identity_types]))
        if user_id:
            base_q = base_q.filter(User.id == user_id)
        return base_q.all()

    users = _users_for_ranking()

    # 单用户指标计算
    def _metric_for_user(u: User) -> (float, Optional[str]):
        uq = tasks_q.filter(or_(Task.assigned_to == u.id, Task.created_by == u.id))
        rq = reports_q.filter(DailyReport.user_id == u.id)
        # 目标按“月度目标”获取：优先个人，其次组，最后全局
        def _get_user_monthly_goal(identity: str, y: int, m: int) -> Optional[MonthlyGoal]:
            identity_norm = (identity or "").upper()
            # personal
            g = db.query(MonthlyGoal).filter(
                func.upper(MonthlyGoal.identity_type) == identity_norm,
                MonthlyGoal.scope == "user",
                MonthlyGoal.user_id == u.id,
                MonthlyGoal.year == y,
                MonthlyGoal.month == m
            ).first()
            if g:
                return g
            # group
            if getattr(u, "group_id", None):
                g = db.query(MonthlyGoal).filter(
                    func.upper(MonthlyGoal.identity_type) == identity_norm,
                    MonthlyGoal.scope == "group",
                    MonthlyGoal.group_id == u.group_id,
                    MonthlyGoal.year == y,
                    MonthlyGoal.month == m
                ).first()
                if g:
                    return g
            # global
            g = db.query(MonthlyGoal).filter(
                func.upper(MonthlyGoal.identity_type) == identity_norm,
                MonthlyGoal.scope == "global",
                MonthlyGoal.year == y,
                MonthlyGoal.month == m
            ).first()
            return g

        y, m = e.year, e.month

        if metric_key == "task_completion_rate":
            total_tasks = uq.count()
            completed_tasks = uq.filter(
                or_(Task.status == TaskStatus.DONE, (isinstance(Task.status, str) and Task.status == "done"))
            ).count()
            val = (completed_tasks / total_tasks * 100.0) if total_tasks else 0.0
            return round(val, 1), f"{round(val, 1)}%"

        if metric_key == "report_submission_rate":
            total_days = (e - s).days + 1
            submitted_days = rq.with_entities(DailyReport.work_date).distinct().count()
            val = (submitted_days / total_days * 100.0) if total_days else 0.0
            return round(val, 1), f"{round(val, 1)}%"

        if metric_key == "sales_achievement_rate":
            # 目标取金额型任务的目标之和
            amount_tasks = uq.filter(or_(Task.task_type == TaskType.amount, (isinstance(Task.task_type, str) and Task.task_type == "amount")))
            target_sum = sum((t.target_amount or 0.0) for t in amount_tasks.all())
            # 实际取日报中的新单金额
            sales_actual = float(rq.with_entities(func.sum(DailyReport.new_sign_amount)).scalar() or 0.0)
            if target_sum <= 0:
                return None, None  # 无目标则视为不参与该指标排名
            val = (sales_actual / target_sum * 100.0)
            return round(val, 2), f"{round(val, 2)}%"

        # 期间金额聚合（ALL 视角近似：新单+转介绍+续费+升舱）
        if metric_key == "period_sales_amount":
            new_sign = float(rq.with_entities(func.sum(DailyReport.new_sign_amount)).scalar() or 0.0)
            referral = float(rq.with_entities(func.sum(DailyReport.referral_amount)).scalar() or 0.0)
            renewal = float(rq.with_entities(func.sum(DailyReport.renewal_amount)).scalar() or 0.0)
            upgrade = float(rq.with_entities(func.sum(DailyReport.upgrade_amount)).scalar() or 0.0)
            val = new_sign + referral + renewal + upgrade
            return round(val, 2), None

        if metric_key == "period_new_sign_amount":
            val = float(rq.with_entities(func.sum(DailyReport.new_sign_amount)).scalar() or 0.0)
            return round(val, 2), None

        if metric_key == "new_sign_count":
            val = int(rq.with_entities(func.sum(DailyReport.new_sign_count)).scalar() or 0)
            return val, None

        if metric_key == "period_referral_amount":
            val = float(rq.with_entities(func.sum(DailyReport.referral_amount)).scalar() or 0.0)
            return round(val, 2), None

        if metric_key == "referral_count":
            val = int(rq.with_entities(func.sum(DailyReport.referral_count)).scalar() or 0)
            return val, None

        if metric_key == "period_total_renewal_amount":
            renewal = float(rq.with_entities(func.sum(DailyReport.renewal_amount)).scalar() or 0.0)
            upgrade = float(rq.with_entities(func.sum(DailyReport.upgrade_amount)).scalar() or 0.0)
            val = renewal + upgrade
            return round(val, 2), None

        if metric_key == "period_upgrade_amount":
            val = float(rq.with_entities(func.sum(DailyReport.upgrade_amount)).scalar() or 0.0)
            return round(val, 2), None

        if metric_key == "upgrade_count":
            val = int(rq.with_entities(func.sum(DailyReport.upgrade_count)).scalar() or 0)
            return val, None

        # 目标达成类（仅在存在目标时参与排名）
        if metric_key == "new_sign_achievement_rate":
            goal = _get_user_monthly_goal("CC", y, m)
            target = float(getattr(goal, "new_sign_target_amount", 0.0) or 0.0)
            if target <= 0:
                return None, None
            actual = float(rq.with_entities(func.sum(DailyReport.new_sign_amount)).scalar() or 0.0)
            val = (actual / target * 100.0)
            return round(val, 2), f"{round(val, 2)}%"

        if metric_key == "referral_achievement_rate":
            goal = _get_user_monthly_goal("CC", y, m)
            target = float(getattr(goal, "referral_target_amount", 0.0) or 0.0)
            if target <= 0:
                return None, None
            actual = float(rq.with_entities(func.sum(DailyReport.referral_amount)).scalar() or 0.0)
            val = (actual / target * 100.0)
            return round(val, 2), f"{round(val, 2)}%"

        if metric_key == "total_renewal_achievement_rate":
            goal = _get_user_monthly_goal("SS", y, m)
            target = float(getattr(goal, "renewal_total_target_amount", 0.0) or 0.0)
            if target <= 0:
                return None, None
            renewal = float(rq.with_entities(func.sum(DailyReport.renewal_amount)).scalar() or 0.0)
            upgrade = float(rq.with_entities(func.sum(DailyReport.upgrade_amount)).scalar() or 0.0)
            actual = renewal + upgrade
            val = (actual / target * 100.0)
            return round(val, 2), f"{round(val, 2)}%"

        if metric_key == "upgrade_rate":
            goal = _get_user_monthly_goal("SS", y, m)
            target_cnt = int(getattr(goal, "upgrade_target_count", 0) or 0)
            if target_cnt <= 0:
                return None, None
            up_cnt = int(rq.with_entities(func.sum(DailyReport.upgrade_count)).scalar() or 0)
            val = (up_cnt / target_cnt * 100.0)
            return round(val, 2), f"{round(val, 2)}%"

        # 未识别指标时返回 0
        return 0.0, None

    rows = []
    for u in users:
        value, formatted = _metric_for_user(u)
        # 目标型指标在无目标时返回 None，直接跳过该用户
        if value is None:
            continue
        rows.append({
            "user_id": u.id,
            "name": u.username,
            "avatar": None,
            "value": value,
            "formatted_value": formatted,
        })

    # 排序与排名
    rows.sort(key=lambda x: (x["value"] if isinstance(x["value"], (int, float)) else -1), reverse=True)
    for idx, r in enumerate(rows, start=1):
        r["rank"] = idx

    top_10 = rows[:10]
    current_user_rank = next((r for r in rows if r.get("user_id") == current_user.id), None)

    return {"top_10": top_10, "current_user_rank": current_user_rank}

# 兼容前端旧路径（无版本前缀）
@app.get("/analytics/ranking")
async def analytics_ranking_alias(
    metric_key: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    role_scope: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_ranking(metric_key, start_date, end_date, role_scope, group_id, user_id, db, current_user)

@app.get("/api/v1/analytics/ai-insights")
async def analytics_ai_insights(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    role_scope: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """AI洞察：基于权限与筛选的数据集进行分析，并结果留存与复用"""
    s, e = _parse_date_range(start_date, end_date)
    tasks_q = _visible_tasks_query(db, current_user, s, e, group_id)
    reports_q = _visible_reports_query(db, current_user, s, e, group_id)

    # 身份与单用户过滤（仅超管可指定 role_scope）
    scope, identity_types = _resolve_scope_and_identities(db, current_user, role_scope, user_id, group_id)

    if identity_types:
        ids = _get_user_ids_by_identity(db, identity_types, group_id if (getattr(current_user, "is_admin", False) or getattr(current_user, "is_super_admin", False)) else None)
        if ids:
            tasks_q = tasks_q.filter(or_(Task.assigned_to.in_(ids), Task.created_by.in_(ids)))
            reports_q = reports_q.filter(DailyReport.user_id.in_(ids))
        else:
            tasks_q = tasks_q.filter(Task.id == -1)
            reports_q = reports_q.filter(DailyReport.id == -1)

    if user_id:
        tasks_q = tasks_q.filter(or_(Task.assigned_to == user_id, Task.created_by == user_id))
        reports_q = reports_q.filter(DailyReport.user_id == user_id)

    tasks = tasks_q.all()
    reports = reports_q.all()

    # 构造范围参数用于指纹/复用
    scope_params = {
        "start_date": s.isoformat(),
        "end_date": e.isoformat(),
        "group_id": group_id,
        "viewer_id": current_user.id,
        "role": current_user.role,
        "role_scope": scope,
        "user_id": user_id,
    }
    fingerprint = _compute_dataset_fingerprint(tasks, reports, scope_params)

    # 选择活跃的AI功能：根据视角（个人/团队）优先使用对应功能
    ai_function = None
    try:
        team_scope = bool(group_id) or (scope and scope.lower() in ["team", "group"])
        if team_scope:
            # 团队数据洞察优先匹配中文名称或英文别名
            ai_function = db.query(AIFunction).filter(
                AIFunction.is_active == True,
                or_(AIFunction.name == "团队数据洞察", AIFunction.name == "team_insight")
            ).first()
        else:
            # 个人数据洞察优先匹配中文名称或英文别名
            ai_function = db.query(AIFunction).filter(
                AIFunction.is_active == True,
                or_(AIFunction.name == "个人数据洞察", AIFunction.name == "personal_insight")
            ).first()
    except Exception:
        ai_function = None
    # 若未找到特定功能，回退到最近的活跃功能
    if not ai_function:
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
    role_scope: Optional[str] = Query(None),
    group_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_ai_insights(start_date, end_date, role_scope, group_id, user_id, db, current_user)

# =============== 新增：AI 总结报告（POST） ===============
@app.post("/api/v1/analytics/ai-insight-summary")
async def analytics_ai_insight_summary(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """根据当前视角与时间范围生成总结报告（轻量实现，便于前端联动）。"""
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    role_scope = payload.get("role_scope")
    group_id = payload.get("group_id")
    user_id = payload.get("user_id")

    s, e = _parse_date_range(start_date, end_date)
    # 复用数据接口的核心计算
    data = await analytics_data(start_date, end_date, role_scope, group_id, user_id, db, current_user)
    metrics = data.get("metrics", {})
    stats = data.get("stats", {})

    # 生成轻量总结（启发式文本）
    comp = stats.get("completionRate", 0)
    avg_emotion_score = stats.get("avgEmotionScore", 0)
    sales_actual = metrics.get("sales_actual")
    sales_target = metrics.get("sales_target")
    ach_rate = metrics.get("sales_achievement_rate")

    lines = []
    if sales_actual is not None and sales_target is not None:
        lines.append(f"销售达成率 {ach_rate or 0}%（实际 {round(sales_actual or 0, 2)}/{round(sales_target or 0, 2)}）")
    lines.append(f"任务完成率 {comp}%，日报提交覆盖 {metrics.get('report_submission_rate', 0)}%")
    # 情绪分作为满意度近似（0-10）
    lines.append(f"平均情感分 {avg_emotion_score}（十分制）")
    summary_text = "；".join(lines)

    suggestions = []
    if comp < 60:
        suggestions.append("提升任务执行力：明确优先级，设置短周期检查点")
    if (ach_rate or 0) < 70 and (sales_target or 0) > 0:
        suggestions.append("优化销售策略：针对转介绍与复购制定专项活动")
    if avg_emotion_score < 5:
        suggestions.append("关注员工情绪与支持：加强团队互助与激励机制")
    if not suggestions:
        suggestions.append("保持良好趋势：延续当前策略并关注异常波动")

    # 写入 AI 调用日志（模拟）
    start_dt = datetime.combine(s, datetime.min.time())
    end_dt = datetime.combine(e, datetime.max.time())
    ai_function = db.query(AIFunction).filter(AIFunction.is_active == True).order_by(AIFunction.created_at.desc()).first()
    if ai_function:
        call_log = AICallLog(
            function_id=ai_function.id,
            agent_id=ai_function.agent_id,
            user_id=current_user.id,
            request_data={
                "type": "analytics_summary",
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "role_scope": role_scope,
                "group_id": group_id,
            },
            status=CallStatus.SUCCESS,
            duration_ms=0,
            response_data={
                "summary": summary_text,
                "suggestions": suggestions,
            },
        )
        db.add(call_log)
        db.commit()

    return {"summary": summary_text, "suggestions": suggestions}

# 兼容前端旧路径（无版本前缀）
@app.post("/analytics/ai-insight-summary")
async def analytics_ai_insight_summary_alias(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await analytics_ai_insight_summary(payload, db, current_user)

# =============== 新增：指标 Schema（可选） ===============
@app.get("/api/v1/analytics/schema")
async def analytics_schema():
    """返回固定指标 Schema（前端也可内置，此接口为后端对齐）。"""
    return {
        "CC_SS": [
            {"key": "task_completion_rate", "label": "任务完成率", "unit": "%"},
            {"key": "sales_target", "label": "销售目标金额", "unit": "USD"},
            {"key": "sales_actual", "label": "实际销售金额", "unit": "USD"},
            {"key": "sales_achievement_rate", "label": "销售目标达成率", "unit": "%"},
            {"key": "touch_count", "label": "服务次数", "unit": "次"},
            {"key": "touch_coverage", "label": "服务覆盖率", "unit": "%"},
            {"key": "referral_count", "label": "转介绍数量", "unit": "个"},
            {"key": "report_submission_rate", "label": "日报提交率", "unit": "%"},
            {"key": "call_count", "label": "通次", "unit": "次"},
            {"key": "call_duration", "label": "通时", "unit": "分钟"},
            {"key": "deal_count", "label": "谈单量", "unit": "单"},
            {"key": "followup_feedback", "label": "跟进反馈次数", "unit": "条"},
        ],
        "LP": [
            {"key": "service_count", "label": "服务次数", "unit": "次"},
            {"key": "service_touch_rate", "label": "服务触达率", "unit": "%"},
            {"key": "satisfaction_score", "label": "满意度", "unit": "分"},
            {"key": "iur_completion_rate", "label": "IUR 完成率", "unit": "%"},
            {"key": "complaint_count", "label": "投诉数量", "unit": "起"},
            {"key": "followup_quality", "label": "跟进质量评分", "unit": "分"},
        ],
        "ALL": [
            {"key": "total_sales_all", "label": "公司总销售额", "unit": "USD"},
            {"key": "avg_sales_achievement", "label": "销售目标平均达成率", "unit": "%"},
            {"key": "avg_task_completion", "label": "任务平均完成率", "unit": "%"},
            {"key": "customer_growth_rate", "label": "客户增长率", "unit": "%"},
            {"key": "lp_service_coverage", "label": "LP服务覆盖率", "unit": "%"},
            {"key": "renewal_rate_total", "label": "整体续费率", "unit": "%"},
            {"key": "referral_growth", "label": "转介绍增长率", "unit": "%"},
            {"key": "overall_satisfaction", "label": "整体满意度", "unit": "分"},
            {"key": "team_gap_rate", "label": "低绩效团队占比", "unit": "%"},
            {"key": "ai_usage_total", "label": "AI 功能使用次数", "unit": "次"},
        ],
    }

# 兼容前端旧路径（无版本前缀）
@app.get("/analytics/schema")
async def analytics_schema_alias():
    return await analytics_schema()

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
        # 读取数据库中的指标
        from .models import AdminMetric
        q = db.query(AdminMetric).order_by(AdminMetric.created_at.desc())
        total = q.count()
        items = [m.to_dict() for m in q.offset((page - 1) * size).limit(size).all()]
        # 若无数据，返回空列表（也可在此处进行默认种子数据的插入）
        return {
            "items": items,
            "total": total,
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
        
        # 计算成功率（百分比，保留两位小数）
        success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0.0
        success_rate = round(success_rate, 2)
        
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

# ==================== AI 浮动球：系统知识与聊天 ====================

@app.get("/api/v1/ai/system-knowledge", response_model=AISystemKnowledgeResponse)
async def get_ai_system_knowledge(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """提供系统向导的欢迎语与推荐问题（基于用户身份类型定制）"""
    try:
        branch = current_user.get_ai_knowledge_branch()
        welcome = f"你好，{current_user.username}！我是系统向导，帮你快速找到功能入口。"
        recommended = [
            "如何查看我的任务进度？",
            "如何提交当天的日报？",
            "哪里可以设置月度目标？",
        ]
        if branch == "ANALYTICS":
            recommended = [
                "如何查看销售趋势与转介绍？",
                "在哪里设置月度目标？",
                "如何查看我的任务完成率？",
            ]
        elif branch == "SS":
            recommended = [
                "如何查看续费与升级数据？",
                "如何管理班级与学员进度？",
                "如何提交日报并补录任务快照？",
            ]
        elif branch == "LP":
            recommended = [
                "如何查看课程上线进度？",
                "如何管理版本需求与任务？",
                "如何查看团队数据洞察？",
            ]
        return AISystemKnowledgeResponse(welcome=welcome, recommended=recommended)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统知识失败: {str(e)}")


@app.post("/api/v1/ai/chat", response_model=AIChatResponse)
async def ai_chat(
    req: AIChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """简单规则的 AI 向导聊天（用于浮动球），后续可接入真实大模型"""
    try:
        q = (req.question or "").strip()
        answer = "这是 AI 向导的示例回答：请在系统中查找对应功能入口。"
        if re.search(r"任务|进度", q):
            answer = "任务进度可在“任务管理”与“仪表盘”查看。"
        elif re.search(r"日报|提交", q):
            answer = "提交日报请进入“日报”页面，点击新建后填写并提交。"
        elif re.search(r"目标|月度", q):
            answer = "月度目标可在“分析/目标管理”页进行设置与查看。"
        elif re.search(r"AI|洞察|分析", q):
            answer = "AI 数据洞察入口位于“分析”模块，可生成趋势与摘要。"
        return AIChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI聊天失败: {str(e)}")


# ==================== 统一 AI 答复编排 ====================

def _classify_intent(text: str) -> str:
    """启发式意图分类：knowledge / data / hybrid"""
    t = (text or '').lower()
    # 中文关键词简单匹配
    knowledge_keys = ["规则", "流程", "解释", "如何", "说明", "背景", "政策", "标准", "定义", "指南"]
    data_keys = ["趋势", "环比", "同比", "占比", "指标", "完成率", "销量", "续费", "升级", "数据", "统计", "图表", "报表", "分析", "目标", "变化", "增长"]
    k_hit = any(kw in text for kw in knowledge_keys)
    d_hit = any(kw in text for kw in data_keys)
    if k_hit and d_hit:
        return "hybrid"
    if d_hit:
        return "data"
    if k_hit:
        return "knowledge"
    # 默认：根据提问形式猜测
    return "knowledge" if re.search(r"(如何|是什么|怎么|为啥|为什么)", text) else "data"


def _resolve_output_target(current_user: User, explicit: Optional[str]) -> str:
    if explicit in ("personal", "team"):
        return explicit
    # 管理类角色默认团队视角，其余默认个人
    if getattr(current_user, "is_admin", False) or getattr(current_user, "is_super_admin", False):
        return "team"
    return "personal"


def _pick_function_for_target(db: Session, target: str) -> Optional[AIFunction]:
    name = "个人数据洞察" if target == "personal" else "团队数据洞察"
    func = db.query(AIFunction).filter(AIFunction.name == name, AIFunction.is_active == True).first()
    if func:
        return func
    # 回退：取最近的启用功能
    return db.query(AIFunction).filter(AIFunction.is_active == True).order_by(AIFunction.created_at.desc()).first()


@app.post("/api/v1/ai/answer", response_model=AIAnswerResponse)
async def ai_answer(
    req: AIAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """统一 AI 答复：意图识别 → 检索/聚合 → 输出组织（由智能体 System Prompt 决定）。"""
    try:
        intent = _classify_intent(req.question or "")
        target = _resolve_output_target(current_user, req.output_target)

        # 选择功能点与对应智能体
        function = _pick_function_for_target(db, target)
        agent_id = function.agent_id if function else None
        function_id = function.id if function else None

        # 组装数据上下文（仅数据意图或混合）
        data_used = False
        data_sources: List[Dict[str, Any]] = []
        data_summary = None
        if intent in ("data", "hybrid"):
            data_used = True
            # 用统一数据接口与总结接口
            analytics_payload = await analytics_ai_insight_summary({
                "start_date": req.start_date,
                "end_date": req.end_date,
                "role_scope": req.role_scope,
                "group_id": req.group_id,
                "user_id": req.user_id,
            }, db, current_user)
            data_summary = analytics_payload
            # 汇总来源（简化）
            data_sources.append({
                "type": "analytics_summary",
                "period": {"start": req.start_date, "end": req.end_date},
                "role_scope": req.role_scope or current_user.get_ai_knowledge_branch(),
            })

        # 组装知识上下文（总是纳入 Summary 逻辑，但此处为占位）
        knowledge_used = intent in ("knowledge", "hybrid")
        kb_sources: List[Dict[str, Any]] = []
        if knowledge_used:
            # 当前版本未接入真实知识库，放占位说明
            kb_sources.append({
                "type": "kb",
                "modules": ["Summary", (current_user.identity_type or "").upper()],
                "note": "知识库检索尚未接入，后续将返回已发布条目摘要",
            })

        # 生成最终文本（由智能体决定风格；当前先用启发式拼接）
        parts = []
        # 结论
        if intent == "data" and data_summary:
            parts.append(f"结论：{data_summary.get('summary', '暂无数据总结')}。")
        elif intent == "knowledge":
            parts.append("结论：依据 Summary 与身份模块的规则进行处理；当前知识库尚未接入，建议参考知识页的已发布内容。")
        else:  # hybrid
            if data_summary:
                parts.append(f"结论：{data_summary.get('summary', '暂无数据总结')}；结合背景规则执行相应流程。")
            else:
                parts.append("结论：结合通用背景与身份规则处理，该问题涉及数据与知识。")

        # 依据
        evidences = []
        if data_summary:
            evidences.append("数据依据：分析总结与关键指标已纳入。")
        if knowledge_used:
            evidences.append("知识依据：Summary 模块与身份模块（占位）。")
        if evidences:
            parts.append("依据：" + "；".join(evidences))

        # 建议
        if data_summary and isinstance(data_summary.get("suggestions"), list) and data_summary["suggestions"]:
            parts.append("建议：" + "；".join(data_summary["suggestions"]))
        else:
            parts.append("建议：如需更具体建议，请明确时间范围/身份视角或补充问题细化。")

        answer_text = "\n".join(parts)

        # 写入调用日志
        start_time = datetime.utcnow()
        call_log = AICallLog(
            function_id=function_id,
            agent_id=agent_id,
            user_id=current_user.id,
            request_data={
                "question": req.question,
                "intent": intent,
                "output_target": target,
                "start_date": req.start_date,
                "end_date": req.end_date,
                "role_scope": req.role_scope,
                "group_id": req.group_id,
                "page_context": req.page_context,
            },
            status=CallStatus.SUCCESS,
            duration_ms=0,
            started_at=start_time,
            completed_at=datetime.utcnow(),
            response_data={"answer": answer_text}
        )
        db.add(call_log)
        db.commit()

        return AIAnswerResponse(
            answer=answer_text,
            used={"knowledge": knowledge_used, "data": data_used, "hybrid": intent == "hybrid"},
            output_target=target,
            agent_id=agent_id,
            function_id=function_id,
            sources=(kb_sources + data_sources) or None,
            meta={"intent": intent}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI统一答复失败: {str(e)}")

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
            organization="系统管理",
            hashed_password=get_password_hash("51talk2025")
        )
        db.add(admin_user)
        db.commit()
        print("✓ 已创建默认超级管理员: admin")
        print("默认密码：51talk2025（请登陆后尽快修改）")
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
        # 若 admin 未设置密码，则初始化默认密码
        if not existing_admin.hashed_password:
            existing_admin.hashed_password = get_password_hash("51talk2025")
            db.commit()
            print("✓ 已为 'admin' 初始化默认密码：51talk2025（请尽快修改）")
    
    db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

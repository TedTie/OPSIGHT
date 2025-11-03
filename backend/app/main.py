from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional
from datetime import datetime

from .db import engine, get_db
from .models import (
    Base, User, UserGroup, Task, TaskStatus, TaskType, TaskAssignmentType, TaskPriority, 
    TaskJielongEntry, TaskCompletion, DailyReport,
    AIAgent, AIFunction, AICallLog, AIProvider, AIFunctionType, CallStatus,
    AISettings, SystemSettings
)
from .schemas import (
    UserGroupCreateRequest, UserGroupUpdateRequest, UserGroupResponse,
    UserCreateRequest, UserUpdateRequest, UserResponse, 
    LoginRequest, AuthResponse, 
    DailyReportCreateRequest, DailyReportUpdateRequest, DailyReportResponse,
    TaskCreateRequest, TaskUpdateRequest, TaskResponse, PaginatedTaskResponse,
    AIAgentCreateRequest, AIAgentUpdateRequest, AIAgentResponse,
    AIFunctionCreateRequest, AIFunctionUpdateRequest, AIFunctionResponse,
    AICallLogResponse, AICallRequest, AICallResponse, AIStatsResponse,
    PaginatedAICallLogResponse, PaginatedUserResponse, PaginatedUserGroupResponse,
    AddMembersRequest, RemoveMemberRequest,
    AISettingsCreateRequest, AISettingsUpdateRequest, AISettingsResponse,
    SystemSettingsCreateRequest, SystemSettingsUpdateRequest, SystemSettingsResponse
)
from .auth import get_current_user_simple, login_user_simple, logout_user_simple

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OPSIGHT 简化版",
    description="内部使用的简化任务管理系统 - 基于 Cookie 的身份验证",
    version="1.0.0"
)

# CORS 配置 - 简化版，允许更多源
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "http://localhost:5173",  # Vite 默认端口
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"🔍 收到请求: {request.method} {request.url}")
    print(f"   来源: {request.headers.get('origin', 'N/A')}")
    print(f"   User-Agent: {request.headers.get('user-agent', 'N/A')}")
    response = await call_next(request)
    print(f"   响应状态: {response.status_code}")
    return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器错误: {str(exc)}"}
    )

# 根路由
@app.get("/")
async def root():
    return {"message": "OPSIGHT 简化版 API 服务器运行正常"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "opsight-simple", "test_modification": "SUCCESS"}

# 认证端点 - 标准RESTful API

@app.post("/api/v1/auth/login", response_model=AuthResponse)
async def login(
    login_request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """用户登录 - 只需要用户名"""
    try:
        user = login_user_simple(login_request.username, db)

        # 设置认证 cookie
        response.set_cookie(
            key="username",
            value=user.username,
            httponly=True,
            max_age=86400,  # 24小时
            samesite="lax"
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

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

@app.post("/api/v1/auth/logout")
async def logout(response: Response):
    """用户登出"""
    response.delete_cookie("username")
    return logout_user_simple()

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_simple)
):
    """获取当前用户信息"""
    user_response = UserResponse(
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
    return user_response

@app.get("/api/v1/auth/check")
async def check_auth_status(request: Request):
    """检查登录状态"""
    username = request.cookies.get("username")
    if username:
        return {"authenticated": True, "username": username}
    return {"authenticated": False}

# 用户组管理
@app.post("/api/v1/groups", response_model=UserGroupResponse)
async def create_group(
    group_request: UserGroupCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """创建用户组（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以创建用户组"
        )

    # 检查同名组是否存在
    existing_group = db.query(UserGroup).filter(UserGroup.name == group_request.name).first()
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户组名称已存在"
        )

    new_group = UserGroup(
        name=group_request.name,
        description=group_request.description
    )

    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    return UserGroupResponse(
        id=new_group.id,
        name=new_group.name,
        description=new_group.description,
        created_at=new_group.created_at,
        updated_at=new_group.updated_at
    )

@app.get("/api/v1/groups", response_model=PaginatedUserGroupResponse)
async def list_groups(
    page: int = 1,
    size: int = 20,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取用户组列表"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看用户组"
        )

    # 构建查询
    query = db.query(UserGroup)
    
    # 添加搜索条件
    if search:
        query = query.filter(UserGroup.name.contains(search))
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * size
    groups = query.offset(offset).limit(size).all()
    
    # 为每个组别计算成员数量
    group_responses = []
    for group in groups:
        member_count = db.query(User).filter(User.group_id == group.id).count()
        group_responses.append(UserGroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            member_count=member_count,
            created_at=group.created_at,
            updated_at=group.updated_at
        ))
    
    return PaginatedUserGroupResponse(
        items=group_responses,
        total=total,
        page=page,
        size=size
    )

@app.get("/api/v1/groups/{group_id}/members", response_model=List[UserResponse])
async def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取组别成员列表"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看组别成员"
        )

    # 检查组别是否存在
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组别不存在"
        )

    # 获取组别成员
    members = db.query(User).filter(User.group_id == group_id).all()
    
    return [UserResponse(
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
    ) for user in members]

@app.post("/api/v1/groups/{group_id}/members")
async def add_group_members(
    group_id: int,
    request: AddMembersRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """添加组别成员"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以管理组别成员"
        )

    # 检查组别是否存在
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组别不存在"
        )

    # 检查用户是否存在并更新其组别
    updated_count = 0
    for user_id in request.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.group_id = group_id
            updated_count += 1

    db.commit()
    
    return {"message": f"成功添加 {updated_count} 个成员到组别"}

@app.delete("/api/v1/groups/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """移除组别成员"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以管理组别成员"
        )

    # 检查组别是否存在
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组别不存在"
        )

    # 检查用户是否存在并移除其组别
    user = db.query(User).filter(User.id == user_id, User.group_id == group_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不在该组别中"
        )

    user.group_id = None
    db.commit()
    
    return {"message": "成功移除成员"}

@app.put("/api/v1/groups/{group_id}", response_model=UserGroupResponse)
async def update_group(
    group_id: int,
    group_request: UserGroupUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """更新用户组（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以更新用户组"
        )

    # 检查组别是否存在
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组别不存在"
        )

    # 检查同名组是否存在（排除当前组）
    existing_group = db.query(UserGroup).filter(
        UserGroup.name == group_request.name,
        UserGroup.id != group_id
    ).first()
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户组名称已存在"
        )

    # 更新组别信息
    group.name = group_request.name
    group.description = group_request.description
    
    db.commit()
    db.refresh(group)

    return UserGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        updated_at=group.updated_at
    )

@app.delete("/api/v1/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """删除用户组（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以删除用户组"
        )

    # 检查组别是否存在
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组别不存在"
        )

    # 检查组别是否有成员
    member_count = db.query(User).filter(User.group_id == group_id).count()
    if member_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法删除组别，该组别还有 {member_count} 个成员"
        )

    # 删除组别
    db.delete(group)
    db.commit()
    
    return {"message": "组别删除成功"}

# 用户管理 - 只有超级管理员可以创建/管理用户

@app.post("/api/v1/users", response_model=UserResponse)
async def create_user(
    user_request: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """创建用户（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以创建用户"
        )

    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 验证组别是否存在（如果指定了组别）
    if user_request.group_id:
        group = db.query(UserGroup).filter(UserGroup.id == user_request.group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的用户组不存在"
            )

    # 创建新用户
    new_user = User(
        username=user_request.username,
        role=user_request.role,
        identity_type=user_request.identity_type,
        organization=user_request.organization,
        group_id=user_request.group_id
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
async def list_users(
    page: int = 1,
    size: int = 20,
    search: str = None,
    role: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """列出用户（超级管理员可查看所有用户，管理员只能查看同组用户）"""
    if not (current_user.is_super_admin or current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员或超级管理员可以查看用户列表"
        )

    # 构建查询
    query = db.query(User)
    
    # 权限控制：管理员只能查看同组用户
    if current_user.is_admin and not current_user.is_super_admin:
        if current_user.group_id:
            query = query.filter(User.group_id == current_user.group_id)
        else:
            # 如果管理员没有组，只能看到自己
            query = query.filter(User.id == current_user.id)
    
    # 添加搜索条件
    if search:
        query = query.filter(User.username.contains(search))
    
    if role:
        query = query.filter(User.role == role)
        
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * size
    users = query.offset(offset).limit(size).all()
    
    return PaginatedUserResponse(
        items=[UserResponse(
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
        ) for user in users],
        total=total,
        page=page,
        size=size
    )

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取单个用户（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以查看用户详情"
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
    user_update: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """更新用户（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以更新用户"
        )

    # 不能禁用当前用户
    if user_id == current_user.id and user_update.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用当前登录用户"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新字段
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.identity_type is not None:
        user.identity_type = user_update.identity_type
    if user_update.organization is not None:
        user.organization = user_update.organization
    if user_update.group_id is not None:
        user.group_id = user_update.group_id
    if user_update.is_active is not None:
        user.is_active = user_update.is_active

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
    current_user: User = Depends(get_current_user_simple)
):
    """删除用户（仅超级管理员）"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以删除用户"
        )

    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录用户"
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

# 任务管理端点

@app.post("/api/v1/tasks")
async def create_task(
    task_data: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """创建任务（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建任务"
        )

    # 验证分配类型和参数
    if task_data.assignment_type == TaskAssignmentType.USER and not task_data.assigned_user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定用户分配时必须提供用户ID"
        )
    if task_data.assignment_type == TaskAssignmentType.GROUP and not task_data.assigned_group_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定组分配时必须提供组ID"
        )
    if task_data.assignment_type == TaskAssignmentType.IDENTITY and not task_data.target_identity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定身份分配时必须提供身份标识"
        )

    # 权限控制：管理员只能选择自己所在的组别，超级管理员可以选择任意组别
    if task_data.assignment_type == TaskAssignmentType.GROUP and task_data.assigned_group_ids:
        if not current_user.is_super_admin:
            # 管理员只能选择自己所在的组别
            if current_user.group_id not in task_data.assigned_group_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="管理员只能为自己所在的组别创建任务"
                )

    # 处理分配信息
    assigned_to = None
    target_group_id = None
    
    if task_data.assignment_type == TaskAssignmentType.USER and task_data.assigned_user_ids:
        assigned_to = task_data.assigned_user_ids[0]  # 暂时只支持单个用户
    elif task_data.assignment_type == TaskAssignmentType.GROUP and task_data.assigned_group_ids:
        target_group_id = task_data.assigned_group_ids[0]  # 暂时只支持单个组

    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type,
        assignment_type=task_data.assignment_type,
        assigned_to=assigned_to,
        target_group_id=target_group_id,
        target_identity=task_data.target_identity,
        priority=task_data.priority,
        target_amount=task_data.target_amount,
        target_quantity=task_data.target_quantity,
        jielong_target_count=task_data.jielong_target_count,
        jielong_config=task_data.jielong_config or {},
        due_date=task_data.due_date,
        created_by=current_user.id
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {"message": "任务创建成功", "task_id": new_task.id}

@app.get("/api/v1/tasks")
async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    task_type: Optional[TaskType] = None,
    assigned_to_me: bool = False,
    created_by_me: bool = False,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取任务列表"""
    query = db.query(Task)

    # 状态过滤
    if status:
        query = query.filter(Task.status == status)

    # 优先级过滤
    if priority:
        query = query.filter(Task.priority == priority)

    # 任务类型过滤
    if task_type:
        query = query.filter(Task.task_type == task_type)

    # 分配给我的任务
    if assigned_to_me:
        query = query.filter(
            or_(
                Task.assignment_type == TaskAssignmentType.ALL,
                and_(Task.assignment_type == TaskAssignmentType.USER, Task.assigned_to == current_user.id)
            )
        )

    # 我创建的任务
    if created_by_me:
        query = query.filter(Task.created_by == current_user.id)

    # 管理员可以看到所有任务，普通用户只能看到分配给自己的任务
    if not current_user.is_admin:
        query = query.filter(
            or_(
                Task.assignment_type == TaskAssignmentType.ALL,
                and_(Task.assignment_type == TaskAssignmentType.USER, Task.assigned_to == current_user.id)
            )
        )

    # 分页
    total = query.count()
    tasks = query.offset((page - 1) * size).limit(size).all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type,
                "assignment_type": task.assignment_type,
                "assigned_to": task.assigned_to,
                "target_group_id": task.target_group_id,
                "target_identity": task.target_identity,
                "status": task.status,
                "priority": task.priority,
                "progress_percentage": task.get_progress_percentage(),
                "target_amount": task.target_amount,
                "current_amount": task.current_amount,
                "target_quantity": task.target_quantity,
                "current_quantity": task.current_quantity,
                "jielong_target_count": task.jielong_target_count,
                "jielong_current_count": task.jielong_current_count,
                "is_completed": task.is_completed,
                "due_date": task.due_date,
                "created_by": task.created_by,
                "created_at": task.created_at
            }
            for task in tasks
        ]
    }

@app.get("/api/v1/tasks/{task_id}")
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 检查权限
    if not current_user.is_admin and not task.is_assigned_to_user(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此任务"
        )

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "assignment_type": task.assignment_type,
        "assigned_to": task.assigned_to,
        "target_group_id": task.target_group_id,
        "target_identity": task.target_identity,
        "status": task.status,
        "priority": task.priority,
        "progress_percentage": task.get_progress_percentage(),
        "target_amount": task.target_amount,
        "current_amount": task.current_amount,
        "target_quantity": task.target_quantity,
        "current_quantity": task.current_quantity,
        "jielong_target_count": task.jielong_target_count,
        "jielong_current_count": task.jielong_current_count,
        "jielong_config": task.jielong_config,
        "is_completed": task.is_completed,
        "due_date": task.due_date,
        "created_by": task.created_by,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }

@app.put("/api/v1/tasks/{task_id}/status")
async def update_task_status(
    task_id: int,
    status: TaskStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """更新任务状态"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 检查权限 - 只有管理员或任务执行者可以更新状态
    if not current_user.is_admin and not task.is_assigned_to_user(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新此任务状态"
        )

    task.status = status
    if status == TaskStatus.DONE:
        task.end_time = datetime.now()

    db.commit()

    return {"message": "任务状态更新成功"}

@app.post("/api/v1/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    completion_value: Optional[float] = None,
    completion_data: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """完成任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 检查权限
    if not task.is_assigned_to_user(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权完成此任务"
        )

    # 根据任务类型处理完成逻辑
    if task.task_type == TaskType.AMOUNT:
        if completion_value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="金额任务需要提供完成金额"
            )
        task.current_amount += completion_value
        if task.current_amount >= (task.target_amount or 0):
            task.status = TaskStatus.DONE
            task.is_completed = True

    elif task.task_type == TaskType.QUANTITY:
        if completion_value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="数量任务需要提供完成数量"
            )
        task.current_quantity += int(completion_value)
        if task.current_quantity >= (task.target_quantity or 0):
            task.status = TaskStatus.DONE
            task.is_completed = True

    elif task.task_type == TaskType.CHECKBOX:
        task.is_completed = True
        task.status = TaskStatus.DONE

    # 记录完成信息
    completion = TaskCompletion(
        task_id=task_id,
        user_id=current_user.id,
        completion_value=completion_value,
        completion_data=completion_data or {},
        is_completed=True
    )

    db.add(completion)
    db.commit()

    return {"message": "任务完成成功", "progress_percentage": task.get_progress_percentage()}

# 接龙任务相关端点

@app.post("/api/v1/tasks/{task_id}/jielong")
async def submit_jielong_entry(
    task_id: int,
    entry_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """提交接龙任务参与"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    if task.task_type != TaskType.JIELONG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此任务不是接龙任务"
        )

    # 检查是否已参与
    existing_entry = db.query(TaskJielongEntry).filter(
        TaskJielongEntry.task_id == task_id,
        TaskJielongEntry.user_id == current_user.id
    ).first()

    if existing_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已经参与过此接龙任务"
        )

    # 获取接龙顺序
    max_order = db.query(TaskJielongEntry).filter(
        TaskJielongEntry.task_id == task_id
    ).count()

    # 创建接龙记录，不设置id字段让数据库自动生成
    from datetime import datetime
    entry = TaskJielongEntry(
        task_id=task_id,
        user_id=current_user.id,
        entry_data=entry_data,
        entry_order=max_order + 1,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(entry)

    # 更新任务接龙计数
    task.jielong_current_count += 1
    if task.jielong_current_count >= (task.jielong_target_count or 0):
        task.status = TaskStatus.DONE

    try:
        db.commit()
        db.refresh(entry)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"接龙提交失败: {str(e)}"
        )

    return {"message": "接龙提交成功", "entry_order": entry.entry_order}

@app.get("/api/v1/tasks/{task_id}/jielong-entries")
async def get_jielong_entries(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取接龙任务参与记录"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    if task.task_type != TaskType.JIELONG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此任务不是接龙任务"
        )

    # 检查权限
    if not current_user.is_admin and not task.is_assigned_to_user(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此任务的接龙记录"
        )

    entries = db.query(TaskJielongEntry).filter(
        TaskJielongEntry.task_id == task_id
    ).order_by(TaskJielongEntry.entry_order).all()

    return {
        "entries": [
            {
                "id": entry.id,
                "user_id": entry.user_id,
                "entry_data": entry.entry_data,
                "entry_order": entry.entry_order,
                "created_at": entry.created_at
            }
            for entry in entries
        ]
    }

# 任务编辑和参与相关端点

@app.put("/api/v1/tasks/{task_id}")
async def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    task_type: Optional[str] = None,
    assignment_type: Optional[str] = None,
    target_amount: Optional[float] = None,
    target_quantity: Optional[int] = None,
    jielong_target_count: Optional[int] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """编辑任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 检查权限：只有管理员或任务创建者可以编辑
    if not current_user.is_admin and task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权编辑此任务"
        )

    # 更新任务字段
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if task_type is not None:
        task.task_type = TaskType(task_type)
    if assignment_type is not None:
        task.assignment_type = TaskAssignmentType(assignment_type)
    if target_amount is not None:
        task.target_amount = target_amount
    if target_quantity is not None:
        task.target_quantity = target_quantity
    if jielong_target_count is not None:
        task.jielong_target_count = jielong_target_count
    if priority is not None:
        task.priority = TaskPriority(priority)
    if due_date is not None:
        from datetime import datetime
        task.due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))

    try:
        db.commit()
        db.refresh(task)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务更新失败: {str(e)}"
        )

    return {"message": "任务更新成功", "task_id": task.id}

@app.post("/api/v1/tasks/{task_id}/amount")
async def participate_amount_task(
    task_id: int,
    amount: float,
    note: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """参与金额任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    if task.task_type != TaskType.AMOUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此任务不是金额任务"
        )

    # 检查权限
    if not task.is_assigned_to_user(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权参与此任务"
        )

    # 更新任务金额
    task.current_amount += amount
    if task.current_amount >= (task.target_amount or 0):
        task.status = TaskStatus.DONE

    # 记录参与信息
    completion = TaskCompletion(
        task_id=task_id,
        user_id=current_user.id,
        completion_value=amount,
        completion_data={"note": note or "", "participation_type": "amount"},
        is_completed=False  # 这是参与记录，不是完成记录
    )

    db.add(completion)

    try:
        db.commit()
        db.refresh(task)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"金额任务参与失败: {str(e)}"
        )

    return {
        "message": "金额任务参与成功",
        "current_amount": task.current_amount,
        "target_amount": task.target_amount,
        "progress_percentage": task.get_progress_percentage()
    }

@app.post("/api/v1/tasks/{task_id}/quantity")
async def participate_quantity_task(
    task_id: int,
    quantity: int,
    note: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """参与数量任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    if task.task_type != TaskType.QUANTITY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此任务不是数量任务"
        )

    # 检查权限
    if not task.is_assigned_to_user(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权参与此任务"
        )

    # 更新任务数量
    task.current_quantity += quantity
    if task.current_quantity >= (task.target_quantity or 0):
        task.status = TaskStatus.DONE

    # 记录参与信息
    completion = TaskCompletion(
        task_id=task_id,
        user_id=current_user.id,
        completion_value=float(quantity),
        completion_data={"note": note or "", "participation_type": "quantity"},
        is_completed=False  # 这是参与记录，不是完成记录
    )

    db.add(completion)

    try:
        db.commit()
        db.refresh(task)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数量任务参与失败: {str(e)}"
        )

    return {
        "message": "数量任务参与成功",
        "current_quantity": task.current_quantity,
        "target_quantity": task.target_quantity,
        "progress_percentage": task.get_progress_percentage()
    }


# 日报管理API
@app.post("/api/v1/reports", response_model=DailyReportResponse)
async def create_report(
    report_request: DailyReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """创建日报"""
    # 检查当天是否已有日报
    existing_report = db.query(DailyReport).filter(
        DailyReport.user_id == current_user.id,
        DailyReport.work_date == report_request.work_date
    ).first()
    
    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当天已存在日报，请编辑现有日报"
        )

    # 创建新日报
    new_report = DailyReport(
        user_id=current_user.id,
        work_date=report_request.work_date,
        title=report_request.title,
        content=report_request.content,
        work_hours=report_request.work_hours,
        task_progress=report_request.task_progress,
        work_summary=report_request.work_summary,
        mood_score=report_request.mood_score,
        efficiency_score=report_request.efficiency_score,
        call_count=report_request.call_count,
        call_duration=report_request.call_duration,
        achievements=report_request.achievements,
        challenges=report_request.challenges,
        tomorrow_plan=report_request.tomorrow_plan
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return DailyReportResponse.from_orm(new_report)


@app.get("/api/v1/reports", response_model=List[DailyReportResponse])
async def list_reports(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    user_id: Optional[int] = Query(None, description="用户ID (仅管理员可用)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取日报列表"""
    query = db.query(DailyReport)

    # 权限检查：普通用户只能查看自己的日报
    if current_user.role == "user":
        query = query.filter(DailyReport.user_id == current_user.id)
    elif user_id and current_user.is_admin:
        # 管理员可以查看指定用户的日报
        query = query.filter(DailyReport.user_id == user_id)

    # 日期筛选
    if start_date:
        query = query.filter(DailyReport.work_date >= start_date)
    if end_date:
        query = query.filter(DailyReport.work_date <= end_date)

    reports = query.order_by(DailyReport.work_date.desc()).all()
    return [DailyReportResponse.from_orm(report) for report in reports]


@app.get("/api/v1/reports/{report_id}", response_model=DailyReportResponse)
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取单个日报详情"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日报不存在"
        )

    # 权限检查：普通用户只能查看自己的日报
    if current_user.role == "user" and report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此日报"
        )

    return DailyReportResponse.from_orm(report)


@app.put("/api/v1/reports/{report_id}", response_model=DailyReportResponse)
async def update_report(
    report_id: int,
    report_request: DailyReportUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """更新日报"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日报不存在"
        )

    # 权限检查：只能编辑自己的日报
    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权编辑此日报"
        )

    # 更新字段
    update_data = report_request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)

    db.commit()
    db.refresh(report)

    return DailyReportResponse.from_orm(report)


@app.delete("/api/v1/reports/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """删除日报"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日报不存在"
        )

    # 权限检查：只能删除自己的日报，或管理员可以删除任何日报
    if report.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此日报"
        )

    db.delete(report)
    db.commit()

    return {"message": "日报删除成功"}


@app.post("/api/v1/reports/{report_id}/ai-analyze")
async def analyze_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """AI分析日报"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日报不存在"
        )

    # 权限检查：只能分析自己的日报，或管理员可以分析任何日报
    if report.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权分析此日报"
        )

    # 模拟AI分析（实际使用时需要配置AI API密钥）
    ai_analysis = {
        "sentiment_analysis": {
            "score": min(max(report.mood_score / 10.0, 0.1), 1.0),
            "description": f"根据心情评分{report.mood_score}分，工作情绪{'积极' if report.mood_score >= 7 else '一般' if report.mood_score >= 5 else '需要关注'}。",
            "keywords": ["工作状态", "情绪分析", "心情评分"]
        },
        "work_summary": {
            "summary": f"工作时长{report.work_hours}小时，效率评分{report.efficiency_score}分。" + (report.work_summary or ""),
            "key_points": [
                f"工作时长: {report.work_hours}小时",
                f"效率评分: {report.efficiency_score}分",
                f"通话次数: {report.call_count}次" if report.call_count > 0 else None
            ]
        },
        "reflection": {
            "achievements": report.achievements or "未填写具体成就",
            "challenges": report.challenges or "未提及具体挑战",
            "suggestions": [
                "建议保持良好的工作节奏" if report.efficiency_score >= 7 else "建议优化工作效率",
                "继续保持积极心态" if report.mood_score >= 7 else "注意调节工作情绪",
                "合理安排明日计划" if report.tomorrow_plan else "建议制定明确的明日计划"
            ]
        },
        "analysis_time": datetime.now().isoformat()
    }

    # 更新日报的AI分析结果
    report.ai_analysis = ai_analysis
    db.commit()

    return {
        "message": "AI分析完成",
        "analysis": ai_analysis
    }


@app.get("/api/v1/reports/efficiency")
async def get_efficiency_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取工作效率统计"""
    try:
        # 获取用户的所有日报
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
        print(f"获取效率统计失败: {e}")
        # 返回默认值
        return {
            "avgCompletionTime": 4.5,
            "weeklyCompletionRate": 85,
            "totalWorkHours": 42
        }


# 数据分析API
@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取仪表板数据"""
    # 根据用户权限获取数据
    if current_user.role == "user":
        # 普通用户只能看自己的数据
        tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
        reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
    elif current_user.role == "super_admin":
        # 超级管理员可以看所有数据（全体数据）
        tasks = db.query(Task).all()
        reports = db.query(DailyReport).all()
    elif current_user.role == "admin":
        # 普通管理员只能看自己组织的数据
        if current_user.organization:
            # 获取同组织的所有用户
            org_users = db.query(User).filter(User.organization == current_user.organization).all()
            org_user_ids = [u.id for u in org_users]
            tasks = db.query(Task).filter(Task.assigned_to.in_(org_user_ids)).all()
            reports = db.query(DailyReport).filter(DailyReport.user_id.in_(org_user_ids)).all()
        else:
            # 如果没有组织信息，只能看自己的数据
            tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
            reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
    else:
        # 默认情况，只能看自己的数据
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
    current_user: User = Depends(get_current_user_simple)
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
    current_user: User = Depends(get_current_user_simple)
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
    from datetime import datetime, timedelta
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
    current_user: User = Depends(get_current_user_simple)
):
    """获取报告统计摘要"""
    # 根据用户权限获取数据
    if current_user.role == "user":
        reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
    else:
        reports = db.query(DailyReport).all()

    # 计算报告统计
    total_reports = len(reports)
    
    # 计算平均情绪分数
    avg_emotion_score = sum(r.mood_score for r in reports) / total_reports if total_reports > 0 else 0
    
    # 计算平均效率分数
    avg_efficiency_score = sum(r.efficiency_score for r in reports) / total_reports if total_reports > 0 else 0
    
    # 计算总工作时间
    total_work_hours = sum(r.work_hours for r in reports)
    
    # 计算本周报告数量
    from datetime import datetime, timedelta
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
    current_user: User = Depends(get_current_user_simple)
):
    """获取本周任务趋势"""
    from datetime import datetime, timedelta
    
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


# ==================== 管理员指标 API ====================

@app.get("/api/v1/admin/metrics/stats")
async def get_admin_metrics_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
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
            # 超级管理员可以看所有数据（全体数据）
            users = db.query(User).all()
            tasks = db.query(Task).all()
            reports = db.query(DailyReport).all()
        elif current_user.role == "admin":
            # 普通管理员只能看自己组织的数据
            if current_user.organization:
                # 获取同组织的所有用户
                users = db.query(User).filter(User.organization == current_user.organization).all()
                user_ids = [u.id for u in users]
                tasks = db.query(Task).filter(Task.assigned_to.in_(user_ids)).all()
                reports = db.query(DailyReport).filter(DailyReport.user_id.in_(user_ids)).all()
            else:
                # 如果没有组织信息，只能看自己的数据
                users = [current_user]
                tasks = db.query(Task).filter(Task.assigned_to == current_user.id).all()
                reports = db.query(DailyReport).filter(DailyReport.user_id == current_user.id).all()
        else:
            # 默认情况，只能看自己的数据
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


@app.get("/api/v1/admin/metrics")
async def get_admin_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple),
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
                "name": "用户活跃度",
                "description": "用户登录和使用频率",
                "value": 85.5,
                "unit": "%",
                "frequency": "daily",
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": 2,
                "name": "任务完成率",
                "description": "任务按时完成的比例",
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
    current_user: User = Depends(get_current_user_simple)
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
    current_user: User = Depends(get_current_user_simple)
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
    current_user: User = Depends(get_current_user_simple)
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
    current_user: User = Depends(get_current_user_simple)
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
    current_user: User = Depends(get_current_user_simple)
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
    current_user: User = Depends(get_current_user_simple)
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
    current_user: User = Depends(get_current_user_simple)
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
    current_user: User = Depends(get_current_user_simple)
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

# AI调用日志
@app.get("/api/v1/ai/logs", response_model=PaginatedAICallLogResponse)
async def get_ai_call_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    function_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取AI调用日志"""
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
        raise HTTPException(status_code=500, detail=f"获取调用日志失败: {str(e)}")

@app.post("/api/v1/ai/call", response_model=AICallResponse)
async def call_ai_function(
    call_request: AICallRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
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
    
    # 创建调用日志
    input_text = call_request.input_data.get('input_text', str(call_request.input_data))
    start_time = datetime.utcnow()
    call_log = AICallLog(
        function_id=function.id,
        agent_id=function.agent_id,
        user_id=current_user.id,
        request_data=call_request.input_data,
        status=CallStatus.PENDING,
        duration_ms=0,  # 初始值，稍后更新
        started_at=start_time
    )
    db.add(call_log)
    db.commit()
    db.refresh(call_log)
    
    try:
        # 这里应该调用实际的AI服务
        # 目前返回模拟响应
        response_data = {
            "response": f"[模拟AI响应] 功能: {function.name}, 输入: {input_text}",
            "analysis": "这是一个积极正面的文本，表达了愉快的心情。"
        }
        
        # 更新调用日志
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
        # 更新调用日志为失败状态
        call_log.status = CallStatus.FAILED
        call_log.error_message = str(e)
        call_log.completed_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"AI调用失败: {str(e)}")

@app.get("/api/v1/ai/stats", response_model=AIStatsResponse)
async def get_ai_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
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

@app.get("/api/v1/ai/system-config")
async def get_system_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取系统功能配置"""
    try:
        # 这里可以从数据库获取配置，暂时返回空配置
        # 实际项目中可以创建一个SystemConfig表来存储配置
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")

@app.post("/api/v1/ai/system-config")
async def update_system_config(
    config_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """更新系统功能配置"""
    try:
        # 检查权限 - 只有管理员和超级管理员可以配置
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="权限不足")
        
        function_id = config_data.get("function_id")
        agent_id = config_data.get("agent_id")
        is_enabled = config_data.get("is_enabled")
        
        if not function_id:
            raise HTTPException(status_code=400, detail="缺少功能ID")
        
        # 验证智能体是否存在
        if agent_id:
            agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="智能体不存在")
        
        # 这里可以将配置保存到数据库
        # 暂时只返回成功响应
        return {"message": "配置更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@app.post("/api/v1/ai/test-function")
async def test_system_function(
    test_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """测试系统功能"""
    try:
        function_id = test_data.get("function_id")
        input_text = test_data.get("input_text", "")
        
        if not function_id or not input_text:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 模拟AI调用结果
        function_responses = {
            "emotion_analysis": f"情感分析结果：根据文本'{input_text[:50]}...'，检测到积极情绪，情感得分：0.75",
            "reflection_generation": f"反思建议：基于您的描述'{input_text[:50]}...'，建议您在下次遇到类似情况时可以提前做好准备。",
            "task_analysis": f"任务分析：从'{input_text[:50]}...'中识别出效率瓶颈，建议优化工作流程。",
            "report_summary": f"报告摘要：'{input_text[:50]}...'的核心要点是团队协作良好，项目进展顺利。",
            "knowledge_qa": f"知识问答：关于'{input_text[:50]}...'的问题，建议查看相关文档或咨询技术专家。",
            "data_insights": f"数据洞察：从'{input_text[:50]}...'的数据中发现用户活跃度呈上升趋势。"
        }
        
        output_text = function_responses.get(function_id, f"功能'{function_id}'的测试结果：处理完成")
        
        return {
            "output_text": output_text,
            "tokens_used": len(input_text) + len(output_text),
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试功能失败: {str(e)}")

# ==================== 设置管理 API ====================

@app.get("/api/v1/settings/ai", response_model=AISettingsResponse)
async def get_ai_settings(
    current_user: User = Depends(get_current_user_simple),
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
    current_user: User = Depends(get_current_user_simple),
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
    current_user: User = Depends(get_current_user_simple),
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
    current_user: User = Depends(get_current_user_simple),
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


# 任务同步相关API
@app.post("/api/v1/task-sync/sync-task-to-report/{task_id}")
async def sync_task_to_report(
    task_id: int,
    sync_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """同步任务到日报"""
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
            detail="无权同步此任务"
        )
    
    return {"message": "任务同步成功", "task_id": task_id}

@app.put("/api/v1/task-sync/sync-task-to-report/{task_id}")
async def update_task_sync(
    task_id: int,
    sync_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """更新任务同步状态"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return {"message": "任务同步更新成功", "task_id": task_id}

@app.post("/api/v1/task-sync/sync-task-to-report")
async def sync_multiple_tasks(
    sync_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """批量同步任务到日报"""
    return {"message": "批量任务同步成功"}

@app.get("/api/v1/task-sync/daily-task-summary")
async def get_daily_task_summary(
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """获取每日任务摘要"""
    from datetime import datetime, date as date_type
    
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    else:
        target_date = date_type.today()
    
    # 获取当天的任务
    tasks = db.query(Task).filter(
        Task.created_by == current_user.id,
        Task.created_at >= target_date,
        Task.created_at < target_date.replace(day=target_date.day + 1) if target_date.day < 28 else target_date.replace(month=target_date.month + 1, day=1)
    ).all()
    
    return {
        "date": target_date.isoformat(),
        "total_tasks": len(tasks),
        "completed_tasks": len([t for t in tasks if t.status == TaskStatus.DONE]),
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
                "task_type": task.task_type.value
            }
            for task in tasks
        ]
    }

@app.post("/api/v1/task-sync/auto-generate-daily-report")
async def auto_generate_daily_report(
    report_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_simple)
):
    """自动生成日报"""
    from datetime import date, datetime
    
    # 处理日期格式
    work_date_str = report_data.get("date", date.today().isoformat())
    try:
        # 确保日期格式正确
        if isinstance(work_date_str, str):
            work_date = datetime.strptime(work_date_str, "%Y-%m-%d").date()
        else:
            work_date = work_date_str
    except ValueError:
        work_date = date.today()
    
    # 检查是否已有日报
    existing_report = db.query(DailyReport).filter(
        DailyReport.user_id == current_user.id,
        DailyReport.work_date == work_date
    ).first()
    
    if existing_report:
        return {"message": "当天已有日报", "report_id": existing_report.id}
    
    # 创建自动生成的日报
    auto_report = DailyReport(
        user_id=current_user.id,
        work_date=work_date,
        title=f"{work_date} 自动生成日报",
        content="基于任务自动生成的日报内容",
        work_hours=8.0,
        mood_score=7,
        efficiency_score=7
    )
    
    db.add(auto_report)
    db.commit()
    db.refresh(auto_report)
    
    return {"message": "日报自动生成成功", "report_id": auto_report.id}

# 初始化数据 - 如果没有用户则创建默认超级管理员
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
        print("🎉 已创建默认超级管理员: admin")
        print("请使用用户名 'admin' 登录系统")
    else:
        # 确保该用户是超级管理员
        if existing_admin.role != "super_admin":
            existing_admin.role = "super_admin"
            if not existing_admin.identity_type:
                existing_admin.identity_type = "CC"  # 默认为CC身份
            db.commit()
            print("🔧 已将用户 'admin' 升级为超级管理员")
        else:
            print("✅ 超级管理员 'admin' 已存在")
    
    db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from enum import Enum

# 任务相关枚举
class TaskType(str, Enum):
    CHECKBOX = "checkbox"
    NORMAL = "normal"
    AMOUNT = "amount"
    QUANTITY = "quantity"
    JIELONG = "jielong"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskAssignmentType(str, Enum):
    USER = "user"
    GROUP = "group"
    IDENTITY = "identity"
    ALL = "all"

class UserGroupCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class UserGroupUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class UserGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    member_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 任务相关schemas
class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    task_type: TaskType = TaskType.NORMAL
    assignment_type: TaskAssignmentType = TaskAssignmentType.USER
    assigned_user_ids: Optional[List[int]] = None
    assigned_group_ids: Optional[List[int]] = None
    target_identity: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    target_amount: Optional[float] = None
    target_quantity: Optional[int] = None
    jielong_target_count: Optional[int] = None
    jielong_config: Optional[Dict[str, Any]] = None
    due_date: Optional[datetime] = None

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    task_type: Optional[TaskType] = None
    assignment_type: Optional[TaskAssignmentType] = None
    assigned_user_ids: Optional[List[int]] = None
    assigned_group_ids: Optional[List[int]] = None
    target_identity: Optional[str] = None
    priority: Optional[TaskPriority] = None
    target_amount: Optional[float] = None
    target_quantity: Optional[int] = None
    jielong_target_count: Optional[int] = None
    jielong_config: Optional[Dict[str, Any]] = None
    due_date: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    task_type: str
    assignment_type: str
    priority: TaskPriority
    # 任务标签与分配信息（前端需要显示）
    tags: Optional[List[str]] = None
    assigned_to: Optional[int] = None
    target_group_id: Optional[int] = None
    target_identity: Optional[str] = None
    target_amount: Optional[float] = None
    target_quantity: Optional[int] = None
    # 当前进度字段（兼容前端详情页显示）
    current_amount: Optional[float] = None
    current_quantity: Optional[int] = None
    jielong_target_count: Optional[int] = None
    jielong_current_count: Optional[int] = None
    jielong_config: Optional[Dict[str, Any]] = None
    due_date: Optional[datetime] = None
    status: str
    is_completed: Optional[bool] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 个人接龙统计（最小改动：仅在后端计算并返回，前端不改即可读取）
    personal_jielong_current_count: Optional[int] = None
    personal_jielong_target_count: Optional[int] = None
    personal_jielong_progress: Optional[float] = None

    # 汇总接龙进度（用于“全部”视角显示）
    aggregate_jielong_progress: Optional[float] = None
    # 汇总接龙目标数量（用于“全部”视角显示）
    aggregate_jielong_target_count: Optional[int] = None

    # 参与人数（按任务分配对象计算）
    participant_count: Optional[int] = None

    # 金额类型：个人与汇总统计
    personal_current_amount: Optional[float] = None
    personal_target_amount: Optional[float] = None
    personal_amount_progress: Optional[float] = None
    aggregate_current_amount: Optional[float] = None
    aggregate_target_amount: Optional[float] = None
    aggregate_amount_progress: Optional[float] = None

    # 数量类型：个人与汇总统计
    personal_current_quantity: Optional[int] = None
    personal_target_quantity: Optional[int] = None
    personal_quantity_progress: Optional[float] = None
    aggregate_current_quantity: Optional[int] = None
    aggregate_target_quantity: Optional[int] = None
    aggregate_quantity_progress: Optional[float] = None

    # 勾选类型：个人与汇总统计
    personal_is_completed: Optional[bool] = None
    personal_completion_count: Optional[int] = None
    completed_count: Optional[int] = None
    aggregate_checkbox_progress: Optional[float] = None

    class Config:
        from_attributes = True

class PaginatedTaskResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    size: int

# AI智能体相关schemas
class AIAgentCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    provider: str  # openrouter, openai, claude, gemini, deepseek
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    system_prompt: str
    user_prompt_template: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    is_active: bool = True
    is_default: bool = False


class AIAgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class AIAgentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    provider: str
    model_name: str
    base_url: Optional[str] = None
    system_prompt: str
    user_prompt_template: Optional[str] = None
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    is_active: bool
    is_default: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# AI功能相关schemas
class AIFunctionCreateRequest(BaseModel):
    name: str
    function_type: str  # emotion_analysis, reflection_generation, task_analysis, report_summary, knowledge_qa, custom
    description: Optional[str] = None
    agent_id: int
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    processing_config: Optional[Dict[str, Any]] = None
    is_active: bool = True


class AIFunctionUpdateRequest(BaseModel):
    name: Optional[str] = None
    function_type: Optional[str] = None
    description: Optional[str] = None
    agent_id: Optional[int] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    processing_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AIFunctionResponse(BaseModel):
    id: int
    name: str
    function_type: str
    description: Optional[str] = None
    agent_id: int
    agent_name: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    processing_config: Optional[Dict[str, Any]] = None
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# AI调用日志相关schemas
class AICallLogResponse(BaseModel):
    id: int
    function_id: int
    function_name: Optional[str] = None
    function_type: Optional[str] = None
    agent_id: int
    agent_name: Optional[str] = None
    user_id: int
    username: Optional[str] = None
    request_data: Dict[str, Any]
    request_tokens: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    response_tokens: Optional[int] = None
    status: str  # success, failed, timeout, rate_limited
    error_message: Optional[str] = None
    duration_ms: int
    cost: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# AI调用请求schema
class AICallRequest(BaseModel):
    function_id: int
    input_data: Dict[str, Any]


# AI调用响应schema
class AICallResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    call_log_id: Optional[int] = None


# AI统计信息schema
class AIStatsResponse(BaseModel):
    total_calls: int
    success_calls: int
    failed_calls: int
    success_rate: float
    avg_duration_ms: float
    total_cost: float
    calls_by_function: Dict[str, int]
    calls_by_status: Dict[str, int]
    recent_calls: List[AICallLogResponse]


# 分页响应schema
class PaginatedAICallLogResponse(BaseModel):
    items: List[AICallLogResponse]
    total: int
    page: int
    size: int

class UserCreateRequest(BaseModel):
    password: str
    username: str
    email: str
    role: str = "user"  # super_admin, admin, user
    identity_type: Optional[str] = None  # cc, ss, lp
    organization: Optional[str] = None
    group_id: Optional[int] = None

class UserUpdateRequest(BaseModel):
    role: Optional[str] = None
    identity_type: Optional[str] = None
    organization: Optional[str] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    identity_type: Optional[str] = None
    full_identity: str
    ai_knowledge_branch: str
    organization: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    is_active: bool
    is_admin: bool = False
    is_super_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str

class AuthResponse(BaseModel):
    message: str
    user: UserResponse


class DailyReportCreateRequest(BaseModel):
    work_date: date
    title: str
    content: str
    work_hours: Optional[float] = None
    task_progress: Optional[str] = None
    work_summary: Optional[str] = None
    mood_score: Optional[int] = None  # 1-10分
    efficiency_score: int  # 1-10分
    call_count: int = 0
    call_duration: int = 0  # 分钟
    achievements: Optional[str] = None
    challenges: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    # 任务卡片明细快照：前端在提交日报时附带的结构化任务数据
    tasks_snapshot: Optional[Dict[str, Any]] = None


class DailyReportUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    work_hours: Optional[float] = None
    task_progress: Optional[str] = None
    work_summary: Optional[str] = None
    mood_score: Optional[int] = None
    efficiency_score: Optional[int] = None
    call_count: Optional[int] = None
    call_duration: Optional[int] = None
    achievements: Optional[str] = None
    challenges: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    # 任务卡片明细快照（更新时可覆盖）
    tasks_snapshot: Optional[Dict[str, Any]] = None


class DailyReportResponse(BaseModel):
    id: int
    user_id: int
    work_date: date
    title: str
    content: str
    work_hours: Optional[float] = None
    task_progress: Optional[str] = None
    work_summary: Optional[str] = None
    mood_score: Optional[int] = None
    efficiency_score: int
    call_count: int
    call_duration: int
    achievements: Optional[str] = None
    challenges: Optional[str] = None
    tomorrow_plan: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 分页响应schema（必须在所有基础schema定义之后）
class PaginatedUserResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int

class PaginatedUserGroupResponse(BaseModel):
    items: List[UserGroupResponse]
    total: int
    page: int
    size: int

# 任务分页响应schema
class PaginatedTaskResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    size: int

# 组别成员管理schema
class AddMembersRequest(BaseModel):
    user_ids: List[int]

class RemoveMemberRequest(BaseModel):
    user_id: int

# AI设置相关schemas
class AISettingsCreateRequest(BaseModel):
    provider: str = "openai"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7

class AISettingsUpdateRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

class AISettingsResponse(BaseModel):
    id: int
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: str
    max_tokens: int
    temperature: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 系统设置相关schemas
class SystemSettingsCreateRequest(BaseModel):
    system_name: str = "OpSight运营洞察系统"
    timezone: str = "Asia/Shanghai"
    language: str = "zh-CN"
    auto_analysis: bool = True
    data_retention_days: int = 365

class SystemSettingsUpdateRequest(BaseModel):
    system_name: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    auto_analysis: Optional[bool] = None
    data_retention_days: Optional[int] = None

class SystemSettingsResponse(BaseModel):
    id: int
    system_name: str
    timezone: str
    language: str
    auto_analysis: bool
    data_retention_days: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Task-related schemas
from pydantic import Field
from pydantic import ConfigDict

class JielongParticipationCreate(BaseModel):
    # 兼容前端字段：id -> student_id，remark -> notes
    student_id: str = Field(alias="id")
    notes: Optional[str] = Field(default=None, alias="remark")
    intention: Optional[str] = None

    # 允许使用字段名或别名进行反序列化
    model_config = ConfigDict(populate_by_name=True)

class TaskProgressUpdate(BaseModel):
    value: float

# User schemas for compatibility
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    role: str = "user"
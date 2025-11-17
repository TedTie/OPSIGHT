from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, BigInteger, Text, Enum, JSON, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base
import enum

# 用户权限级别枚举
class UserRole(str, enum.Enum):
    USER = "user"           # 普通用户
    ADMIN = "admin"         # 管理员
    SUPER_ADMIN = "super_admin"  # 超级管理员

# 身份类型枚举 (用于AI知识库分支)
class IdentityType(str, enum.Enum):
    CC = "cc"              # 顾问 (Consultant)
    SS = "ss"              # 班主任 (Supervisor)
    LP = "lp"              # 英文辅导 (Language Partner)
    SA = "sa"              # 超级分析师 (Super Analyst) - 用于整体数据分析

# 任务状态枚举
class TaskStatus(str, enum.Enum):
    PENDING = "pending"      # 待处理
    PROCESSING = "processing" # 进行中
    DONE = "done"           # 已完成
    CANCELLED = "cancelled"  # 已取消

# 任务类型枚举
class TaskType(str, enum.Enum):
    AMOUNT = "amount"        # 金额任务
    QUANTITY = "quantity"    # 数量任务
    JIELONG = "jielong"      # 接龙任务
    CHECKBOX = "checkbox"    # 勾选任务

# 任务分配类型枚举
class TaskAssignmentType(str, enum.Enum):
    USER = "user"           # 指定用户
    GROUP = "group"         # 指定组
    IDENTITY = "identity"   # 指定身份
    ALL = "all"            # 所有人

# 优先级枚举
class TaskPriority(str, enum.Enum):
    URGENT = "urgent"      # 紧急
    HIGH = "high"         # 高
    MEDIUM = "medium"     # 中
    LOW = "low"          # 低

class UserGroup(Base):
    """用户组模型 - 组别是自定义名称，可包含不同身份类型的用户"""
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # 组别名称 (如: "1组", "2组", "北京分部")
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    members = relationship("User", back_populates="group")
    
    def get_members_by_identity(self, identity_type: str):
        """获取指定身份类型的组员"""
        return [member for member in self.members if member.identity_type == identity_type]
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "member_count": len(self.members),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    # 用于存储密码哈希（bcrypt），不返回到接口
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default='user')  # super_admin, admin, user
    identity_type = Column(String(10), nullable=True)  # cc, ss, lp (普通用户和管理员必须有身份类型)
    organization = Column(String(100), nullable=True)  # 组织名称
    group_id = Column(Integer, ForeignKey("user_groups.id"), nullable=True)  # 用户组ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    group = relationship("UserGroup", back_populates="members")

    @property
    def is_super_admin(self):
        """是否为超级管理员"""
        return self.role == 'super_admin'

    @property
    def is_admin(self):
        """是否为管理员（包括超级管理员）"""
        return self.role in ['admin', 'super_admin']

    @property
    def is_user(self):
        """是否为普通用户"""
        return self.role == 'user'

    def get_full_identity(self):
        """获取完整身份描述"""
        role_names = {
            'super_admin': '超级管理员',
            'admin': '管理员',
            'user': '普通用户'
        }
        identity_names = {
            'cc': 'CC(顾问)',
            'ss': 'SS(班主任)', 
            'lp': 'LP(英文辅导)',
            'sa': 'SA(超级分析师)'
        }
        
        role_name = role_names.get(self.role, self.role)
        if self.identity_type:
            identity_name = identity_names.get(self.identity_type, self.identity_type)
            return f"{role_name} - {identity_name}"
        return role_name

    def get_ai_knowledge_branch(self):
        """获取AI知识库分支"""
        if self.identity_type:
            if self.identity_type == "sa":
                return "ANALYTICS"  # SA身份使用分析分支，可访问所有数据
            return self.identity_type.upper()  # CC, SS, LP
        return "GENERAL"  # 通用分支

    def can_manage_users(self):
        """是否可以管理用户"""
        return self.is_super_admin

    def can_manage_tasks(self):
        """是否可以管理任务"""
        return self.is_admin

    def can_view_all_reports(self):
        """是否可以查看所有日报"""
        return self.is_admin

    def can_access_admin_panel(self):
        """是否可以访问管理面板"""
        return self.is_admin

    def can_manage_group(self, target_group_id: int = None):
        """是否可以管理指定组别"""
        if self.is_super_admin:
            return True
        if self.is_admin and target_group_id:
            # 管理员只能管理自己所在的组
            return self.group_id == target_group_id
        return False

    def has_permission(self, permission_type: str, scope: str = 'personal') -> bool:
        """
        检查用户是否有特定权限
        permission_type: 'task_assign', 'task_complete', 'report_manage', 'data_analysis', 'knowledge_base', 'profile'
        scope: 'personal', 'group', 'all'
        """
        if self.is_super_admin:
            return True

        if self.is_admin:
            admin_permissions = {
                'task_assign': ['group', 'all'],
                'task_complete': ['personal', 'group', 'all'],
                'report_manage': ['group', 'all'],
                'data_analysis': ['group', 'all'],
                'knowledge_base': ['personal', 'group', 'all'],
                'profile': ['personal']
            }
            return scope in admin_permissions.get(permission_type, [])

        if self.role == 'user':
            user_permissions = {
                'task_complete': ['personal'],
                'report_manage': ['personal'],
                'data_analysis': ['personal'],
                'profile': ['personal']
            }
            return scope in user_permissions.get(permission_type, [])

        return False

    def can_manage_ai(self) -> bool:
        """检查用户是否可以管理AI配置"""
        return self.is_super_admin or self.is_admin

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "identity_type": self.identity_type,
            "full_identity": self.get_full_identity(),
            "ai_knowledge_branch": self.get_ai_knowledge_branch(),
            "organization": self.organization,
            "group_id": self.group_id,
            "group_name": self.group.name if self.group else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}', identity_type='{self.identity_type}')>"


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 任务类型和标签
    # 兼容历史数据中的小写字符串值（amount/quantity/jielong/checkbox）
    task_type = Column(
        Enum(
            TaskType,
            values_callable=lambda e: [member.value for member in e]
        ),
        nullable=False,
        default=TaskType.CHECKBOX
    )
    tags = Column(JSON, nullable=True)  # 存储标签数组

    # 任务分配（兼容历史小写字符串）
    assignment_type = Column(
        Enum(
            TaskAssignmentType,
            values_callable=lambda e: [member.value for member in e]
        ),
        nullable=False
    )
    assigned_to = Column(BigInteger, ForeignKey("users.id"), nullable=True)  # 分配给特定用户
    target_group_id = Column(BigInteger, ForeignKey("user_groups.id"), nullable=True)  # 分配给特定组
    target_identity = Column(String(20), nullable=True)  # 分配给特定身份

    # 任务状态（兼容历史小写字符串）
    status = Column(
        Enum(
            TaskStatus,
            values_callable=lambda e: [member.value for member in e]
        ),
        default=TaskStatus.PENDING
    )
    priority = Column(
        Enum(
            TaskPriority,
            values_callable=lambda e: [member.value for member in e]
        ),
        default=TaskPriority.MEDIUM
    )  # 优先级

    # 任务类型特定字段
    # 金额类型
    target_amount = Column(Float, nullable=True)  # 目标金额
    current_amount = Column(Float, default=0.0)   # 当前金额

    # 数量类型
    target_quantity = Column(Integer, nullable=True)  # 目标数量
    current_quantity = Column(Integer, default=0)     # 当前数量

    # 接龙类型
    jielong_target_count = Column(Integer, nullable=True)  # 接龙目标数量
    jielong_current_count = Column(Integer, default=0)     # 当前接龙数量
    jielong_config = Column(JSON, nullable=True)           # 接龙配置（字段设置）

    # 勾选类型
    is_completed = Column(Boolean, default=False)  # 是否完成

    # 时间管理
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)

    # 创建信息
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系属性
    records = relationship("TaskRecord", back_populates="task", cascade="all, delete-orphan")
    jielong_records = relationship("JielongRecord", back_populates="task", cascade="all, delete-orphan")

    def is_assigned_to_user(self, user: "User") -> bool:
        """
        检查此任务是否对指定用户可见。
        注意：这里的 'user' 是一个 User ORM 对象。
        """
        # 情况1: 任务分配给所有人
        if self.assignment_type == TaskAssignmentType.ALL:
            return True

        # 情况2: 任务直接分配给该用户
        if self.assignment_type == TaskAssignmentType.USER:
            return self.assigned_to == user.id

        # 情况3: 任务分配给该用户所在的用户组
        if self.assignment_type == TaskAssignmentType.GROUP:
            return user.group_id is not None and self.target_group_id == user.group_id

        # 情况4: 任务分配给该用户的身份类型
        if self.assignment_type == TaskAssignmentType.IDENTITY:
            return user.identity_type is not None and self.target_identity == user.identity_type

        # 其他情况或数据不一致时，默认为不可见
        return False

    def get_progress_percentage(self) -> float:
        """获取任务进度百分比"""
        if self.task_type == TaskType.AMOUNT and self.target_amount:
            return min(100.0, (self.current_amount / self.target_amount) * 100)
        elif self.task_type == TaskType.QUANTITY and self.target_quantity:
            return min(100.0, (self.current_quantity / self.target_quantity) * 100)
        elif self.task_type == TaskType.JIELONG and self.jielong_target_count:
            return min(100.0, (self.jielong_current_count / self.jielong_target_count) * 100)
        elif self.task_type == TaskType.CHECKBOX:
            return 100.0 if self.is_completed else 0.0
        return 0.0

    def is_completed_auto(self) -> bool:
        """检查任务是否自动完成"""
        if self.task_type == TaskType.AMOUNT and self.target_amount:
            return self.current_amount >= self.target_amount
        elif self.task_type == TaskType.QUANTITY and self.target_quantity:
            return self.current_quantity >= self.target_quantity
        elif self.task_type == TaskType.JIELONG and self.jielong_target_count:
            return self.jielong_current_count >= self.jielong_target_count
        elif self.task_type == TaskType.CHECKBOX:
            return self.is_completed
        return False


class TaskJielongEntry(Base):
    """接龙任务参与记录"""
    __tablename__ = "task_jielong_entries"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    # 接龙数据
    entry_data = Column(JSON, nullable=False)  # 存储用户填写的接龙数据
    entry_order = Column(Integer, nullable=False)  # 接龙顺序

    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TaskCompletion(Base):
    """任务完成记录"""
    __tablename__ = "task_completions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    # 完成数据
    completion_data = Column(JSON, nullable=True)  # 存储完成时的数据
    completion_value = Column(Float, nullable=True)  # 完成的数值（金额/数量）
    is_completed = Column(Boolean, default=False)   # 是否完成

    # 时间信息
    completed_at = Column(DateTime(timezone=True), server_default=func.now())


class DailyReport(Base):
    """日报模型"""
    __tablename__ = "daily_reports"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # 基础信息
    work_date = Column(Date, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # 工作数据
    work_hours = Column(Float, nullable=False)
    task_progress = Column(Text, nullable=True)
    work_summary = Column(Text, nullable=True)
    
    # 评分数据
    mood_score = Column(Integer, nullable=False)  # 1-10分
    efficiency_score = Column(Integer, nullable=False)  # 1-10分
    
    # KPI数据
    call_count = Column(Integer, default=0)
    call_duration = Column(Integer, default=0)  # 分钟

    # 销售相关字段（用于数据分析）
    new_sign_count = Column(Integer, default=0)        # 新签单数
    new_sign_amount = Column(Float, default=0.0)       # 新签金额
    referral_count = Column(Integer, default=0)        # 转介绍单数（CC）
    referral_amount = Column(Float, default=0.0)       # 转介绍金额（CC）
    renewal_count = Column(Integer, default=0)         # 续费次数
    upgrade_count = Column(Integer, default=0)         # 升级次数
    renewal_amount = Column(Float, default=0.0)        # 续费金额（SS）
    upgrade_amount = Column(Float, default=0.0)        # 升舱金额（SS）
    
    # 反思数据
    achievements = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)
    tomorrow_plan = Column(Text, nullable=True)
    
    # AI分析结果
    ai_analysis = Column(JSON, nullable=True)
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def is_assigned_to_user(self, user: "User") -> bool:
        """检查此日报是否对指定用户可见（仅本人）。"""
        return self.user_id == (user.id if hasattr(user, "id") else None)

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "work_date": self.work_date.isoformat() if self.work_date else None,
            "title": self.title,
            "content": self.content,
            "work_hours": self.work_hours,
            "task_progress": self.task_progress,
            "work_summary": self.work_summary,
            "mood_score": self.mood_score,
            "efficiency_score": self.efficiency_score,
            "call_count": self.call_count,
            "call_duration": self.call_duration,
            "new_sign_count": self.new_sign_count,
            "new_sign_amount": self.new_sign_amount,
            "referral_count": self.referral_count,
            "referral_amount": self.referral_amount,
            "renewal_count": self.renewal_count,
            "renewal_amount": self.renewal_amount,
            "upgrade_count": self.upgrade_count,
            "upgrade_amount": self.upgrade_amount,
            "achievements": self.achievements,
            "challenges": self.challenges,
            "tomorrow_plan": self.tomorrow_plan,
            "ai_analysis": self.ai_analysis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AdminMetric(Base):
    """管理员指标模型"""
    __tablename__ = "admin_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True)  # 指标唯一键
    name = Column(String(200), nullable=False)              # 指标名称
    description = Column(Text, nullable=True)               # 说明
    identity_scope = Column(String(20), nullable=True)      # 视角：CC/SS/LP/ALL/CC_SS
    target_count = Column(Integer, nullable=True)           # 目标数量
    target_amount = Column(Float, nullable=True)            # 目标金额
    unit = Column(String(20), nullable=True)                # 单位：%、次、元
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "identity_scope": self.identity_scope,
            "target_count": self.target_count,
            "target_amount": self.target_amount,
            "unit": self.unit,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# AI功能类型枚举
class AIFunctionType(str, enum.Enum):
    EMOTION_ANALYSIS = "emotion_analysis"      # 情感分析
    REFLECTION_GENERATION = "reflection_generation"  # 反思生成
    TASK_ANALYSIS = "task_analysis"           # 任务分析
    REPORT_SUMMARY = "report_summary"         # 报告总结
    KNOWLEDGE_QA = "knowledge_qa"             # 知识问答
    CUSTOM = "custom"                         # 自定义功能

# AI模型提供商枚举
class AIProvider(str, enum.Enum):
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"

# 调用状态枚举
class CallStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class AIAgent(Base):
    """智能体配置模型"""
    __tablename__ = "ai_agents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # 智能体名称
    description = Column(Text, nullable=True)  # 描述
    
    # 模型配置
    provider = Column(Enum(AIProvider), nullable=False)  # 提供商
    model_name = Column(String(100), nullable=False)  # 模型名称
    api_key = Column(String(500), nullable=True)  # API密钥（加密存储）
    base_url = Column(String(200), nullable=True)  # API基础URL
    
    # 提示词配置
    system_prompt = Column(Text, nullable=False)  # 系统提示词
    user_prompt_template = Column(Text, nullable=True)  # 用户提示词模板
    
    # 模型参数
    temperature = Column(Float, default=0.7)  # 温度参数
    max_tokens = Column(Integer, default=1000)  # 最大token数
    top_p = Column(Float, default=1.0)  # top_p参数
    frequency_penalty = Column(Float, default=0.0)  # 频率惩罚
    presence_penalty = Column(Float, default=0.0)  # 存在惩罚
    
    # 状态和权限
    is_active = Column(Boolean, default=True)  # 是否启用
    is_default = Column(Boolean, default=False)  # 是否为默认智能体
    
    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "provider": self.provider,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AIFunction(Base):
    """AI功能配置模型"""
    __tablename__ = "ai_functions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # 功能名称
    function_type = Column(Enum(AIFunctionType), nullable=False)  # 功能类型
    description = Column(Text, nullable=True)  # 功能描述
    
    # 智能体配置
    agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=False)  # 关联的智能体
    
    # 功能配置
    input_schema = Column(JSON, nullable=True)  # 输入数据结构
    output_schema = Column(JSON, nullable=True)  # 输出数据结构
    processing_config = Column(JSON, nullable=True)  # 处理配置
    
    # 状态
    is_active = Column(Boolean, default=True)  # 是否启用
    
    # 创建信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    agent = relationship("AIAgent")

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "function_type": self.function_type,
            "description": self.description,
            "agent_id": self.agent_id,
            "agent_name": self.agent.name if self.agent else None,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "processing_config": self.processing_config,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AICallLog(Base):
    """AI调用日志模型"""
    __tablename__ = "ai_call_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 调用信息
    function_id = Column(Integer, ForeignKey("ai_functions.id"), nullable=False)  # AI功能
    agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=False)  # 智能体
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 调用用户
    
    # 请求信息
    request_data = Column(JSON, nullable=False)  # 请求数据
    request_tokens = Column(Integer, nullable=True)  # 请求token数
    
    # 响应信息
    response_data = Column(JSON, nullable=True)  # 响应数据
    response_tokens = Column(Integer, nullable=True)  # 响应token数
    
    # 调用结果
    status = Column(Enum(CallStatus), nullable=False)  # 调用状态
    error_message = Column(Text, nullable=True)  # 错误信息
    
    # 性能指标
    duration_ms = Column(Integer, nullable=False)  # 调用耗时（毫秒）
    cost = Column(Float, nullable=True)  # 调用成本
    
    # 时间信息
    started_at = Column(DateTime(timezone=True), nullable=False)  # 开始时间
    completed_at = Column(DateTime(timezone=True), nullable=True)  # 完成时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    function = relationship("AIFunction")
    agent = relationship("AIAgent")
    user = relationship("User")

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "function_id": self.function_id,
            "function_name": self.function.name if self.function else None,
            "function_type": self.function.function_type if self.function else None,
            "agent_id": self.agent_id,
            "agent_name": self.agent.name if self.agent else None,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "request_data": self.request_data,
            "request_tokens": self.request_tokens,
            "response_data": self.response_data,
            "response_tokens": self.response_tokens,
            "status": self.status,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "cost": self.cost,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class AISettings(Base):
    """AI设置模型"""
    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider = Column(String(50), nullable=False, default="openai")  # AI提供商
    api_key = Column(String(500), nullable=True)  # API密钥
    base_url = Column(String(500), nullable=True)  # API基础URL
    model_name = Column(String(100), nullable=False, default="gpt-3.5-turbo")  # 模型名称
    max_tokens = Column(Integer, nullable=False, default=2000)  # 最大token数
    temperature = Column(Float, nullable=False, default=0.7)  # 温度参数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "provider": self.provider,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class SystemSettings(Base):
    """系统设置模型"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    system_name = Column(String(100), nullable=False, default="OpSight运营洞察系统")  # 系统名称
    timezone = Column(String(50), nullable=False, default="Asia/Shanghai")  # 时区
    language = Column(String(10), nullable=False, default="zh-CN")  # 语言
    auto_analysis = Column(Boolean, nullable=False, default=True)  # 自动分析
    data_retention_days = Column(Integer, nullable=False, default=365)  # 数据保留天数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "system_name": self.system_name,
            "timezone": self.timezone,
            "language": self.language,
            "auto_analysis": self.auto_analysis,
            "data_retention_days": self.data_retention_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# --- 以下是需要追加到文件末尾的内容 ---
class TaskRecord(Base):
    """记录数量或金额任务的每次提交"""
    __tablename__ = "task_records"
    
    id = Column(Integer, primary_key=True, index=True)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    task = relationship("Task")
    owner = relationship("User")


class JielongRecord(Base):
    """记录接龙任务的每次参与详情"""
    __tablename__ = "jielong_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    notes = Column(String, nullable=True)
    intention = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    task = relationship("Task")
    owner = relationship("User")


class MonthlyGoal(Base):
    """月度目标模型：按身份与作用域设置当月目标（金额/人数）。"""
    __tablename__ = "monthly_goals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    identity_type = Column(String(10), nullable=False)  # CC / SS
    scope = Column(String(10), nullable=False)  # global / group / user
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    group_id = Column(Integer, ForeignKey("user_groups.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    amount_target = Column(Float, nullable=False, default=0.0)  # 金额目标（CC/SS）
    # 新增细分金额目标
    new_sign_target_amount = Column(Float, nullable=False, default=0.0)  # CC 新单目标金额
    referral_target_amount = Column(Float, nullable=False, default=0.0)  # CC 转介绍目标金额
    renewal_total_target_amount = Column(Float, nullable=False, default=0.0)  # SS 总续费目标金额（续费+升舱）
    renewal_target_count = Column(Integer, nullable=False, default=0)  # SS 续费人数目标
    upgrade_target_count = Column(Integer, nullable=False, default=0)  # SS 升舱人数目标
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "identity_type": self.identity_type,
            "scope": self.scope,
            "year": self.year,
            "month": self.month,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "amount_target": self.amount_target,
            "new_sign_target_amount": self.new_sign_target_amount,
            "referral_target_amount": self.referral_target_amount,
            "renewal_total_target_amount": self.renewal_total_target_amount,
            "renewal_target_count": self.renewal_target_count,
            "upgrade_target_count": self.upgrade_target_count,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# 通知已读记录：用于多端同步通知的已读状态
class NotificationRead(Base):
    __tablename__ = "notification_reads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    notification_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
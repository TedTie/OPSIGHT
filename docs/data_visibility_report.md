# OPSIGHT 数据内容与可见性审计报告

- 生成时间: `2025-11-04T15:29:52.707697`
- API基址: `http://127.0.0.1:8000/api/v1`
- 数据库文件: `backend\simple_app.db`

## 数据库内容概览（通过API）
- 用户总数: `3`
- 组织总数: `2`
- 任务总数: `10`
- 日报总数: `1`

## 数据库表记录数（直接读取SQLite）
- `users`: `3`
- `user_groups`: `2`
- `tasks`: `10`
- `daily_reports`: `1`
- `ai_call_logs`: `2`
- `ai_agents`: `1`
- `ai_functions`: `1`

## 全量清单（基础实体）
### 用户（users）
- 用户 `admin` (id=1) 角色=`super_admin` 身份=`sa` 组ID=`2`
- 用户 `jlpss-chenjianxiong` (id=2) 角色=`admin` 身份=`ss` 组ID=`1`
- 用户 `test_user` (id=3) 角色=`user` 身份=`ss` 组ID=`1`

### 组织（user_groups）
- 组织 `MYC-SS01Team` (id=1) 成员数=`None`
- 组织 `MYC-LP01Team` (id=2) 成员数=`None`

### 任务（tasks）
- 任务 `全员任务1 - 系统维护` (id=31) 类型=`CHECKBOX` 分配=`ALL` 状态=`PENDING`
- 任务 `全员任务2 - 安全培训` (id=32) 类型=`CHECKBOX` 分配=`ALL` 状态=`PENDING`
- 任务 `全员任务3 - 政策更新` (id=33) 类型=`CHECKBOX` 分配=`ALL` 状态=`PENDING`
- 任务 `全员任务4 - 年度总结` (id=34) 类型=`CHECKBOX` 分配=`ALL` 状态=`PENDING`
- 任务 `个人任务1 - 分配给admin` (id=35) 类型=`CHECKBOX` 分配=`USER` 状态=`PENDING`
- 任务 `个人任务2 - 分配给jlpss-chenjianxiong` (id=36) 类型=`CHECKBOX` 分配=`USER` 状态=`PENDING`
- 任务 `个人任务3 - 分配给test_user` (id=37) 类型=`CHECKBOX` 分配=`USER` 状态=`PENDING`
- 任务 `个人任务4 - 分配给admin` (id=38) 类型=`CHECKBOX` 分配=`USER` 状态=`PENDING`
- 任务 `组任务1 - MYC-SS01Team` (id=39) 类型=`CHECKBOX` 分配=`GROUP` 状态=`PENDING`
- 任务 `组任务2 - MYC-LP01Team` (id=40) 类型=`CHECKBOX` 分配=`GROUP` 状态=`PENDING`

### 日报（daily_reports）
- 日报 id=1 用户ID=`1` 日期=`2025-11-03` 标题=`更新后的测试日报`

## 各身份可见性审计
### 用户 `admin` (角色=`super_admin` 身份=`sa` 组ID=`2`)
- 可见任务数: `10` (分配类型分布: {"ALL": 4, "USER": 4, "GROUP": 2})
  - 任务 `全员任务1 - 系统维护` (id=31) 分配=`ALL`
  - 任务 `全员任务2 - 安全培训` (id=32) 分配=`ALL`
  - 任务 `全员任务3 - 政策更新` (id=33) 分配=`ALL`
  - 任务 `全员任务4 - 年度总结` (id=34) 分配=`ALL`
  - 任务 `个人任务1 - 分配给admin` (id=35) 分配=`USER`
  - 任务 `个人任务2 - 分配给jlpss-chenjianxiong` (id=36) 分配=`USER`
  - 任务 `个人任务3 - 分配给test_user` (id=37) 分配=`USER`
  - 任务 `个人任务4 - 分配给admin` (id=38) 分配=`USER`
  - 任务 `组任务1 - MYC-SS01Team` (id=39) 分配=`GROUP`
  - 任务 `组任务2 - MYC-LP01Team` (id=40) 分配=`GROUP`
- 可见日报数: `1`
  - 日报 id=1 用户ID=`1` 日期=`2025-11-03` 标题=`更新后的测试日报`
- 可见用户数: `3` (非管理员通常为0，或接口403)
- 可见组织数: `2`

### 用户 `jlpss-chenjianxiong` (角色=`admin` 身份=`ss` 组ID=`1`)
- 可见任务数: `10` (分配类型分布: {"ALL": 4, "USER": 4, "GROUP": 2})
  - 任务 `全员任务1 - 系统维护` (id=31) 分配=`ALL`
  - 任务 `全员任务2 - 安全培训` (id=32) 分配=`ALL`
  - 任务 `全员任务3 - 政策更新` (id=33) 分配=`ALL`
  - 任务 `全员任务4 - 年度总结` (id=34) 分配=`ALL`
  - 任务 `个人任务1 - 分配给admin` (id=35) 分配=`USER`
  - 任务 `个人任务2 - 分配给jlpss-chenjianxiong` (id=36) 分配=`USER`
  - 任务 `个人任务3 - 分配给test_user` (id=37) 分配=`USER`
  - 任务 `个人任务4 - 分配给admin` (id=38) 分配=`USER`
  - 任务 `组任务1 - MYC-SS01Team` (id=39) 分配=`GROUP`
  - 任务 `组任务2 - MYC-LP01Team` (id=40) 分配=`GROUP`
- 可见日报数: `1`
  - 日报 id=1 用户ID=`1` 日期=`2025-11-03` 标题=`更新后的测试日报`
- 可见用户数: `3` (非管理员通常为0，或接口403)
- 可见组织数: `2`

### 用户 `test_user` (角色=`user` 身份=`ss` 组ID=`1`)
- 可见任务数: `6` (分配类型分布: {"ALL": 4, "USER": 1, "GROUP": 1})
  - 任务 `全员任务1 - 系统维护` (id=31) 分配=`ALL`
  - 任务 `全员任务2 - 安全培训` (id=32) 分配=`ALL`
  - 任务 `全员任务3 - 政策更新` (id=33) 分配=`ALL`
  - 任务 `全员任务4 - 年度总结` (id=34) 分配=`ALL`
  - 任务 `个人任务3 - 分配给test_user` (id=37) 分配=`USER`
  - 任务 `组任务1 - MYC-SS01Team` (id=39) 分配=`GROUP`
- 可见日报数: `0`
- 可见用户数: `0` (非管理员通常为0，或接口403)
- 可见组织数: `2`

## 可见性规则说明（后端实现摘要）
- 管理员（`is_admin=True`）可见所有任务和所有用户；普通用户仅可见与自身相关的数据。
- 任务（Task）：普通用户可见以下之一：分配给自己（`assignment_type=user` 且 `assigned_to=当前用户`）、分配给所有人（`all`）、分配给所在组（`group` 且 `target_group_id=用户组ID`）、分配给其身份类型（`identity` 且 `target_identity=用户身份类型`）。
- 日报（DailyReport）：普通用户仅可见自己的日报；管理员可见全部。
- 用户列表（Users）：仅超级管理员可管理；普通用户不可见或403。
- 组织列表（Groups）：所有登录用户可见列表，更新/删除需要管理员权限。

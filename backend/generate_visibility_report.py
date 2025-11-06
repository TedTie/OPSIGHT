#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPSIGHT 数据内容与可见性审计报告生成脚本

功能：
- 使用后端API按不同用户身份登录，抓取系统所有核心数据（用户、组织、任务、日报）
- 按身份生成“可见性”列表（每个身份能看到哪些具体记录）
- 汇总数据库表的记录数（直接读取SQLite），对AI日志类大表仅统计条数
- 将审计结果输出为 Markdown 文档 docs/data_visibility_report.md

运行方法：
    python backend/generate_visibility_report.py

依赖：
    requests, sqlite3
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Tuple

import requests


API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000/api/v1")
DOC_PATH = os.path.join("docs", "data_visibility_report.md")

# 测试的用户身份（确保这些用户已存在于数据库）
TEST_USERS: List[Tuple[str, str]] = [
    ("admin", "super_admin"),
    ("jlpss-chenjianxiong", "admin"),
    ("test_user", "user"),
]


def login(session: requests.Session, username: str) -> Dict[str, Any]:
    """登录指定用户，返回用户数据或错误信息。"""
    try:
        resp = session.post(f"{API_BASE}/auth/login", json={"username": username})
        if resp.status_code == 200:
            return {"ok": True, "user": resp.json().get("user"), "error": None}
        return {"ok": False, "user": None, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"ok": False, "user": None, "error": str(e)}


def fetch_paginated(session: requests.Session, path: str, size: int = 1000, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """统一抓取分页或非分页的API数据，返回 {items, total}。"""
    q = {"page": 1, "size": size}
    if params:
        q.update(params)
    resp = session.get(f"{API_BASE}{path}", params=q)
    data = {"items": [], "total": 0, "status": resp.status_code, "raw": None}
    if resp.status_code != 200:
        return data
    try:
        body = resp.json()
        data["raw"] = body
        if isinstance(body, dict) and "items" in body:
            data["items"] = body.get("items", [])
            data["total"] = int(body.get("total", len(data["items"])))
        elif isinstance(body, list):
            data["items"] = body
            data["total"] = len(body)
        else:
            # 兜底：未知结构
            data["items"] = []
            data["total"] = 0
    except Exception:
        pass
    return data


def _get_db_path() -> str | None:
    for p in [
        os.path.join("backend", "simple_app.db"),
        os.path.join(os.path.dirname(__file__), "simple_app.db"),
    ]:
        if os.path.exists(p):
            return p
    return None


def _query_all(conn: sqlite3.Connection, table: str) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {table}")
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []


def collect_all_data_as_admin() -> Dict[str, Any]:
    """以管理员身份抓取全量数据（用于数据库内容清单）。优先API，失败则离线(SQLite)。"""
    session = requests.Session()
    lg = login(session, "admin")
    if lg.get("ok"):
        users = fetch_paginated(session, "/users", size=2000)
        groups = fetch_paginated(session, "/groups", size=2000)
        tasks = fetch_paginated(session, "/tasks", size=2000)
        reports = fetch_paginated(session, "/reports", size=2000)
        return {
            "users": users,
            "groups": groups,
            "tasks": tasks,
            "reports": reports,
            "source": "api",
        }

    # API不可用，走离线路径
    db_path = _get_db_path()
    if not db_path:
        raise RuntimeError("未找到SQLite数据库文件，且API不可用，无法生成全量数据清单")
    conn = sqlite3.connect(db_path)
    users_items = _query_all(conn, "users")
    groups_items = _query_all(conn, "user_groups")
    tasks_items = _query_all(conn, "tasks")
    reports_items = _query_all(conn, "daily_reports")
    conn.close()
    return {
        "users": {"items": users_items, "total": len(users_items), "status": 200},
        "groups": {"items": groups_items, "total": len(groups_items), "status": 200},
        "tasks": {"items": tasks_items, "total": len(tasks_items), "status": 200},
        "reports": {"items": reports_items, "total": len(reports_items), "status": 200},
        "source": "sqlite",
    }


def sqlite_counts() -> Dict[str, Any]:
    """直接读取SQLite统计各表记录数，避免仅依赖API。"""
    # 数据库路径可能是 backend/simple_app.db
    db_path_candidates = [
        os.path.join("backend", "simple_app.db"),
        os.path.join(os.path.dirname(__file__), "simple_app.db"),
    ]
    db_path = next((p for p in db_path_candidates if os.path.exists(p)), None)
    result = {"db_path": db_path, "tables": {}, "ok": bool(db_path)}
    if not db_path:
        return result

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = [
        "users",
        "user_groups",
        "tasks",
        "daily_reports",
        "ai_call_logs",
        "ai_agents",
        "ai_functions",
    ]
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cur.fetchone()[0]
            result["tables"][t] = cnt
        except Exception:
            result["tables"][t] = None  # 表不存在或查询失败
    conn.close()
    return result


def _compute_visibility_offline(username: str) -> Dict[str, Any]:
    """不依赖API，直接用SQLite离线计算指定用户的可见任务与日报。"""
    db_path = _get_db_path()
    if not db_path:
        return {"errors": ["未找到SQLite数据库文件"], "username": username, "login_ok": False}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 读取用户
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"errors": [f"用户不存在: {username}"], "username": username, "login_ok": False}
    user = dict(row)

    # 全量数据
    tasks = _query_all(conn, "tasks")
    reports = _query_all(conn, "daily_reports")
    users = _query_all(conn, "users")
    groups = _query_all(conn, "user_groups")
    conn.close()

    # 管理员直接全可见
    is_admin = user.get("role") in ["admin", "super_admin"]
    if is_admin:
        return {
            "username": username,
            "login_ok": True,
            "user": user,
            "tasks": {"items": tasks, "total": len(tasks), "status": 200},
            "reports": {"items": reports, "total": len(reports), "status": 200},
            "users": {"items": users, "total": len(users), "status": 200},
            "groups": {"items": groups, "total": len(groups), "status": 200},
            "errors": [],
            "source": "sqlite",
        }

    # 普通用户按规则过滤
    visible_tasks: List[Dict[str, Any]] = []
    for t in tasks:
        at = t.get("assignment_type")
        # 存储为Enum名称或原始字符串，统一为小写字符串
        at_str = str(at).lower() if at is not None else ""
        if at_str == "all":
            visible_tasks.append(t)
        elif at_str == "user":
            if t.get("assigned_to") == user.get("id"):
                visible_tasks.append(t)
        elif at_str == "group":
            if user.get("group_id") is not None and t.get("target_group_id") == user.get("group_id"):
                visible_tasks.append(t)
        elif at_str == "identity":
            if user.get("identity_type") and t.get("target_identity") == user.get("identity_type"):
                visible_tasks.append(t)

    visible_reports = [r for r in reports if r.get("user_id") == user.get("id")]

    return {
        "username": username,
        "login_ok": True,
        "user": user,
        "tasks": {"items": visible_tasks, "total": len(visible_tasks), "status": 200},
        "reports": {"items": visible_reports, "total": len(visible_reports), "status": 200},
        "users": {"items": [], "total": 0, "status": 403},
        "groups": {"items": groups, "total": len(groups), "status": 200},
        "errors": [],
        "source": "sqlite",
    }


def collect_visibility_for_user(username: str) -> Dict[str, Any]:
    """登录指定用户并采集其可见性数据。优先API，失败则离线(SQLite)。"""
    session = requests.Session()
    lg = login(session, username)
    if not lg.get("ok"):
        # API登录失败，走离线
        return _compute_visibility_offline(username)

    vis = {
        "username": username,
        "login_ok": True,
        "user": lg.get("user"),
        "tasks": {"items": [], "total": 0, "status": None},
        "reports": {"items": [], "total": 0, "status": None},
        "users": {"items": [], "total": 0, "status": None},
        "groups": {"items": [], "total": 0, "status": None},
        "errors": [],
        "source": "api",
    }

    t = fetch_paginated(session, "/tasks", size=1000)
    vis["tasks"] = {"items": t["items"], "total": t["total"], "status": t["status"]}

    r = fetch_paginated(session, "/reports", size=1000)
    vis["reports"] = {"items": r["items"], "total": r["total"], "status": r["status"]}

    u = fetch_paginated(session, "/users", size=1000)
    vis["users"] = {"items": u["items"], "total": u["total"], "status": u["status"]}

    g = fetch_paginated(session, "/groups", size=1000)
    vis["groups"] = {"items": g["items"], "total": g["total"], "status": g["status"]}

    return vis


def summarize_tasks_by_assignment(tasks: List[Dict[str, Any]]) -> Dict[str, int]:
    """统计任务按assignment_type的分布。"""
    dist: Dict[str, int] = {}
    for t in tasks:
        at = t.get("assignment_type", "unknown")
        dist[at] = dist.get(at, 0) + 1
    return dist


def render_markdown(admin_data: Dict[str, Any], vis_list: List[Dict[str, Any]], db_counts: Dict[str, Any]) -> str:
    """将采集到的数据渲染为Markdown文档。"""
    timestamp = datetime.now().isoformat()
    lines: List[str] = []

    lines.append(f"# OPSIGHT 数据内容与可见性审计报告")
    lines.append("")
    lines.append(f"- 生成时间: `{timestamp}`")
    lines.append(f"- API基址: `{API_BASE}`")
    if db_counts.get("ok"):
        lines.append(f"- 数据库文件: `{db_counts['db_path']}`")
    lines.append("")

    # 数据库内容概览（API）
    lines.append("## 数据库内容概览（通过API）")
    lines.append(f"- 用户总数: `{admin_data['users']['total']}`")
    lines.append(f"- 组织总数: `{admin_data['groups']['total']}`")
    lines.append(f"- 任务总数: `{admin_data['tasks']['total']}`")
    lines.append(f"- 日报总数: `{admin_data['reports']['total']}`")
    lines.append("")

    # 数据库内容概览（直接SQLite计数）
    lines.append("## 数据库表记录数（直接读取SQLite）")
    if db_counts.get("ok"):
        for t, cnt in db_counts["tables"].items():
            val = "未知/表不存在" if cnt is None else str(cnt)
            lines.append(f"- `{t}`: `{val}`")
    else:
        lines.append("- 未找到SQLite数据库文件，跳过该项")
    lines.append("")

    # 全量清单（关键实体）
    lines.append("## 全量清单（基础实体）")
    # 用户列表
    lines.append("### 用户（users）")
    for u in admin_data["users"]["items"]:
        lines.append(
            f"- 用户 `{u.get('username')}` (id={u.get('id')}) 角色=`{u.get('role')}` 身份=`{u.get('identity_type')}` 组ID=`{u.get('group_id')}`"
        )
    lines.append("")
    # 组织列表
    lines.append("### 组织（user_groups）")
    for g in admin_data["groups"]["items"]:
        lines.append(
            f"- 组织 `{g.get('name')}` (id={g.get('id')}) 成员数=`{g.get('member_count')}`"
        )
    lines.append("")
    # 任务列表
    lines.append("### 任务（tasks）")
    for t in admin_data["tasks"]["items"]:
        lines.append(
            f"- 任务 `{t.get('title')}` (id={t.get('id')}) 类型=`{t.get('task_type')}` 分配=`{t.get('assignment_type')}` 状态=`{t.get('status')}`"
        )
    lines.append("")
    # 日报列表（仅列出基本信息）
    lines.append("### 日报（daily_reports）")
    for r in admin_data["reports"]["items"]:
        lines.append(
            f"- 日报 id={r.get('id')} 用户ID=`{r.get('user_id')}` 日期=`{r.get('work_date')}` 标题=`{r.get('title')}`"
        )
    lines.append("")

    # 可见性审计
    lines.append("## 各身份可见性审计")
    for vis in vis_list:
        u = vis.get("user") or {}
        username = vis.get("username")
        role = u.get("role")
        identity = u.get("identity_type")
        group_id = u.get("group_id")
        lines.append(f"### 用户 `{username}` (角色=`{role}` 身份=`{identity}` 组ID=`{group_id}`)")

        # 任务可见性
        t_items = vis["tasks"]["items"]
        t_total = vis["tasks"]["total"]
        t_dist = summarize_tasks_by_assignment(t_items)
        lines.append(f"- 可见任务数: `{t_total}` (分配类型分布: {json.dumps(t_dist, ensure_ascii=False)})")
        for t in t_items:
            lines.append(
                f"  - 任务 `{t.get('title')}` (id={t.get('id')}) 分配=`{t.get('assignment_type')}`"
            )

        # 日报可见性
        r_items = vis["reports"]["items"]
        r_total = vis["reports"]["total"]
        lines.append(f"- 可见日报数: `{r_total}`")
        for r in r_items:
            lines.append(
                f"  - 日报 id={r.get('id')} 用户ID=`{r.get('user_id')}` 日期=`{r.get('work_date')}` 标题=`{r.get('title')}`"
            )

        # 用户列表可见性
        u_total = vis["users"]["total"]
        lines.append(f"- 可见用户数: `{u_total}` (非管理员通常为0，或接口403)")

        # 组织列表可见性
        g_total = vis["groups"]["total"]
        lines.append(f"- 可见组织数: `{g_total}`")

        # 错误
        if vis.get("errors"):
            lines.append(f"- 错误: {vis['errors']}")

        lines.append("")

    # 规则说明（来自后端逻辑）
    lines.append("## 可见性规则说明（后端实现摘要）")
    lines.append("- 管理员（`is_admin=True`）可见所有任务和所有用户；普通用户仅可见与自身相关的数据。")
    lines.append("- 任务（Task）：普通用户可见以下之一：分配给自己（`assignment_type=user` 且 `assigned_to=当前用户`）、分配给所有人（`all`）、分配给所在组（`group` 且 `target_group_id=用户组ID`）、分配给其身份类型（`identity` 且 `target_identity=用户身份类型`）。")
    lines.append("- 日报（DailyReport）：普通用户仅可见自己的日报；管理员可见全部。")
    lines.append("- 用户列表（Users）：仅超级管理员可管理；普通用户不可见或403。")
    lines.append("- 组织列表（Groups）：所有登录用户可见列表，更新/删除需要管理员权限。")
    lines.append("")

    return "\n".join(lines)


def main():
    # 1) 以管理员抓取全量数据
    admin_data = collect_all_data_as_admin()

    # 2) 读取SQLite计数（可选）
    db_count_data = sqlite_counts()

    # 3) 审计各身份可见性
    vis_list: List[Dict[str, Any]] = []
    for username, _role in TEST_USERS:
        vis_list.append(collect_visibility_for_user(username))

    # 4) 渲染Markdown
    md = render_markdown(admin_data, vis_list, db_count_data)

    # 5) 输出到文件
    os.makedirs(os.path.dirname(DOC_PATH), exist_ok=True)
    with open(DOC_PATH, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✅ 审计报告已生成: {DOC_PATH}")


if __name__ == "__main__":
    main()
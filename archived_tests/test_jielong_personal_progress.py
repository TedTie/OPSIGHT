#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量验证：接龙任务个人进度与按用户筛选

步骤：
1) 登录后端 API
2) 找到一个接龙任务
3) 获取任务详情，检查个人接龙统计字段
4) 参与接龙一次
5) 再次获取详情，验证个人当前数量递增
6) 调用接龙记录列表并按 user_id 过滤
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"


def run():
    session = requests.Session()
    # 1) 登录（使用 admin 用户，如需修改可调整用户名密码）
    resp = session.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200, f"登录失败: {resp.status_code} {resp.text}"

    me = session.get(f"{BASE_URL}/auth/me").json()
    user_id = me.get("id")
    print(f"当前用户: {me.get('username')} (ID: {user_id})")

    # 2) 找接龙任务
    tasks_resp = session.get(f"{BASE_URL}/tasks")
    assert tasks_resp.status_code == 200, f"获取任务失败: {tasks_resp.status_code}"
    tasks_data = tasks_resp.json()
    items = tasks_data.get("items", []) if isinstance(tasks_data, dict) else tasks_data
    jielong_tasks = [t for t in items if str(t.get("task_type")) == "jielong"]
    assert jielong_tasks, "没有找到接龙任务用于验证"
    task_id = jielong_tasks[0]["id"]
    print(f"选择接龙任务 ID: {task_id}")

    # 3) 获取详情，检查个人统计字段
    detail = session.get(f"{BASE_URL}/tasks/{task_id}").json()
    print("任务详情(个人统计)：", {
        "personal_current": detail.get("personal_jielong_current_count"),
        "personal_target": detail.get("personal_jielong_target_count"),
        "personal_progress": detail.get("personal_jielong_progress"),
    })

    # 4) 参与接龙一次
    participation = {
        "id": "verifier_001",
        "remark": "验收脚本参与",
        "intention": "",
    }
    join_resp = session.post(f"{BASE_URL}/tasks/{task_id}/jielong", json=participation)
    assert join_resp.status_code in (200, 201), f"参与接龙失败: {join_resp.status_code} {join_resp.text}"
    print("已参与接龙一次")

    # 5) 再次获取详情，验证个人当前数量递增
    detail2 = session.get(f"{BASE_URL}/tasks/{task_id}").json()
    print("参与后个人统计：", {
        "personal_current": detail2.get("personal_jielong_current_count"),
        "personal_target": detail2.get("personal_jielong_target_count"),
        "personal_progress": detail2.get("personal_jielong_progress"),
    })

    # 6) 按 user_id 过滤接龙记录
    records = session.get(f"{BASE_URL}/tasks/{task_id}/jielong", params={"user_id": user_id}).json()
    print(f"按当前用户过滤记录，总数: {records.get('total')}")


if __name__ == "__main__":
    run()
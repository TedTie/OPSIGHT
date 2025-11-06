#!/usr/bin/env python3
"""
手动验证：金额任务参与接口在不同分配类型下是否可用。
使用管理员账号登录后遍历任务，针对金额任务做一次参与。
"""

import requests
import sys


BASE_URL = "http://localhost:8000/api/v1"


def get_tasks(session):
    url = f"{BASE_URL}/tasks"
    resp = session.get(url)
    if resp.status_code != 200:
        print(f"❌ 获取任务失败: HTTP {resp.status_code} - {resp.text[:200]}")
        return []
    data = resp.json()
    # 兼容分页与非分页结构
    if isinstance(data, dict) and "items" in data:
        return data.get("items", [])
    if isinstance(data, list):
        return data
    return []


def participate_amount(session, task_id, amount=1.0):
    url = f"{BASE_URL}/task-sync/sync-task-to-report"
    payload = {"task_id": task_id, "amount": amount}
    resp = session.post(url, json=payload)
    return resp.status_code, resp.text[:200]

def put_progress(session, task_id, value=1.0):
    url = f"{BASE_URL}/tasks/{task_id}/progress"
    payload = {"value": value}
    resp = session.put(url, json=payload)
    return resp.status_code, resp.text[:200]


def main():
    session = requests.Session()
    login_resp = session.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    if login_resp.status_code != 200:
        print(f"❌ 登录失败: HTTP {login_resp.status_code} - {login_resp.text[:200]}")
        sys.exit(1)
    print("✅ 登录成功，开始测试金额任务参与…")

    tasks = get_tasks(session)
    if not tasks:
        print("⚠️ 没有任务可测")
        sys.exit(0)

    # 按分配类型分桶
    buckets = {"all": [], "group": [], "identity": [], "user": [], "other": []}
    for t in tasks:
        tt = str(t.get("task_type", "")).lower()
        at = str(t.get("assignment_type", "other")).lower()
        if tt == "amount":
            buckets.get(at, buckets["other"]).append(t)

    tested = 0
    for at in ["all", "group", "identity", "user", "other"]:
        if not buckets[at]:
            print(f"ℹ️ 无金额任务（{at}）可测")
            continue
        task = buckets[at][0]
        code, text = participate_amount(session, task["id"], amount=1.0)
        if code == 200:
            print(f"✅ 参与成功：任务#{task['id']}（{at}） [POST 快速参与]")
        else:
            print(f"❌ 参与失败：任务#{task['id']}（{at}） [POST] HTTP {code} - {text}")
            # 尝试使用 PUT /tasks/{id}/progress 作为回退验证
            code2, text2 = put_progress(session, task["id"], value=1.0)
            if code2 == 200:
                print(f"✅ 参与成功：任务#{task['id']}（{at}） [PUT 进度更新]")
            else:
                print(f"❌ 进度更新失败：任务#{task['id']}（{at}） [PUT] HTTP {code2} - {text2}")
        tested += 1

    if tested == 0:
        print("⚠️ 没有任何金额任务参与被测试到")
    else:
        print(f"📊 已测试 {tested} 个分配类型的金额任务参与")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
调试任务API的脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_task_api():
    """测试任务API"""
    print("🔍 调试任务API...")
    
    # 创建会话
    session = requests.Session()
    
    # 1. 登录超级管理员
    print("\n1. 登录超级管理员...")
    login_data = {"username": "admin"}
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"   登录响应状态: {response.status_code}")
    if response.status_code == 200:
        user_data = response.json()
        print(f"   用户信息: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
    else:
        print(f"   登录失败: {response.text}")
        return
    
    # 2. 获取任务列表
    print("\n2. 获取任务列表...")
    response = session.get(f"{BASE_URL}/tasks")
    print(f"   任务列表响应状态: {response.status_code}")
    if response.status_code == 200:
        tasks_data = response.json()
        print(f"   任务数据: {json.dumps(tasks_data, indent=2, ensure_ascii=False)}")
    else:
        print(f"   获取任务列表失败: {response.text}")
    
    # 3. 测试任务创建权限
    print("\n3. 测试任务创建权限...")
    test_task = {
        "title": "调试测试任务",
        "description": "用于调试的测试任务",
        "task_type": "checkbox",
        "priority": "medium",
        "assignment_type": "all"
    }
    response = session.post(f"{BASE_URL}/tasks", json=test_task)
    print(f"   任务创建响应状态: {response.status_code}")
    if response.status_code == 200:
        task_data = response.json()
        print(f"   创建的任务: {json.dumps(task_data, indent=2, ensure_ascii=False)}")
    else:
        print(f"   任务创建失败: {response.text}")

if __name__ == "__main__":
    test_task_api()
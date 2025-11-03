#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试普通用户是否能创建任务
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_user_create_task():
    """测试普通用户创建任务权限"""
    session = requests.Session()
    
    # 登录普通用户
    login_data = {
        "username": "user",
        "password": "123456"
    }
    
    print("登录普通用户...")
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"登录状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"登录失败: {response.text}")
        return
    
    # 获取用户信息
    user_info = session.get(f"{BASE_URL}/auth/me")
    if user_info.status_code == 200:
        user_data = user_info.json()
        print(f"用户信息: {user_data.get('username')} ({user_data.get('identity')})")
        print(f"用户角色: {user_data.get('role')}")
        print(f"is_admin: {user_data.get('is_admin')}")
    
    # 尝试创建任务
    test_task = {
        "title": f"普通用户测试任务 {datetime.now().strftime('%H%M%S')}",
        "description": "这是普通用户创建的测试任务",
        "task_type": "checkbox",
        "priority": "medium",
        "assignment_type": "all"
    }
    
    print("\n尝试创建任务...")
    response = session.post(f"{BASE_URL}/tasks", json=test_task)
    print(f"创建任务状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code in [200, 201]:
        print("❌ 普通用户能够创建任务 - 这是权限配置错误!")
        # 删除测试任务
        task_data = response.json()
        task_id = task_data.get('task_id') or task_data.get('id')
        if task_id:
            delete_response = session.delete(f"{BASE_URL}/tasks/{task_id}")
            print(f"删除测试任务: {delete_response.status_code}")
    elif response.status_code == 403:
        print("✅ 普通用户无法创建任务 - 权限配置正确!")
    else:
        print(f"❓ 意外的响应状态码: {response.status_code}")

if __name__ == "__main__":
    test_user_create_task()
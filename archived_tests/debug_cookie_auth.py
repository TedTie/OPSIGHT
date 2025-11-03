#!/usr/bin/env python3
"""
调试Cookie认证机制
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_cookie_auth():
    """测试Cookie认证机制"""
    session = requests.Session()
    
    print("🔍 测试Cookie认证机制")
    print("=" * 50)
    
    # 1. 登录超级管理员
    print("\n1️⃣ 登录超级管理员...")
    login_response = session.post(f"{BASE_URL}/auth/login", json={
        "username": "admin"
    })
    
    print(f"登录响应状态码: {login_response.status_code}")
    print(f"登录响应内容: {login_response.text}")
    print(f"登录响应Cookie: {login_response.cookies}")
    print(f"Session Cookie: {session.cookies}")
    
    if login_response.status_code == 200:
        # 2. 检查当前用户信息
        print("\n2️⃣ 获取当前用户信息...")
        me_response = session.get(f"{BASE_URL}/auth/me")
        print(f"用户信息响应状态码: {me_response.status_code}")
        print(f"用户信息响应内容: {me_response.text}")
        
        # 3. 获取任务列表
        print("\n3️⃣ 获取任务列表...")
        tasks_response = session.get(f"{BASE_URL}/tasks")
        print(f"任务列表响应状态码: {tasks_response.status_code}")
        print(f"任务列表响应内容: {tasks_response.text}")
        
        # 4. 手动设置Cookie再试一次
        print("\n4️⃣ 手动设置Cookie再试一次...")
        session.cookies.set('username', 'admin')
        tasks_response2 = session.get(f"{BASE_URL}/tasks")
        print(f"手动设置Cookie后任务列表响应状态码: {tasks_response2.status_code}")
        print(f"手动设置Cookie后任务列表响应内容: {tasks_response2.text}")
        
        # 5. 检查所有Cookie
        print(f"\n5️⃣ 当前所有Cookie:")
        for cookie in session.cookies:
            print(f"   {cookie.name}: {cookie.value}")
        
        # 6. 测试创建任务
        print("\n6️⃣ 测试创建任务...")
        create_response = session.post(f"{BASE_URL}/tasks", json={
            "title": "Cookie测试任务",
            "description": "测试Cookie认证的任务",
            "assignment_type": "all",
            "task_type": "checkbox",
            "task_config": {
                "options": ["选项1", "选项2"]
            }
        })
        print(f"创建任务响应状态码: {create_response.status_code}")
        print(f"创建任务响应内容: {create_response.text}")

if __name__ == "__main__":
    test_cookie_auth()
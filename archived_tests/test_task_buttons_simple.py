#!/usr/bin/env python3
"""
简单的任务按钮测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_task_buttons():
    """测试任务按钮功能"""
    print("登录超级管理员...")
    
    # 登录超级管理员
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    print(f"登录状态码: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return
    
    # 获取登录响应和cookies
    login_data = login_response.json()
    print(f"登录响应: {login_data}")
    
    # 创建会话并使用cookies进行认证
    session = requests.Session()
    # 复制登录响应的cookies到会话中
    session.cookies.update(login_response.cookies)
    
    print("\n获取任务列表...")
    tasks_response = session.get(f"{BASE_URL}/tasks")
    if tasks_response.status_code != 200:
        print(f"获取任务失败: {tasks_response.text}")
        return
    
    tasks_data = tasks_response.json()
    print(f"任务响应数据: {tasks_data}")
    
    # 处理不同的响应格式
    if isinstance(tasks_data, dict):
        tasks = tasks_data.get('items', []) or tasks_data.get('data', []) or []
    else:
        tasks = tasks_data if isinstance(tasks_data, list) else []
    
    print(f"找到 {len(tasks)} 个任务")
    
    # 测试不同类型的任务
    for task in tasks[:3]:  # 只测试前3个任务
        task_id = task['id']
        task_type = task['task_type']
        title = task['title']
        
        print(f"\n测试任务: {title} (ID: {task_id}, 类型: {task_type})")
        
        if task_type == 'checkbox':
            # 测试完成按钮
            print("  测试完成按钮...")
            response = session.post(f"{BASE_URL}/tasks/{task_id}/complete", json={
                "completion_data": {"completion_note": "测试完成"}
            })
            print(f"  完成按钮状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"  响应内容: {response.text}")
            else:
                print(f"  响应内容: {response.json()}")
        
        elif task_type == 'amount':
            # 测试金额参与按钮
            print("  测试金额参与按钮...")
            response = session.post(f"{BASE_URL}/tasks/{task_id}/amount", params={
                "amount": 100.0,
                "note": "测试金额参与"
            })
            print(f"  金额参与状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"  响应内容: {response.text}")
            else:
                print(f"  响应内容: {response.json()}")
        
        elif task_type == 'quantity':
            # 测试数量参与按钮
            print("  测试数量参与按钮...")
            response = session.post(f"{BASE_URL}/tasks/{task_id}/quantity", params={
                "quantity": 5,
                "note": "测试数量参与"
            })
            print(f"  数量参与状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"  响应内容: {response.text}")
            else:
                print(f"  响应内容: {response.json()}")
        
        elif task_type == 'jielong':
            # 测试接龙参与按钮
            print("  测试接龙参与按钮...")
            response = session.post(f"{BASE_URL}/tasks/{task_id}/jielong", json={
                "entry_data": {"name": "测试用户", "content": "测试接龙内容"}
            })
            print(f"  接龙参与状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"  响应内容: {response.text}")
            else:
                print(f"  响应内容: {response.json()}")
        
        # 测试编辑任务
        print("  测试编辑任务...")
        response = session.put(f"{BASE_URL}/tasks/{task_id}", json={
            "title": task.get('title'),
            "description": task.get('description'),
            "task_type": task.get('task_type'),
            "assignment_type": task.get('assignment_type', 'all')
        })
        print(f"  编辑任务状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"  响应内容: {response.text}")
        else:
            print(f"  响应内容: {response.json()}")

if __name__ == "__main__":
    test_task_buttons()
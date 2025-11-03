#!/usr/bin/env python3
"""
测试任务创建功能
"""

import requests
import json
from datetime import datetime, timedelta

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_task_creation():
    """测试任务创建功能"""
    
    print("=== 测试任务创建功能 ===\n")
    
    session = requests.Session()
    
    # 1. 登录管理员账户
    print("1. 登录管理员账户...")
    try:
        login_data = {"username": "jlpss-chenjianxiong"}
        response = session.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   登录成功: {user_info['user']['username']}")
            print(f"   角色: {user_info['user']['role']}")
            print(f"   是否管理员: {user_info['user']['is_admin']}")
            print(f"   所属组ID: {user_info['user']['group_id']}")
        else:
            print(f"   登录失败: {response.text}")
            return
            
    except Exception as e:
        print(f"   登录错误: {e}")
        return
    
    # 2. 获取用户列表
    print("\n2. 获取用户列表...")
    try:
        response = session.get(f"{API_BASE}/users")
        if response.status_code == 200:
            users_data = response.json()
            users = users_data.get('items', [])
            print(f"   成功获取 {len(users)} 个用户")
            if users:
                print("   可用用户:")
                for user in users:
                    print(f"     - {user['username']} (ID: {user['id']})")
        else:
            print(f"   获取用户列表失败: {response.text}")
            return
    except Exception as e:
        print(f"   获取用户列表错误: {e}")
        return
    
    # 3. 获取组列表
    print("\n3. 获取组列表...")
    try:
        response = session.get(f"{API_BASE}/groups")
        if response.status_code == 200:
            groups_data = response.json()
            groups = groups_data.get('items', [])
            print(f"   成功获取 {len(groups)} 个组")
            if groups:
                print("   可用组:")
                for group in groups:
                    print(f"     - {group['name']} (ID: {group['id']})")
        else:
            print(f"   获取组列表失败: {response.text}")
            return
    except Exception as e:
        print(f"   获取组列表错误: {e}")
        return
    
    # 4. 测试创建不同类型的任务
    test_tasks = [
        {
            "title": "测试勾选任务",
            "description": "这是一个测试勾选任务",
            "task_type": "checkbox",
            "priority": "medium",
            "assignment_type": "user",
            "assigned_user_ids": [users[0]['id']] if users else [],
            "due_date": (datetime.now() + timedelta(days=7)).isoformat()
        },
        {
            "title": "测试金额任务",
            "description": "这是一个测试金额任务",
            "task_type": "amount",
            "priority": "high",
            "assignment_type": "group",
            "assigned_group_ids": [groups[0]['id']] if groups else [],
            "target_amount": 1000.0,
            "due_date": (datetime.now() + timedelta(days=14)).isoformat()
        },
        {
            "title": "测试数量任务",
            "description": "这是一个测试数量任务",
            "task_type": "quantity",
            "priority": "low",
            "assignment_type": "all",
            "target_quantity": 50,
            "due_date": (datetime.now() + timedelta(days=10)).isoformat()
        }
    ]
    
    print("\n4. 测试创建任务...")
    for i, task_data in enumerate(test_tasks, 1):
        print(f"\n   测试任务 {i}: {task_data['title']}")
        try:
            response = session.post(f"{API_BASE}/tasks", json=task_data)
            print(f"   响应状态: {response.status_code}")
            
            if response.status_code == 200:
                task = response.json()
                task_id = task.get('id', '未知')
                print(f"   ✅ 任务创建成功: ID {task_id}")
                print(f"   响应数据: {task}")
            elif response.status_code == 422:
                error_detail = response.json()
                print(f"   ❌ 验证错误: {error_detail}")
            else:
                print(f"   ❌ 创建失败: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 创建错误: {e}")
    
    # 5. 获取任务列表验证
    print("\n5. 验证任务列表...")
    try:
        response = session.get(f"{API_BASE}/tasks")
        if response.status_code == 200:
            tasks_data = response.json()
            total_tasks = tasks_data.get('total', 0)
            print(f"   当前总任务数: {total_tasks}")
        else:
            print(f"   获取任务列表失败: {response.text}")
    except Exception as e:
        print(f"   获取任务列表错误: {e}")

if __name__ == "__main__":
    test_task_creation()
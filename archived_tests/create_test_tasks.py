#!/usr/bin/env python3
"""
创建测试任务数据
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def create_test_tasks():
    """创建测试任务数据"""
    print("🚀 开始创建测试任务数据...")
    print("=" * 50)
    
    session = requests.Session()
    
    # 1. 登录管理员账户
    print("📍 步骤1: 登录管理员账户")
    try:
        login_data = {"username": "admin"}  # 无密码登录
        response = session.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   ✅ 登录成功: {user_info['user']['username']}")
            print(f"   角色: {user_info['user']['role']}")
            print(f"   是否管理员: {user_info['user']['is_admin']}")
        else:
            print(f"   ❌ 登录失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 登录错误: {e}")
        return False
    
    # 2. 创建测试任务
    print("\n📍 步骤2: 创建测试任务")
    
    test_tasks = [
        {
            "title": "测试勾选任务",
            "description": "这是一个测试勾选任务，用于测试完成按钮",
            "task_type": "checkbox",
            "priority": "medium",
            "assignment_type": "all",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat()
        },
        {
            "title": "测试金额任务",
            "description": "这是一个测试金额任务，用于测试参与按钮",
            "task_type": "amount",
            "priority": "high",
            "assignment_type": "all",
            "target_amount": 1000.0,
            "due_date": (datetime.now() + timedelta(days=14)).isoformat()
        },
        {
            "title": "测试数量任务",
            "description": "这是一个测试数量任务，用于测试参与按钮",
            "task_type": "quantity",
            "priority": "low",
            "assignment_type": "all",
            "target_quantity": 50,
            "due_date": (datetime.now() + timedelta(days=10)).isoformat()
        },
        {
            "title": "测试接龙任务",
            "description": "这是一个测试接龙任务，用于测试接龙按钮",
            "task_type": "jielong",
            "priority": "medium",
            "assignment_type": "all",
            "jielong_target_count": 10,
            "jielong_config": {
                "id_enabled": True,
                "remark_enabled": True,
                "intention_enabled": False,
                "custom_field_enabled": False
            },
            "due_date": (datetime.now() + timedelta(days=21)).isoformat()
        }
    ]
    
    created_tasks = []
    
    for i, task_data in enumerate(test_tasks, 1):
        print(f"\n   任务 {i}: {task_data['title']}")
        try:
            response = session.post(f"{BASE_URL}/tasks", json=task_data)
            print(f"   响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                print(f"   ✅ 创建成功: ID {task_id}")
                created_tasks.append(task_id)
            else:
                print(f"   ❌ 创建失败: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 创建错误: {e}")
    
    # 3. 验证创建的任务
    print(f"\n📍 步骤3: 验证创建的任务")
    try:
        response = session.get(f"{BASE_URL}/tasks")
        if response.status_code == 200:
            tasks_data = response.json()
            
            # 处理不同的响应格式
            if isinstance(tasks_data, list):
                tasks = tasks_data
            elif isinstance(tasks_data, dict):
                tasks = tasks_data.get('items', tasks_data.get('data', []))
            else:
                tasks = []
            
            print(f"   ✅ 当前总任务数: {len(tasks)}")
            
            if tasks:
                print("   📋 任务列表:")
                for task in tasks:
                    print(f"     - {task.get('title')} (ID: {task.get('id')}, 类型: {task.get('task_type')})")
            
            return len(created_tasks) > 0
            
        else:
            print(f"   ❌ 获取任务列表失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 验证错误: {e}")
        return False

if __name__ == "__main__":
    success = create_test_tasks()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试任务创建完成！")
        print("✅ 现在可以进行权限测试了")
    else:
        print("❌ 测试任务创建失败")
        print("请检查后端服务和权限配置")
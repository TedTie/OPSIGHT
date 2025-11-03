#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务创建功能测试脚本
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_task_creation():
    """测试任务创建功能"""
    print("🧪 开始测试任务创建功能...")
    
    # 创建session来保持cookie
    session = requests.Session()
    
    # 1. 登录管理员
    print("\n1. 登录管理员...")
    login_response = session.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "123456"
    })
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        print(login_response.text)
        return
    
    login_data = login_response.json()
    print(f"✅ 登录成功，用户: {login_data['user']['username']}, 角色: {login_data['user']['role']}")
    
    # 2. 获取组列表
    print("\n2. 获取组列表...")
    groups_response = session.get(f"{BASE_URL}/groups")
    
    if groups_response.status_code != 200:
        print(f"❌ 获取组列表失败: {groups_response.status_code}")
        print(groups_response.text)
        return
    
    groups_data = groups_response.json()
    print(f"✅ 获取组数据成功")
    print(f"   数据类型: {type(groups_data)}")
    print(f"   数据内容: {groups_data}")
    
    # 处理不同的响应格式
    if isinstance(groups_data, list):
        groups = groups_data
    elif isinstance(groups_data, dict) and 'items' in groups_data:
        groups = groups_data['items']
    else:
        groups = []
    
    print(f"✅ 获取到 {len(groups)} 个组")
    for group in groups:
        if isinstance(group, dict):
            print(f"   - {group.get('name', 'Unknown')} (ID: {group.get('id', 'Unknown')})")
        else:
            print(f"   - {group}")
    
    # 3. 测试创建不同类型的任务
    test_tasks = [
        {
            "title": "测试勾选任务",
            "description": "这是一个测试勾选任务",
            "task_type": "checkbox",
            "assignment_type": "all",
            "priority": "medium"
        },
        {
            "title": "测试金额任务",
            "description": "这是一个测试金额任务",
            "task_type": "amount",
            "assignment_type": "user",
            "assigned_to": login_data['user']['id'],
            "priority": "high",
            "target_amount": 1000.0
        },
        {
            "title": "测试数量任务",
            "description": "这是一个测试数量任务",
            "task_type": "quantity",
            "assignment_type": "group",
            "target_group_id": groups[0].get('id') if groups and isinstance(groups[0], dict) else None,
            "priority": "urgent",
            "target_quantity": 50
        },
        {
            "title": "测试接龙任务",
            "description": "这是一个测试接龙任务",
            "task_type": "jielong",
            "assignment_type": "all",
            "priority": "low",
            "jielong_target_count": 20,
            "jielong_config": {
                "id_enabled": True,
                "remark_enabled": True,
                "intention_enabled": False,
                "custom_field_enabled": False
            }
        }
    ]
    
    created_tasks = []
    
    for i, task_data in enumerate(test_tasks, 1):
        print(f"\n3.{i} 创建{task_data['title']}...")
        
        # 添加截止日期
        task_data["due_date"] = (datetime.now() + timedelta(days=7)).isoformat()
        
        create_response = session.post(f"{BASE_URL}/tasks", params=task_data)
        
        if create_response.status_code == 200:
            result = create_response.json()
            print(f"✅ 任务创建成功，ID: {result['task_id']}")
            created_tasks.append(result['task_id'])
        else:
            print(f"❌ 任务创建失败: {create_response.status_code}")
            print(f"   错误信息: {create_response.text}")
    
    # 4. 验证创建的任务
    print(f"\n4. 验证创建的任务...")
    tasks_response = session.get(f"{BASE_URL}/tasks")
    
    if tasks_response.status_code == 200:
        tasks = tasks_response.json()
        print(f"✅ 获取到 {len(tasks.get('items', []))} 个任务")
        
        # 检查我们创建的任务是否在列表中
        task_ids = [task['id'] for task in tasks.get('items', [])]
        for task_id in created_tasks:
            if task_id in task_ids:
                print(f"   ✅ 任务 {task_id} 在列表中")
            else:
                print(f"   ❌ 任务 {task_id} 不在列表中")
    else:
        print(f"❌ 获取任务列表失败: {tasks_response.status_code}")
        print(tasks_response.text)
    
    # 5. 测试任务详情获取
    if created_tasks:
        print(f"\n5. 测试任务详情获取...")
        task_id = created_tasks[0]
        detail_response = session.get(f"{BASE_URL}/tasks/{task_id}")
        
        if detail_response.status_code == 200:
            task_detail = detail_response.json()
            print(f"✅ 获取任务详情成功:")
            print(f"   - 标题: {task_detail['title']}")
            print(f"   - 类型: {task_detail['task_type']}")
            print(f"   - 状态: {task_detail['status']}")
            print(f"   - 优先级: {task_detail['priority']}")
        else:
            print(f"❌ 获取任务详情失败: {detail_response.status_code}")
            print(detail_response.text)
    
    print(f"\n🎉 任务创建功能测试完成！")
    print(f"   成功创建 {len(created_tasks)} 个任务")

if __name__ == "__main__":
    test_task_creation()
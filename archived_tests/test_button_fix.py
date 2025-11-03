#!/usr/bin/env python3
"""
测试 Tasks.vue 按钮点击功能修复效果
"""

import requests
import json

def test_button_functions():
    """测试按钮功能是否正常工作"""
    
    base_url = "http://localhost:8000"
    
    # 登录获取会话
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    try:
        # 登录
        print("🔐 正在登录...")
        login_response = session.post(f"{base_url}/api/v1/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return False
        
        print("✅ 登录成功")
        
        # 获取任务列表
        print("📋 获取任务列表...")
        tasks_response = session.get(f"{base_url}/api/v1/tasks")
        
        if tasks_response.status_code != 200:
            print(f"❌ 获取任务失败: {tasks_response.status_code}")
            return False
        
        tasks_data = tasks_response.json()
        tasks = tasks_data.get('items', tasks_data) if isinstance(tasks_data, dict) else tasks_data
        
        print(f"✅ 获取到 {len(tasks)} 个任务")
        
        # 查找不同类型的任务进行测试
        amount_task = None
        quantity_task = None
        jielong_task = None
        
        for task in tasks:
            if task['task_type'] == 'amount' and not amount_task:
                amount_task = task
            elif task['task_type'] == 'quantity' and not quantity_task:
                quantity_task = task
            elif task['task_type'] == 'jielong' and not jielong_task:
                jielong_task = task
        
        # 测试金额任务参与
        if amount_task:
            print(f"💰 测试金额任务参与 (ID: {amount_task['id']})...")
            amount_response = session.post(
                f"{base_url}/api/v1/tasks/{amount_task['id']}/amount",
                params={"amount": 50.0}
            )
            print(f"   状态码: {amount_response.status_code}")
            if amount_response.status_code == 200:
                print("   ✅ 金额任务参与功能正常")
            else:
                print(f"   ❌ 金额任务参与失败: {amount_response.text}")
        
        # 测试数量任务参与
        if quantity_task:
            print(f"📊 测试数量任务参与 (ID: {quantity_task['id']})...")
            quantity_response = session.post(
                f"{base_url}/api/v1/tasks/{quantity_task['id']}/quantity",
                params={"quantity": 5}
            )
            print(f"   状态码: {quantity_response.status_code}")
            if quantity_response.status_code == 200:
                print("   ✅ 数量任务参与功能正常")
            else:
                print(f"   ❌ 数量任务参与失败: {quantity_response.text}")
        
        # 测试接龙任务参与
        if jielong_task:
            print(f"🔗 测试接龙任务参与 (ID: {jielong_task['id']})...")
            jielong_data = {
                "id": "test_user_123",
                "remark": "测试接龙参与",
                "intention": "",
                "custom_field": ""
            }
            jielong_response = session.post(
                f"{base_url}/api/v1/tasks/{jielong_task['id']}/jielong",
                json=jielong_data
            )
            print(f"   状态码: {jielong_response.status_code}")
            if jielong_response.status_code == 200:
                print("   ✅ 接龙任务参与功能正常")
            else:
                print(f"   ❌ 接龙任务参与失败: {jielong_response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == '__main__':
    print("🧪 开始测试按钮功能修复效果...")
    print("=" * 50)
    
    success = test_button_functions()
    
    print("=" * 50)
    if success:
        print("✅ 按钮功能测试完成")
        print("📝 注意: 这只是后端API测试，前端按钮点击功能需要在浏览器中验证")
    else:
        print("❌ 测试失败")
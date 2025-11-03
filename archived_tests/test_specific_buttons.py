#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完成、参与、接龙按钮的API调用
"""

import requests
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"

def test_button_apis():
    """测试按钮相关的API"""
    print("🔍 测试完成、参与、接龙按钮的API调用...")
    
    session = requests.Session()
    
    # 1. 登录
    print("\n🔐 测试登录...")
    try:
        login_response = session.post(f"{BASE_URL}/api/v1/auth/login", 
                                    json={"username": "admin"})
        if login_response.status_code == 200:
            print("✅ 登录成功")
            user_data = login_response.json()
            print(f"   用户: {user_data.get('username', 'N/A')}")
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            return
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return
    
    # 2. 获取任务列表
    print("\n📋 获取任务列表...")
    try:
        tasks_response = session.get(f"{BASE_URL}/api/v1/tasks")
        if tasks_response.status_code == 200:
            tasks_data = tasks_response.json()
            tasks = tasks_data.get('items', [])
            print(f"✅ 获取到 {len(tasks)} 个任务")
            
            if not tasks:
                print("⚠️  没有任务，创建测试任务...")
                # 创建测试任务
                test_tasks = [
                    {
                        "title": "测试勾选任务",
                        "description": "用于测试完成按钮",
                        "task_type": "checkbox",
                        "priority": 2,
                        "assignment_type": "all"
                    },
                    {
                        "title": "测试金额任务", 
                        "description": "用于测试参与按钮",
                        "task_type": "amount",
                        "target_amount": 1000.0,
                        "priority": 2,
                        "assignment_type": "all"
                    },
                    {
                        "title": "测试接龙任务",
                        "description": "用于测试接龙按钮", 
                        "task_type": "jielong",
                        "jielong_target_count": 10,
                        "jielong_config": {
                            "id_enabled": True,
                            "remark_enabled": True,
                            "intention_enabled": False,
                            "custom_field_enabled": False
                        },
                        "priority": 2,
                        "assignment_type": "all"
                    }
                ]
                
                for task_data in test_tasks:
                    create_response = session.post(f"{BASE_URL}/api/v1/tasks", json=task_data)
                    if create_response.status_code == 200:
                        print(f"✅ 创建任务: {task_data['title']}")
                    else:
                        print(f"❌ 创建任务失败: {create_response.status_code}")
                
                # 重新获取任务列表
                tasks_response = session.get(f"{BASE_URL}/api/v1/tasks")
                if tasks_response.status_code == 200:
                    tasks_data = tasks_response.json()
                    tasks = tasks_data.get('items', [])
                    print(f"✅ 重新获取到 {len(tasks)} 个任务")
        else:
            print(f"❌ 获取任务列表失败: {tasks_response.status_code}")
            return
    except Exception as e:
        print(f"❌ 获取任务列表异常: {e}")
        return
    
    # 3. 测试各种按钮API
    print("\n🔘 测试按钮API...")
    
    for task in tasks[:5]:  # 只测试前5个任务
        task_id = task['id']
        task_type = task['task_type']
        task_title = task['title']
        
        print(f"\n📝 测试任务: {task_title} (类型: {task_type})")
        
        if task_type == 'checkbox':
            # 测试完成按钮API
            print("  🔘 测试完成按钮...")
            try:
                # 测试切换完成状态
                complete_response = session.put(f"{BASE_URL}/api/v1/task-sync/sync-task-to-report/{task_id}", 
                                              json={"is_completed": True})
                if complete_response.status_code == 200:
                    print("  ✅ 完成按钮API正常")
                else:
                    print(f"  ❌ 完成按钮API失败: {complete_response.status_code}")
                    print(f"     响应: {complete_response.text}")
            except Exception as e:
                print(f"  ❌ 完成按钮API异常: {e}")
        
        elif task_type == 'amount':
            # 测试参与金额任务API
            print("  💰 测试参与金额任务...")
            try:
                participate_response = session.post(f"{BASE_URL}/api/v1/task-sync/sync-task-to-report", 
                                                  json={
                                                      "task_id": task_id,
                                                      "amount": 100.0,
                                                      "remark": "测试参与"
                                                  })
                if participate_response.status_code == 200:
                    print("  ✅ 参与金额任务API正常")
                else:
                    print(f"  ❌ 参与金额任务API失败: {participate_response.status_code}")
                    print(f"     响应: {participate_response.text}")
            except Exception as e:
                print(f"  ❌ 参与金额任务API异常: {e}")
        
        elif task_type == 'quantity':
            # 测试参与数量任务API
            print("  🔢 测试参与数量任务...")
            try:
                participate_response = session.post(f"{BASE_URL}/api/v1/task-sync/sync-task-to-report", 
                                                  json={
                                                      "task_id": task_id,
                                                      "quantity": 5,
                                                      "remark": "测试参与"
                                                  })
                if participate_response.status_code == 200:
                    print("  ✅ 参与数量任务API正常")
                else:
                    print(f"  ❌ 参与数量任务API失败: {participate_response.status_code}")
                    print(f"     响应: {participate_response.text}")
            except Exception as e:
                print(f"  ❌ 参与数量任务API异常: {e}")
        
        elif task_type == 'jielong':
            # 测试接龙任务API
            print("  🐉 测试接龙任务...")
            try:
                jielong_response = session.post(f"{BASE_URL}/api/v1/tasks/{task_id}/jielong", 
                                              json={
                                                  "remark": "测试接龙",
                                                  "intention": "",
                                                  "custom_field": ""
                                              })
                if jielong_response.status_code == 200:
                    print("  ✅ 接龙任务API正常")
                else:
                    print(f"  ❌ 接龙任务API失败: {jielong_response.status_code}")
                    print(f"     响应: {jielong_response.text}")
            except Exception as e:
                print(f"  ❌ 接龙任务API异常: {e}")
    
    # 4. 测试其他相关API
    print("\n🔍 测试其他相关API...")
    
    # 测试获取接龙记录
    jielong_tasks = [t for t in tasks if t['task_type'] == 'jielong']
    if jielong_tasks:
        task_id = jielong_tasks[0]['id']
        try:
            entries_response = session.get(f"{BASE_URL}/api/v1/tasks/{task_id}/jielong-entries")
            if entries_response.status_code == 200:
                print("✅ 获取接龙记录API正常")
            else:
                print(f"❌ 获取接龙记录API失败: {entries_response.status_code}")
        except Exception as e:
            print(f"❌ 获取接龙记录API异常: {e}")
    
    print("\n🎉 按钮API测试完成！")
    print("\n📝 建议检查项目：")
    print("   1. 检查浏览器开发者工具的Console标签页是否有JavaScript错误")
    print("   2. 检查Network标签页中按钮点击时的API请求")
    print("   3. 确认v-can指令是否正确注册和工作")
    print("   4. 检查任务权限是否正确配置")
    print("   5. 确认前端组件的事件绑定是否正确")

if __name__ == "__main__":
    test_button_apis()
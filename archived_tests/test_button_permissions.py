#!/usr/bin/env python3
"""
测试任务列表按钮权限和响应问题
"""

import requests
import json
from datetime import datetime, timedelta

# API配置
API_BASE = "http://localhost:8000/api/v1"

def test_user_permissions():
    """测试用户权限和任务数据"""
    print("🔍 测试用户权限和任务数据...")
    
    # 1. 登录获取token
    print("\n1. 登录系统...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    try:
        response = session.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get('access_token')
            session.headers.update({'Authorization': f'Bearer {token}'})
            print(f"   ✅ 登录成功")
        else:
            print(f"   ❌ 登录失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 登录错误: {e}")
        return False
    
    # 2. 获取当前用户信息
    print("\n2. 获取当前用户信息...")
    try:
        response = session.get(f"{API_BASE}/auth/me")
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ 用户信息获取成功")
            print(f"   👤 用户名: {user_data.get('username')}")
            print(f"   🔑 用户ID: {user_data.get('id')}")
            print(f"   👑 是否管理员: {user_data.get('is_admin')}")
            print(f"   🌟 是否超级管理员: {user_data.get('is_super_admin')}")
            print(f"   🏢 组ID: {user_data.get('group_id')}")
            print(f"   🎭 身份类型: {user_data.get('identity_type')}")
            current_user = user_data
        else:
            print(f"   ❌ 获取用户信息失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 获取用户信息错误: {e}")
        return False
    
    # 3. 获取任务列表
    print("\n3. 获取任务列表...")
    try:
        response = session.get(f"{API_BASE}/tasks")
        if response.status_code == 200:
            tasks_data = response.json()
            tasks = tasks_data.get('items', [])
            print(f"   ✅ 任务列表获取成功")
            print(f"   📊 任务总数: {len(tasks)}")
            
            if tasks:
                # 分析每个任务的权限
                print(f"\n4. 分析任务权限...")
                for i, task in enumerate(tasks[:5]):  # 只分析前5个任务
                    print(f"\n   📝 任务 {i+1}: {task.get('title', 'N/A')}")
                    print(f"      - ID: {task.get('id')}")
                    print(f"      - 类型: {task.get('task_type')}")
                    print(f"      - 状态: {task.get('status')}")
                    print(f"      - 创建者: {task.get('created_by')}")
                    print(f"      - 分配类型: {task.get('assignment_type')}")
                    print(f"      - 分配给: {task.get('assigned_to')}")
                    print(f"      - 目标组ID: {task.get('target_group_id')}")
                    print(f"      - 目标身份: {task.get('target_identity')}")
                    
                    # 权限检查
                    can_edit = check_edit_permission(current_user, task)
                    can_delete = check_delete_permission(current_user, task)
                    can_complete = check_complete_permission(current_user, task)
                    
                    print(f"      🔐 权限分析:")
                    print(f"         - 可编辑: {can_edit}")
                    print(f"         - 可删除: {can_delete}")
                    print(f"         - 可完成/参与: {can_complete}")
                    
                return True
            else:
                print(f"   ℹ️ 当前没有任务")
                return True
        else:
            print(f"   ❌ 获取任务列表失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 获取任务列表错误: {e}")
        return False

def check_edit_permission(user, task):
    """检查编辑权限"""
    # 管理员和超级管理员可以编辑所有任务
    if user.get('is_admin') or user.get('is_super_admin'):
        return True
    # 任务创建者可以编辑自己的任务
    return task.get('created_by') == user.get('id')

def check_delete_permission(user, task):
    """检查删除权限"""
    # 管理员和超级管理员可以删除所有任务
    if user.get('is_admin') or user.get('is_super_admin'):
        return True
    # 任务创建者可以删除自己的任务
    return task.get('created_by') == user.get('id')

def check_complete_permission(user, task):
    """检查完成/参与权限"""
    # 已完成的任务不能再完成
    if task.get('status') == 'completed':
        return False
    
    current_user_id = user.get('id')
    
    # 如果任务分配给所有人
    if task.get('assignment_type') == 'all':
        return True
    
    # 如果任务分配给特定用户
    if task.get('assignment_type') == 'user' and task.get('assigned_to') == current_user_id:
        return True
    
    # 如果任务分配给特定身份
    if task.get('assignment_type') == 'identity' and task.get('target_identity') == user.get('identity_type'):
        return True
    
    # 如果任务分配给用户组
    if task.get('assignment_type') == 'group' and task.get('target_group_id'):
        return user.get('group_id') == task.get('target_group_id')
    
    return False

def test_button_apis():
    """测试按钮相关的API端点"""
    print("\n🔧 测试按钮相关的API端点...")
    
    # 登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    try:
        response = session.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get('access_token')
            session.headers.update({'Authorization': f'Bearer {token}'})
            print("   ✅ 登录成功")
        else:
            print(f"   ❌ 登录失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 登录错误: {e}")
        return False
    
    # 测试各种API端点
    api_tests = [
        ("任务同步API", "GET", "/task-sync/"),
        ("任务详情API", "GET", "/tasks/1"),
        ("接龙API", "GET", "/tasks/1/jielong"),
    ]
    
    for name, method, endpoint in api_tests:
        try:
            if method == "GET":
                response = session.get(f"{API_BASE}{endpoint}")
            elif method == "POST":
                response = session.post(f"{API_BASE}{endpoint}", json={})
            
            print(f"   📡 {name}: {response.status_code}")
            if response.status_code >= 400:
                print(f"      ⚠️ 错误: {response.text[:100]}...")
        except Exception as e:
            print(f"   ❌ {name} 测试失败: {e}")

if __name__ == "__main__":
    print("🔧 开始测试任务列表按钮权限和响应...")
    
    # 测试用户权限
    permissions_ok = test_user_permissions()
    
    if permissions_ok:
        # 测试API端点
        test_button_apis()
        
        print("\n📋 问题排查建议:")
        print("1. 检查浏览器控制台是否有JavaScript错误")
        print("2. 检查网络请求是否正常")
        print("3. 检查权限指令v-can是否正确注册")
        print("4. 检查任务数据中的权限相关字段是否正确")
        print("5. 检查前端组件的事件绑定是否正确")
        
        print(f"\n🎯 下一步操作:")
        print("1. 打开浏览器开发者工具")
        print("2. 查看Console标签页的错误信息")
        print("3. 查看Network标签页的网络请求")
        print("4. 尝试点击按钮并观察是否有请求发出")
    else:
        print("\n❌ 权限测试失败，请检查后端服务")
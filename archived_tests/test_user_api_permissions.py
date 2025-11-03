#!/usr/bin/env python3
"""
测试用户API权限问题
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_user_permissions():
    """测试用户权限和API访问"""
    
    print("=== 测试用户API权限问题 ===\n")
    
    # 1. 测试登录
    print("1. 测试登录...")
    login_data = {"username": "admin"}
    
    session = requests.Session()
    
    try:
        response = session.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"   登录响应状态: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   登录成功: {user_info['user']['username']}")
            print(f"   用户角色: {user_info['user']['role']}")
            print(f"   是否管理员: {user_info['user']['is_admin']}")
            print(f"   是否超级管理员: {user_info['user']['is_super_admin']}")
        else:
            print(f"   登录失败: {response.text}")
            return
            
    except Exception as e:
        print(f"   登录错误: {e}")
        return
    
    # 2. 测试获取当前用户信息
    print("\n2. 测试获取当前用户信息...")
    try:
        response = session.get(f"{API_BASE}/auth/me")
        print(f"   响应状态: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   当前用户: {user_info['username']}")
            print(f"   用户权限: 管理员={user_info['is_admin']}, 超级管理员={user_info['is_super_admin']}")
        else:
            print(f"   获取用户信息失败: {response.text}")
            
    except Exception as e:
        print(f"   获取用户信息错误: {e}")
    
    # 3. 测试获取用户列表
    print("\n3. 测试获取用户列表...")
    try:
        response = session.get(f"{API_BASE}/users")
        print(f"   响应状态: {response.status_code}")
        
        if response.status_code == 200:
            users_data = response.json()
            print(f"   用户列表获取成功，共 {users_data.get('total', 0)} 个用户")
            if 'items' in users_data and users_data['items']:
                print("   前几个用户:")
                for user in users_data['items'][:3]:
                    print(f"     - {user['username']} ({user['role']})")
        elif response.status_code == 403:
            print(f"   权限不足: {response.text}")
            print("   这可能是导致前端'获取用户列表失败'的原因")
        else:
            print(f"   获取用户列表失败: {response.text}")
            
    except Exception as e:
        print(f"   获取用户列表错误: {e}")
    
    # 4. 测试获取组列表
    print("\n4. 测试获取组列表...")
    try:
        response = session.get(f"{API_BASE}/groups")
        print(f"   响应状态: {response.status_code}")
        
        if response.status_code == 200:
            groups_data = response.json()
            print(f"   组列表获取成功，共 {groups_data.get('total', 0)} 个组")
            if 'items' in groups_data and groups_data['items']:
                print("   组列表:")
                for group in groups_data['items']:
                    print(f"     - {group['name']}")
        else:
            print(f"   获取组列表失败: {response.text}")
            
    except Exception as e:
        print(f"   获取组列表错误: {e}")
    
    # 5. 检查数据库中的用户
    print("\n5. 检查数据库中的用户...")
    try:
        import sqlite3
        conn = sqlite3.connect('backend/simple_app.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, role, is_admin, is_super_admin FROM users")
        users = cursor.fetchall()
        
        print("   数据库中的用户:")
        for user in users:
            username, role, is_admin, is_super_admin = user
            print(f"     - {username}: role={role}, admin={bool(is_admin)}, super_admin={bool(is_super_admin)}")
        
        conn.close()
        
    except Exception as e:
        print(f"   查询数据库错误: {e}")

if __name__ == "__main__":
    test_user_permissions()
#!/usr/bin/env python3
"""
测试修改后的用户列表API权限
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_user_api_with_different_roles():
    """测试不同角色的用户API访问"""
    
    print("=== 测试修改后的用户列表API权限 ===\n")
    
    # 测试用户列表
    test_users = [
        {"username": "admin", "expected_role": "super_admin"},
        {"username": "jlpss-chenjianxiong", "expected_role": "admin"},
        {"username": "test_user", "expected_role": "user"}
    ]
    
    for test_user in test_users:
        username = test_user["username"]
        expected_role = test_user["expected_role"]
        
        print(f"--- 测试用户: {username} ({expected_role}) ---")
        
        session = requests.Session()
        
        # 1. 登录
        try:
            login_data = {"username": username}
            response = session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                user_info = response.json()
                print(f"   登录成功: {user_info['user']['username']}")
                print(f"   实际角色: {user_info['user']['role']}")
                print(f"   是否管理员: {user_info['user']['is_admin']}")
                print(f"   是否超级管理员: {user_info['user']['is_super_admin']}")
                print(f"   所属组ID: {user_info['user']['group_id']}")
            else:
                print(f"   登录失败: {response.text}")
                continue
                
        except Exception as e:
            print(f"   登录错误: {e}")
            continue
        
        # 2. 测试用户列表API
        try:
            response = session.get(f"{API_BASE}/users")
            print(f"   用户列表API响应状态: {response.status_code}")
            
            if response.status_code == 200:
                users_data = response.json()
                total_users = users_data.get('total', 0)
                print(f"   可访问的用户数量: {total_users}")
                
                if 'items' in users_data and users_data['items']:
                    print("   可访问的用户:")
                    for user in users_data['items']:
                        print(f"     - {user['username']} (组ID: {user['group_id']})")
            elif response.status_code == 403:
                print(f"   权限不足: {response.json().get('detail', '未知错误')}")
            else:
                print(f"   API调用失败: {response.text}")
                
        except Exception as e:
            print(f"   用户列表API错误: {e}")
        
        print()

if __name__ == "__main__":
    test_user_api_with_different_roles()
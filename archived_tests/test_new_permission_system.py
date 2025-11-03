#!/usr/bin/env python3
"""
测试新的权限系统API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """测试登录"""
    print("=== 测试登录 ===")
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                           json={"username": "admin"})
    print(f"登录响应: {response.status_code}")
    if response.status_code == 200:
        print(f"登录成功: {response.json()}")
        return response.cookies
    else:
        print(f"登录失败: {response.text}")
        return None

def test_current_user(cookies):
    """测试获取当前用户信息"""
    print("\n=== 测试获取当前用户信息 ===")
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", cookies=cookies)
    print(f"获取用户信息响应: {response.status_code}")
    if response.status_code == 200:
        user_info = response.json()
        print(f"用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
        return user_info
    else:
        print(f"获取用户信息失败: {response.text}")
        return None

def test_create_group(cookies):
    """测试创建用户组"""
    print("\n=== 测试创建用户组 ===")
    group_data = {
        "name": "测试组",
        "description": "这是一个测试用户组"
    }
    response = requests.post(f"{BASE_URL}/api/v1/groups", 
                           json=group_data, cookies=cookies)
    print(f"创建用户组响应: {response.status_code}")
    if response.status_code == 200:
        group_info = response.json()
        print(f"创建的用户组: {json.dumps(group_info, indent=2, ensure_ascii=False)}")
        return group_info
    else:
        print(f"创建用户组失败: {response.text}")
        return None

def test_list_groups(cookies):
    """测试列出用户组"""
    print("\n=== 测试列出用户组 ===")
    response = requests.get(f"{BASE_URL}/api/v1/groups", cookies=cookies)
    print(f"列出用户组响应: {response.status_code}")
    if response.status_code == 200:
        groups = response.json()
        print(f"用户组列表: {json.dumps(groups, indent=2, ensure_ascii=False)}")
        return groups
    else:
        print(f"列出用户组失败: {response.text}")
        return None

def test_create_user(cookies, group_id=None):
    """测试创建用户"""
    print("\n=== 测试创建用户 ===")
    user_data = {
        "username": "test_user",
        "role": "user",
        "identity_type": "SS",
        "organization": "测试部门",
        "group_id": group_id
    }
    response = requests.post(f"{BASE_URL}/api/v1/users", 
                           json=user_data, cookies=cookies)
    print(f"创建用户响应: {response.status_code}")
    if response.status_code == 200:
        user_info = response.json()
        print(f"创建的用户: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
        return user_info
    else:
        print(f"创建用户失败: {response.text}")
        return None

def test_list_users(cookies):
    """测试列出用户"""
    print("\n=== 测试列出用户 ===")
    response = requests.get(f"{BASE_URL}/api/v1/users", cookies=cookies)
    print(f"列出用户响应: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"用户列表: {json.dumps(users, indent=2, ensure_ascii=False)}")
        return users
    else:
        print(f"列出用户失败: {response.text}")
        return None

def main():
    """主测试函数"""
    print("开始测试新的权限系统...")
    
    # 1. 测试登录
    cookies = test_login()
    if not cookies:
        print("登录失败，无法继续测试")
        return
    
    # 2. 测试获取当前用户信息
    user_info = test_current_user(cookies)
    if not user_info:
        print("获取用户信息失败")
        return
    
    # 3. 测试创建用户组
    group_info = test_create_group(cookies)
    group_id = group_info.get('id') if group_info else None
    
    # 4. 测试列出用户组
    test_list_groups(cookies)
    
    # 5. 测试创建用户
    test_create_user(cookies, group_id)
    
    # 6. 测试列出用户
    test_list_users(cookies)
    
    print("\n✅ 权限系统测试完成！")

if __name__ == "__main__":
    main()
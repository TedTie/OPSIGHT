#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的用户
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

def check_users():
    """检查系统中的用户"""
    session = requests.Session()
    
    # 先登录超级管理员
    login_data = {
        "username": "admin",
        "password": "123456"
    }
    
    print("登录超级管理员...")
    response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"登录状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"登录失败: {response.text}")
        return
    
    # 获取所有用户
    print("\n获取所有用户...")
    response = session.get(f"{BASE_URL}/users")
    print(f"获取用户状态码: {response.status_code}")
    
    if response.status_code == 200:
        users_data = response.json()
        print(f"响应数据类型: {type(users_data)}")
        print(f"响应内容: {users_data}")
        
        if isinstance(users_data, list):
            users = users_data
        elif isinstance(users_data, dict) and 'items' in users_data:
            users = users_data['items']
        else:
            users = []
            
        print(f"用户总数: {len(users)}")
        for user in users:
            if isinstance(user, dict):
                print(f"- 用户名: {user.get('username')}, 身份: {user.get('identity')}, 角色: {user.get('role')}, 管理员: {user.get('is_admin')}")
            else:
                print(f"- 用户数据: {user}")
    else:
        print(f"获取用户失败: {response.text}")

if __name__ == "__main__":
    check_users()
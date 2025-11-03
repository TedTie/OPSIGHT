#!/usr/bin/env python3
"""
测试前端认证状态
"""

import requests
import json

# 配置
FRONTEND_URL = "http://localhost:3001"
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1"

def test_frontend_auth_state():
    """测试前端认证状态"""
    
    print("=== 测试前端认证状态 ===\n")
    
    # 1. 直接测试后端API（模拟前端请求）
    print("1. 测试后端API认证状态...")
    
    session = requests.Session()
    
    # 检查认证状态
    try:
        response = session.get(f"{API_BASE}/auth/check")
        print(f"   认证检查响应: {response.status_code}")
        print(f"   认证状态: {response.json()}")
        
        if not response.json().get('authenticated', False):
            print("   用户未登录，尝试登录...")
            
            # 登录
            login_data = {"username": "admin"}
            login_response = session.post(f"{API_BASE}/auth/login", json=login_data)
            print(f"   登录响应: {login_response.status_code}")
            
            if login_response.status_code == 200:
                print("   登录成功")
                # 再次检查认证状态
                auth_check = session.get(f"{API_BASE}/auth/check")
                print(f"   登录后认证状态: {auth_check.json()}")
            else:
                print(f"   登录失败: {login_response.text}")
                return
        
    except Exception as e:
        print(f"   认证检查错误: {e}")
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
    
    # 3. 测试用户列表API（使用相同的session）
    print("\n3. 测试用户列表API...")
    try:
        response = session.get(f"{API_BASE}/users")
        print(f"   响应状态: {response.status_code}")
        
        if response.status_code == 200:
            users_data = response.json()
            print(f"   用户列表获取成功，共 {users_data.get('total', 0)} 个用户")
        elif response.status_code == 403:
            print(f"   权限不足: {response.text}")
        else:
            print(f"   获取用户列表失败: {response.text}")
            
    except Exception as e:
        print(f"   获取用户列表错误: {e}")
    
    # 4. 检查cookie
    print("\n4. 检查session cookies...")
    print(f"   Session cookies: {dict(session.cookies)}")
    
    # 5. 测试前端代理
    print("\n5. 测试前端代理...")
    try:
        # 通过前端代理访问API
        proxy_session = requests.Session()
        
        # 先登录
        login_response = proxy_session.post(f"{FRONTEND_URL}/api/v1/auth/login", json={"username": "admin"})
        print(f"   通过代理登录响应: {login_response.status_code}")
        
        if login_response.status_code == 200:
            # 测试用户列表
            users_response = proxy_session.get(f"{FRONTEND_URL}/api/v1/users")
            print(f"   通过代理获取用户列表响应: {users_response.status_code}")
            
            if users_response.status_code == 403:
                print("   通过代理也是403，说明认证有问题")
            elif users_response.status_code == 200:
                print("   通过代理成功获取用户列表")
            else:
                print(f"   通过代理获取用户列表失败: {users_response.text}")
        
    except Exception as e:
        print(f"   测试前端代理错误: {e}")

if __name__ == "__main__":
    test_frontend_auth_state()
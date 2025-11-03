#!/usr/bin/env python3
"""
调试认证问题
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def debug_auth():
    """调试认证"""
    print("=== 测试登录 ===")
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                           json={"username": "admin"})
    print(f"登录响应: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code != 200:
        return
    
    cookies = response.cookies
    print(f"Cookies: {dict(cookies)}")
    
    print("\n=== 测试获取当前用户信息 ===")
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", cookies=cookies)
    print(f"获取用户信息响应: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"用户角色: {user_data.get('role')}")
        print(f"是否管理员: {user_data.get('role') in ['admin', 'super_admin']}")
    
    print("\n=== 测试用户组API（带详细错误信息）===")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/groups", cookies=cookies)
        print(f"获取用户组列表响应: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 500:
            print("服务器内部错误，可能是数据库或代码问题")
        elif response.status_code == 403:
            print("权限不足")
        elif response.status_code == 404:
            print("路由未找到")
            
    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    debug_auth()
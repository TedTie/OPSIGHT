#!/usr/bin/env python3
"""
简单的API测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    """测试API"""
    print("=== 测试基本连接 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"健康检查响应: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"连接失败: {e}")
        return
    
    print("\n=== 测试登录 ===")
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                           json={"username": "admin"})
    print(f"登录响应: {response.status_code}")
    if response.status_code != 200:
        print(f"登录失败: {response.text}")
        return
    
    cookies = response.cookies
    print("登录成功")
    print(f"Cookies: {dict(cookies)}")
    
    print("\n=== 测试用户组API ===")
    # 测试获取用户组列表
    print("发送请求到: /api/v1/groups")
    response = requests.get(f"{BASE_URL}/api/v1/groups", cookies=cookies)
    print(f"获取用户组列表响应: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text}")
    
    # 测试创建用户组
    print("\n发送POST请求到: /api/v1/groups")
    group_data = {"name": "测试组", "description": "测试描述"}
    response = requests.post(f"{BASE_URL}/api/v1/groups", 
                           json=group_data, cookies=cookies)
    print(f"创建用户组响应: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text}")

if __name__ == "__main__":
    test_api()
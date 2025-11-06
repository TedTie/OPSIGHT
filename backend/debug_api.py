#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 API 测试脚本
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoint(method, endpoint, data=None, cookies=None):
    """测试单个API端点"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"测试: {method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, cookies=cookies)
        elif method == "POST":
            response = requests.post(url, json=data, cookies=cookies)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"成功响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
            except:
                print(f"响应内容: {response.text[:500]}...")
        else:
            print(f"错误响应: {response.text}")
            
        return response
        
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def main():
    print("开始调试 API 测试")
    
    # 1. 先登录获取会话
    print("\n1. 登录获取会话")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_response = test_api_endpoint("POST", "/api/v1/auth/login", login_data)
    
    if not login_response or login_response.status_code != 200:
        print("登录失败，无法继续测试")
        return
    
    # 获取会话cookies
    cookies = login_response.cookies
    print(f"获取到的cookies: {dict(cookies)}")
    
    # 2. 测试获取当前用户信息
    print("\n2. 测试获取当前用户信息")
    test_api_endpoint("GET", "/api/v1/auth/me", cookies=cookies)
    
    # 3. 测试获取用户分组
    print("\n3. 测试获取用户分组")
    test_api_endpoint("GET", "/api/v1/groups", cookies=cookies)

if __name__ == "__main__":
    main()
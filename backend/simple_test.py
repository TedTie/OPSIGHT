#!/usr/bin/env python3
"""
简单的 API 测试脚本
逐个测试 API 端点以诊断问题
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_single_endpoint(url, method="GET", data=None, cookies=None):
    """测试单个端点"""
    try:
        if method == "GET":
            response = requests.get(url, cookies=cookies)
        elif method == "POST":
            response = requests.post(url, json=data, cookies=cookies)
        
        print(f"{method} {url}: {response.status_code}")
        if response.status_code != 200:
            print(f"  错误: {response.text}")
        else:
            try:
                result = response.json()
                print(f"  成功: {json.dumps(result, indent=2, ensure_ascii=False)[:200]}...")
            except:
                print(f"  成功: {response.text[:200]}...")
        return response
    except Exception as e:
        print(f"{method} {url}: 异常 - {e}")
        return None

def main():
    print("=" * 50)
    print("简单 API 测试")
    print("=" * 50)
    
    # 1. 健康检查
    test_single_endpoint(f"{BASE_URL}/")
    
    # 2. 登录
    login_data = {"username": "admin", "password": "admin123"}
    login_response = test_single_endpoint(f"{BASE_URL}/api/v1/auth/login", "POST", login_data)
    
    if login_response and login_response.status_code == 200:
        cookies = login_response.cookies
        
        # 3. 测试获取当前用户信息
        test_single_endpoint(f"{BASE_URL}/api/v1/auth/me", cookies=cookies)
        
        # 4. 测试用户分组
        test_single_endpoint(f"{BASE_URL}/api/v1/groups", cookies=cookies)
        
        # 5. 测试任务列表
        test_single_endpoint(f"{BASE_URL}/api/v1/tasks", cookies=cookies)

if __name__ == "__main__":
    main()
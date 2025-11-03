#!/usr/bin/env python3
"""
调试API路径问题
"""

import requests

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """测试各种API端点"""
    endpoints = [
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/api/v1/auth/simple/login",
        "/auth/simple/login",
        "/api/auth/simple/login",
        "/simple/login",
        "/login"
    ]
    
    print("🔍 测试API端点可访问性")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=5)
            status = f"✅ {response.status_code}" if response.status_code < 400 else f"❌ {response.status_code}"
            print(f"{status} {endpoint}")
            
            # 如果是200，显示部分内容
            if response.status_code == 200:
                content = response.text[:100].replace('\n', ' ')
                print(f"     内容: {content}...")
                
        except Exception as e:
            print(f"❌ ERR {endpoint} - {str(e)}")
    
    print("\n🔍 测试POST请求到登录端点")
    print("=" * 50)
    
    login_endpoints = [
        "/api/v1/auth/simple/login",
        "/auth/simple/login",
        "/api/auth/simple/login"
    ]
    
    login_data = {"username": "admin", "password": "admin123"}
    
    for endpoint in login_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.post(url, json=login_data, timeout=5)
            status = f"✅ {response.status_code}" if response.status_code < 400 else f"❌ {response.status_code}"
            print(f"{status} POST {endpoint}")
            
            if response.status_code != 404:
                print(f"     响应: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ ERR POST {endpoint} - {str(e)}")

if __name__ == "__main__":
    test_endpoints()
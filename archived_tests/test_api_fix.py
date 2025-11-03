#!/usr/bin/env python3
"""
简单的API连接测试脚本
测试修复后的API路径是否正常工作
"""

import requests
import json

def test_api_endpoints():
    base_url = "http://localhost:8000"
    
    print("🔍 测试API连接...")
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ 健康检查: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
    
    # 测试认证检查
    try:
        response = requests.get(f"{base_url}/api/v1/auth/check")
        print(f"✅ 认证检查: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 认证检查失败: {e}")
    
    # 测试登录
    try:
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        print(f"✅ 登录测试: {response.status_code}")
        if response.status_code == 200:
            print(f"   用户信息: {response.json()}")
        else:
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")

if __name__ == "__main__":
    test_api_endpoints()
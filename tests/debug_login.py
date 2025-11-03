#!/usr/bin/env python3
"""
调试登录API的详细测试脚本
"""
import requests
import json

def test_api_endpoints():
    base_url = "http://localhost:8000"
    
    print("🔍 测试API端点...")
    
    # 1. 测试根路径
    print("\n1. 测试根路径 /")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 2. 测试健康检查
    print("\n2. 测试健康检查 /health")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 3. 测试OpenAPI文档
    print("\n3. 测试OpenAPI文档 /docs")
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"   状态码: {response.status_code}")
        print(f"   内容长度: {len(response.text)}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 4. 测试登录端点 - 不同方法
    login_url = f"{base_url}/api/v1/auth/simple/login"
    
    print(f"\n4. 测试登录端点 {login_url}")
    
    # 4a. GET请求（应该返回405 Method Not Allowed）
    print("   4a. GET请求:")
    try:
        response = requests.get(login_url)
        print(f"      状态码: {response.status_code}")
        print(f"      响应: {response.text}")
    except Exception as e:
        print(f"      错误: {e}")
    
    # 4b. POST请求 - 正确的JSON格式
    print("   4b. POST请求 - JSON格式:")
    try:
        headers = {"Content-Type": "application/json"}
        data = {"username": "jlp-zhengyuneng"}
        response = requests.post(login_url, json=data, headers=headers)
        print(f"      状态码: {response.status_code}")
        print(f"      响应头: {dict(response.headers)}")
        print(f"      响应: {response.text}")
    except Exception as e:
        print(f"      错误: {e}")
    
    # 4c. POST请求 - 表单格式
    print("   4c. POST请求 - 表单格式:")
    try:
        data = {"username": "jlp-zhengyuneng"}
        response = requests.post(login_url, data=data)
        print(f"      状态码: {response.status_code}")
        print(f"      响应: {response.text}")
    except Exception as e:
        print(f"      错误: {e}")
    
    # 5. 测试admin账号登录
    print("\n5. 测试admin账号登录:")
    try:
        headers = {"Content-Type": "application/json"}
        data = {"username": "admin"}
        response = requests.post(login_url, json=data, headers=headers)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
    except Exception as e:
        print(f"   错误: {e}")

if __name__ == "__main__":
    test_api_endpoints()
#!/usr/bin/env python3
"""
测试当前运行的后端版本
"""
import requests
import json

def test_backend_version():
    """测试后端版本和可用端点"""
    try:
        # 测试根路径
        response = requests.get("http://localhost:8000/")
        print(f"根路径响应: {response.json()}")
        
        # 获取OpenAPI文档
        response = requests.get("http://localhost:8000/openapi.json")
        openapi_data = response.json()
        
        print(f"\nAPI标题: {openapi_data.get('info', {}).get('title', 'Unknown')}")
        print(f"API版本: {openapi_data.get('info', {}).get('version', 'Unknown')}")
        print(f"API描述: {openapi_data.get('info', {}).get('description', 'Unknown')}")
        
        print(f"\n可用端点数量: {len(openapi_data.get('paths', {}))}")
        print("所有端点:")
        for path in sorted(openapi_data.get('paths', {}).keys()):
            methods = list(openapi_data['paths'][path].keys())
            print(f"  {path} - {methods}")
            
        # 测试几个关键端点
        test_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/simple/login", 
            "/api/v1/tasks",
            "/api/v1/users"
        ]
        
        print(f"\n端点测试:")
        for endpoint in test_endpoints:
            try:
                response = requests.get(f"http://localhost:8000{endpoint}")
                print(f"  {endpoint} - 状态码: {response.status_code}")
            except Exception as e:
                print(f"  {endpoint} - 错误: {e}")
                
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_backend_version()
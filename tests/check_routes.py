#!/usr/bin/env python3
"""
检查API路由的脚本
"""
import requests
import json

def check_routes():
    try:
        response = requests.get("http://localhost:8000/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            print("🔍 已注册的API路径:")
            for path in sorted(paths.keys()):
                methods = list(paths[path].keys())
                print(f"   {path} - {', '.join(methods).upper()}")
            
            # 特别检查登录路径
            login_path = "/api/v1/auth/simple/login"
            if login_path in paths:
                print(f"\n✅ 找到登录路径: {login_path}")
                print(f"   支持的方法: {list(paths[login_path].keys())}")
            else:
                print(f"\n❌ 未找到登录路径: {login_path}")
                
        else:
            print(f"❌ 无法获取OpenAPI规范: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    check_routes()
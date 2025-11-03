#!/usr/bin/env python3
"""
测试登录API
"""
import requests
import json

def test_login():
    """测试jlp-zhengyuneng账号登录"""
    url = "http://localhost:8001/api/v1/auth/login"
    data = {"username": "admin"}
    
    try:
        print("🔍 测试登录API...")
        print(f"📍 URL: {url}")
        print(f"📝 数据: {data}")
        print("-" * 40)
        
        response = requests.post(url, json=data)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")
        print(f"📝 响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 登录成功!")
            print(f"👤 用户信息: {result.get('user', {})}")
            print(f"💬 消息: {result.get('message', '')}")
        else:
            print("❌ 登录失败!")
            
    except Exception as e:
        print(f"❌ 测试出错: {e}")

if __name__ == "__main__":
    test_login()
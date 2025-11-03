#!/usr/bin/env python3
"""
API连接测试脚本
测试前端和后端的API连接是否正常
"""

import requests
import json

def test_api_connection():
    """测试API连接"""
    base_url = "http://localhost:8001/api/v1"
    
    print("🔍 测试API连接...")
    print(f"📍 后端地址: {base_url}")
    print("=" * 50)
    
    # 测试1: 健康检查
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ 健康检查: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
    
    print("-" * 30)
    
    # 测试2: 登录API
    try:
        login_data = {"username": "admin"}
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"✅ 登录API: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   用户: {result['user']['username']}")
            print(f"   身份: {result['user']['identity']}")
            
            # 保存cookie用于后续测试
            cookies = response.cookies
            
            # 测试3: 获取用户信息
            try:
                me_response = requests.get(f"{base_url}/auth/me", cookies=cookies)
                print(f"✅ 用户信息API: {me_response.status_code}")
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    print(f"   当前用户: {user_info['username']}")
            except Exception as e:
                print(f"❌ 用户信息API失败: {e}")
                
    except Exception as e:
        print(f"❌ 登录API失败: {e}")
    
    print("-" * 30)
    
    # 测试4: 检查认证状态
    try:
        response = requests.get(f"{base_url}/auth/check")
        print(f"✅ 认证检查API: {response.status_code}")
    except Exception as e:
        print(f"❌ 认证检查API失败: {e}")
    
    print("=" * 50)
    print("🎉 API连接测试完成!")

if __name__ == "__main__":
    test_api_connection()
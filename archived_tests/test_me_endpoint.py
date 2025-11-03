#!/usr/bin/env python3
"""
测试/api/v1/auth/me端点
"""

import requests
import json

def test_me_endpoint():
    """测试/api/v1/auth/me端点"""
    
    # 先登录获取cookie
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("=== 登录获取cookie ===")
    login_response = requests.post(login_url, json=login_data)
    print(f"登录状态码: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # 获取cookie
        cookies = login_response.cookies
        print(f"获取到的cookies: {dict(cookies)}")
        
        # 测试/api/v1/auth/me端点
        me_url = "http://localhost:8000/api/v1/auth/me"
        print(f"\n=== 测试{me_url} ===")
        
        me_response = requests.get(me_url, cookies=cookies)
        print(f"状态码: {me_response.status_code}")
        print(f"响应头: {dict(me_response.headers)}")
        
        if me_response.status_code == 200:
            response_data = me_response.json()
            print(f"完整响应: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            print(f"\n用户数据字段:")
            for key, value in response_data.items():
                print(f"  {key}: {value}")
            
            print(f"\n检查字段:")
            print(f"  有role字段: {'role' in response_data}")
            print(f"  有identity字段: {'identity' in response_data}")
            print(f"  role值: {response_data.get('role')}")
            print(f"  identity值: {response_data.get('identity')}")
        else:
            print(f"请求失败: {me_response.text}")
    else:
        print(f"登录失败: {login_response.text}")

if __name__ == "__main__":
    test_me_endpoint()
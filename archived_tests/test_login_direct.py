#!/usr/bin/env python3
"""
直接测试登录API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login_direct():
    """直接测试登录API"""
    print("=== 直接测试登录API ===")
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                           json={"username": "admin"})
    
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        user_data = data.get('user', {})
        print(f"\n用户数据字段:")
        for key, value in user_data.items():
            print(f"  {key}: {value}")
            
        print(f"\n检查字段:")
        print(f"  有role字段: {'role' in user_data}")
        print(f"  有identity字段: {'identity' in user_data}")
        print(f"  role值: {user_data.get('role')}")
        print(f"  identity值: {user_data.get('identity')}")
    else:
        print(f"登录失败: {response.text}")

if __name__ == "__main__":
    test_login_direct()
#!/usr/bin/env python3
"""
调用测试服务器
"""

import requests
import json

def test_call_test_server():
    """调用测试服务器"""
    
    url = "http://localhost:8002/test-user-response"
    print(f"=== 测试{url} ===")
    
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    
    if response.status_code == 200:
        response_data = response.json()
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
        print(f"请求失败: {response.text}")

if __name__ == "__main__":
    test_call_test_server()
#!/usr/bin/env python3
"""
API 功能测试脚本
测试修复后的 main.py 中的各种 API 端点
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_health_check():
    """测试健康检查端点"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ 健康检查: {response.status_code} - {response.text}")
        return True
    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        return False

def test_login():
    """测试登录功能"""
    try:
        # 测试默认管理员登录
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"✓ 登录测试: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  - 返回数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True, response.cookies
        else:
            print(f"  - 错误信息: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"✗ 登录测试失败: {e}")
        return False, None

def test_get_current_user(cookies=None):
    """测试获取当前用户信息"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            cookies=cookies
        )
        
        print(f"✓ 获取用户信息: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  - 用户信息: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"  - 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 获取用户信息失败: {e}")
        return False

def test_user_groups(cookies=None):
    """测试用户分组功能"""
    try:
        # 获取用户分组列表
        response = requests.get(
            f"{BASE_URL}/api/v1/groups",
            cookies=cookies
        )
        
        print(f"✓ 获取用户分组: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  - 分组数量: {len(result)}")
            return True
        else:
            print(f"  - 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 用户分组测试失败: {e}")
        return False

def test_tasks(cookies=None):
    """测试任务功能"""
    try:
        # 获取任务列表
        response = requests.get(
            f"{BASE_URL}/api/v1/tasks",
            cookies=cookies
        )
        
        print(f"✓ 获取任务列表: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  - 任务数量: {len(result)}")
            return True
        else:
            print(f"  - 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 任务测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("开始 API 功能测试")
    print("=" * 50)
    
    # 1. 健康检查
    if not test_health_check():
        print("服务器未启动或无法访问")
        sys.exit(1)
    
    # 2. 登录测试
    login_success, cookies = test_login()
    if not login_success:
        print("登录失败，无法继续测试")
        sys.exit(1)
    
    # 3. 获取当前用户信息
    test_get_current_user(cookies)
    
    # 4. 测试用户分组
    test_user_groups(cookies)
    
    # 5. 测试任务
    test_tasks(cookies)
    
    print("=" * 50)
    print("API 测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
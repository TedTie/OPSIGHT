#!/usr/bin/env python3
"""
快速页面功能验证脚本
测试修复后的页面是否能正常加载和响应
"""

import requests
import json

def test_api_endpoints():
    """测试关键API端点"""
    base_url = "http://localhost:8001/api/v1"
    
    # 登录获取session
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    print("🔐 测试登录...")
    try:
        login_response = session.post(f"{base_url}/auth/login", json=login_data)
        if login_response.status_code == 200:
            print("✅ 登录成功")
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False
    
    # 测试关键API端点
    endpoints = [
        ("/auth/me", "用户信息"),
        ("/users", "用户列表"),
        ("/tasks", "任务列表"),
        ("/reports", "报告列表"),
        ("/analytics/dashboard", "仪表板数据"),
        ("/analytics/task-types", "任务类型统计")
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    for endpoint, name in endpoints:
        try:
            response = session.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                print(f"✅ {name}: 正常")
                success_count += 1
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: 请求失败 - {e}")
    
    print(f"\n📊 API测试结果: {success_count}/{total_count} 个端点正常")
    return success_count == total_count

def test_frontend_access():
    """测试前端页面访问"""
    frontend_url = "http://localhost:3001"
    
    print("\n🌐 测试前端页面访问...")
    try:
        response = requests.get(frontend_url, timeout=10)
        if response.status_code == 200:
            print("✅ 前端页面可以正常访问")
            return True
        else:
            print(f"❌ 前端页面访问失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端页面访问失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始快速页面功能验证...\n")
    
    # 测试前端访问
    frontend_ok = test_frontend_access()
    
    # 测试API端点
    api_ok = test_api_endpoints()
    
    print("\n" + "="*50)
    if frontend_ok and api_ok:
        print("🎉 所有测试通过！页面功能已修复")
        print("\n✨ 修复内容总结:")
        print("1. 修复了路由守卫中权限字段不匹配问题 (permission_level -> identity)")
        print("2. 修复了前端API端口配置错误 (8001 -> 8000)")
        print("3. 重启前端服务器应用新配置")
        print("\n🔍 建议手动测试:")
        print("- 登录功能")
        print("- 各个页面的数据加载")
        print("- 用户管理功能")
        print("- 任务管理功能")
    else:
        print("⚠️  仍有问题需要解决")
        if not frontend_ok:
            print("- 前端页面访问异常")
        if not api_ok:
            print("- 部分API端点异常")
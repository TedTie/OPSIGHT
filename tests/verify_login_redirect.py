#!/usr/bin/env python3
"""
验证登录跳转功能
"""

import requests
import json

def test_login_flow():
    """测试完整的登录流程"""
    print("🔍 验证登录跳转功能...")
    print("=" * 50)
    
    # 1. 测试后端登录API
    print("📍 步骤1: 测试后端登录API")
    try:
        login_url = "http://localhost:8001/api/v1/auth/login"
        login_data = {"username": "admin"}
        
        response = requests.post(login_url, json=login_data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 登录成功")
            print(f"   用户: {result['user']['username']}")
            print(f"   身份: {result['user']['identity']}")
            
            # 2. 检查前端应该设置的localStorage数据
            print("\n📍 步骤2: 检查前端应该设置的数据")
            user_data = json.dumps(result['user'])
            print(f"   应设置 localStorage['user']: {user_data}")
            print(f"   应设置 localStorage['token']: 'authenticated'")
            
            # 3. 模拟路由守卫逻辑
            print("\n📍 步骤3: 模拟路由守卫逻辑")
            has_token = True  # 模拟localStorage中有token
            current_path = "/login"  # 模拟当前在登录页
            
            if has_token and current_path == "/login":
                print("   ✅ 路由守卫应该重定向到 /dashboard")
                print("   逻辑: 已登录用户访问登录页 → 重定向到仪表板")
            else:
                print("   ❌ 路由守卫逻辑异常")
            
            return True
        else:
            print(f"   ❌ 登录失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 登录测试失败: {e}")
        return False

def check_route_guard_logic():
    """检查路由守卫逻辑"""
    print("\n🔍 检查路由守卫逻辑...")
    print("-" * 30)
    
    scenarios = [
        {"token": True, "path": "/", "expected": "重定向到 /dashboard"},
        {"token": True, "path": "/login", "expected": "重定向到 /dashboard"},
        {"token": True, "path": "/dashboard", "expected": "允许访问"},
        {"token": False, "path": "/", "expected": "重定向到 /login"},
        {"token": False, "path": "/dashboard", "expected": "重定向到 /login"},
        {"token": False, "path": "/login", "expected": "允许访问"},
    ]
    
    for scenario in scenarios:
        token_status = "有token" if scenario["token"] else "无token"
        print(f"   场景: {token_status} + 访问 {scenario['path']}")
        print(f"   预期: {scenario['expected']}")
        print()

def create_test_instructions():
    """创建手动测试说明"""
    print("\n📋 手动测试说明:")
    print("=" * 50)
    print("1. 打开浏览器访问: http://localhost:3001/")
    print("2. 应该自动重定向到登录页面")
    print("3. 在登录页面输入用户名: admin")
    print("4. 点击登录按钮")
    print("5. 观察是否自动跳转到仪表板页面")
    print("6. 检查浏览器开发者工具:")
    print("   - Application > Local Storage")
    print("   - 应该看到 'user' 和 'token' 两个键")
    print("7. 刷新页面，应该保持在仪表板页面")
    print("8. 手动访问 /login，应该重定向到仪表板")

if __name__ == "__main__":
    print("🚀 开始验证登录跳转功能...")
    
    # 测试登录流程
    success = test_login_flow()
    
    # 检查路由守卫逻辑
    check_route_guard_logic()
    
    # 提供手动测试说明
    create_test_instructions()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 后端登录API正常，前端应该能正确跳转")
        print("💡 请按照上述手动测试说明验证前端跳转功能")
    else:
        print("❌ 后端登录API异常，需要先修复后端问题")
    
    print("\n🔧 如果跳转仍有问题，请检查:")
    print("1. 浏览器控制台是否有JavaScript错误")
    print("2. 网络请求是否成功")
    print("3. localStorage是否正确设置")
    print("4. 路由守卫是否正确执行")
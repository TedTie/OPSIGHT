#!/usr/bin/env python3
"""
页面加载测试脚本
测试各个页面是否能正常加载
"""

import requests
import json
import time

def test_login_and_get_cookies():
    """登录并获取cookies"""
    print("🔐 执行登录获取认证...")
    
    try:
        login_url = "http://localhost:8001/api/v1/auth/login"
        login_data = {"username": "admin"}
        
        session = requests.Session()
        response = session.post(login_url, json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 登录成功: {result['user']['username']}")
            return session, result['user']
        else:
            print(f"   ❌ 登录失败: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ 登录错误: {e}")
        return None, None

def test_api_endpoints(session):
    """测试各个API端点"""
    print("\n🔍 测试API端点...")
    print("-" * 40)
    
    endpoints = [
        ("GET", "/api/v1/auth/me", "用户信息"),
        ("GET", "/api/v1/auth/check", "认证检查"),
        ("GET", "/api/v1/tasks", "任务列表"),
        ("GET", "/api/v1/reports", "报告列表"),
        ("GET", "/api/v1/analytics", "分析数据"),
        ("GET", "/api/v1/admin/users", "用户管理"),
        ("GET", "/api/v1/admin/groups", "组管理"),
        ("GET", "/api/v1/admin/metrics", "系统指标"),
    ]
    
    base_url = "http://localhost:8001"
    results = {}
    
    for method, endpoint, description in endpoints:
        try:
            url = base_url + endpoint
            if method == "GET":
                response = session.get(url)
            elif method == "POST":
                response = session.post(url, json={})
            
            status = response.status_code
            results[endpoint] = status
            
            if status == 200:
                print(f"   ✅ {description}: {status}")
            elif status == 404:
                print(f"   ⚠️  {description}: {status} (端点不存在)")
            elif status == 403:
                print(f"   🔒 {description}: {status} (权限不足)")
            else:
                print(f"   ❌ {description}: {status}")
                
        except Exception as e:
            print(f"   ❌ {description}: 请求失败 - {e}")
            results[endpoint] = "ERROR"
    
    return results

def check_frontend_routes():
    """检查前端路由配置"""
    print("\n🗺️  检查前端路由配置...")
    print("-" * 40)
    
    routes = [
        ("/", "首页重定向"),
        ("/login", "登录页面"),
        ("/dashboard", "仪表板"),
        ("/tasks", "任务管理"),
        ("/reports", "报告页面"),
        ("/analytics", "分析页面"),
        ("/settings", "设置页面"),
        ("/profile", "个人资料"),
        ("/knowledge-base", "知识库"),
        ("/admin/users", "用户管理"),
        ("/admin/groups", "组管理"),
        ("/admin/ai", "AI管理"),
        ("/admin/metrics", "系统指标"),
        ("/permission-test", "权限测试"),
        ("/test-buttons", "按钮测试"),
    ]
    
    for route, description in routes:
        print(f"   📍 {route} - {description}")

def analyze_potential_issues():
    """分析潜在问题"""
    print("\n🔍 分析潜在问题...")
    print("-" * 40)
    
    issues = [
        "1. 路由守卫权限字段不匹配 (已修复: permission_level → identity)",
        "2. API端点可能不存在或返回错误",
        "3. 组件导入路径可能有问题",
        "4. 认证状态可能未正确初始化",
        "5. 某些页面可能缺少必要的数据",
    ]
    
    for issue in issues:
        print(f"   ⚠️  {issue}")

def provide_debugging_steps():
    """提供调试步骤"""
    print("\n🛠️  调试步骤建议:")
    print("=" * 50)
    
    steps = [
        "1. 打开浏览器开发者工具 (F12)",
        "2. 查看Console标签页的错误信息",
        "3. 查看Network标签页的网络请求",
        "4. 检查Application > Local Storage中的认证信息",
        "5. 尝试访问不同的页面路由",
        "6. 检查是否有404或500错误",
        "7. 查看前端开发服务器的终端输出",
        "8. 查看后端服务器的终端输出",
    ]
    
    for step in steps:
        print(f"   📋 {step}")
    
    print("\n🌐 测试URL:")
    print("   前端: http://localhost:3001/")
    print("   后端API文档: http://localhost:8001/docs")

if __name__ == "__main__":
    print("🚀 开始页面加载测试...")
    print("=" * 50)
    
    # 1. 测试登录
    session, user = test_login_and_get_cookies()
    
    if session and user:
        # 2. 测试API端点
        api_results = test_api_endpoints(session)
        
        # 3. 检查路由配置
        check_frontend_routes()
        
        # 4. 分析潜在问题
        analyze_potential_issues()
        
        # 5. 提供调试步骤
        provide_debugging_steps()
        
        print("\n" + "=" * 50)
        print("📊 测试总结:")
        print(f"   登录状态: ✅ 成功 ({user['username']})")
        print(f"   用户身份: {user['identity']}")
        
        # 统计API结果
        success_count = sum(1 for status in api_results.values() if status == 200)
        total_count = len(api_results)
        print(f"   API端点: {success_count}/{total_count} 成功")
        
        if success_count < total_count:
            print("\n⚠️  部分API端点异常，这可能导致页面显示问题")
            print("💡 建议检查后端是否实现了所有必要的API端点")
        
    else:
        print("❌ 登录失败，无法继续测试")
        print("💡 请检查后端服务是否正常运行")
    
    print("\n🔧 如果页面仍有问题，请:")
    print("1. 检查浏览器控制台错误")
    print("2. 确认所有组件文件存在")
    print("3. 验证API端点是否正确实现")
    print("4. 检查路由配置是否正确")
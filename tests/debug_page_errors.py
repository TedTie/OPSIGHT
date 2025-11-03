#!/usr/bin/env python3
"""
页面错误详细诊断脚本
检查各个页面的API调用和可能的错误
"""

import requests
import json
import time

def test_login_and_get_session():
    """登录并获取session"""
    base_url = "http://localhost:8001/api/v1"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    try:
        login_response = session.post(f"{base_url}/auth/login", json=login_data)
        if login_response.status_code == 200:
            print("✅ 登录成功")
            return session, base_url
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"响应内容: {login_response.text}")
            return None, None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None, None

def test_api_endpoints_detailed(session, base_url):
    """详细测试各个API端点"""
    endpoints = [
        # 认证相关
        ("/auth/me", "GET", "获取当前用户信息"),
        ("/auth/check", "GET", "检查认证状态"),
        
        # 用户管理
        ("/users", "GET", "获取用户列表"),
        
        # 任务管理
        ("/tasks", "GET", "获取任务列表"),
        ("/tasks?status=pending", "GET", "获取待处理任务"),
        ("/tasks?assigned_to_me=true", "GET", "获取分配给我的任务"),
        
        # 报告管理
        ("/reports", "GET", "获取报告列表"),
        
        # 数据分析
        ("/analytics/dashboard", "GET", "获取仪表板数据"),
        ("/analytics/task-types", "GET", "获取任务类型统计"),
        
        # AI配置
        ("/ai/config", "GET", "获取AI配置"),
    ]
    
    print("\n🔍 详细测试API端点...")
    success_count = 0
    total_count = len(endpoints)
    
    for endpoint, method, description in endpoints:
        try:
            if method == "GET":
                response = session.get(f"{base_url}{endpoint}")
            elif method == "POST":
                response = session.post(f"{base_url}{endpoint}")
            
            if response.status_code == 200:
                print(f"✅ {description}: 正常 (200)")
                success_count += 1
                # 检查响应数据结构
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📊 返回列表，包含 {len(data)} 项")
                    elif isinstance(data, dict):
                        print(f"   📊 返回对象，包含字段: {list(data.keys())[:5]}")
                except:
                    print(f"   ⚠️  响应不是JSON格式")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                print(f"   错误内容: {response.text[:200]}")
        except Exception as e:
            print(f"❌ {description}: 请求失败 - {e}")
    
    print(f"\n📊 API测试结果: {success_count}/{total_count} 个端点正常")
    return success_count == total_count

def test_frontend_pages():
    """测试前端页面访问"""
    frontend_url = "http://localhost:3001"
    
    print("\n🌐 测试前端页面访问...")
    try:
        response = requests.get(frontend_url, timeout=10)
        if response.status_code == 200:
            print("✅ 前端主页可以正常访问")
            
            # 检查页面内容
            content = response.text
            if "<!DOCTYPE html>" in content:
                print("✅ 返回了有效的HTML页面")
            if "vite" in content.lower():
                print("✅ 检测到Vite开发环境")
            if "vue" in content.lower():
                print("✅ 检测到Vue.js框架")
                
            return True
        else:
            print(f"❌ 前端页面访问失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端页面访问失败: {e}")
        return False

def check_common_issues():
    """检查常见问题"""
    print("\n🔧 检查常见问题...")
    
    issues = []
    
    # 检查端口冲突
    try:
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code != 200:
            issues.append("前端服务器响应异常")
    except:
        issues.append("前端服务器无法访问")
    
    try:
        response = requests.get("http://localhost:8001/api/v1/auth/check", timeout=5)
        if response.status_code not in [200, 401]:
            issues.append("后端API服务器响应异常")
    except:
        issues.append("后端API服务器无法访问")
    
    # 检查CORS问题
    try:
        response = requests.options("http://localhost:8001/api/v1/auth/check", timeout=5)
        if response.status_code not in [200, 204]:
            issues.append("可能存在CORS配置问题")
    except:
        issues.append("CORS预检请求失败")
    
    if issues:
        print("⚠️  发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ 未发现常见问题")
    
    return len(issues) == 0

def main():
    print("🚀 开始页面错误详细诊断...\n")
    
    # 测试前端页面
    frontend_ok = test_frontend_pages()
    
    # 测试后端API
    session, base_url = test_login_and_get_session()
    if session and base_url:
        api_ok = test_api_endpoints_detailed(session, base_url)
    else:
        api_ok = False
    
    # 检查常见问题
    no_common_issues = check_common_issues()
    
    print("\n" + "="*60)
    print("📋 诊断结果总结:")
    print(f"   前端页面访问: {'✅ 正常' if frontend_ok else '❌ 异常'}")
    print(f"   后端API功能: {'✅ 正常' if api_ok else '❌ 异常'}")
    print(f"   常见问题检查: {'✅ 无问题' if no_common_issues else '❌ 有问题'}")
    
    if frontend_ok and api_ok and no_common_issues:
        print("\n🎉 系统运行正常！")
        print("\n💡 如果仍有控制台错误，可能的原因:")
        print("   1. 浏览器缓存问题 - 尝试硬刷新 (Ctrl+Shift+R)")
        print("   2. 前端组件内部错误 - 需要检查具体组件代码")
        print("   3. 网络请求超时 - 检查网络连接")
        print("   4. 数据格式不匹配 - 检查API响应格式")
    else:
        print("\n⚠️  系统存在问题，需要进一步排查")
        
        if not frontend_ok:
            print("\n🔧 前端问题排查建议:")
            print("   1. 检查前端开发服务器是否正常运行")
            print("   2. 检查端口3001是否被占用")
            print("   3. 重启前端开发服务器")
            
        if not api_ok:
            print("\n🔧 后端API问题排查建议:")
            print("   1. 检查后端服务器是否正常运行")
            print("   2. 检查端口8001是否被占用")
            print("   3. 检查数据库连接")
            print("   4. 重启后端服务器")

if __name__ == "__main__":
    main()
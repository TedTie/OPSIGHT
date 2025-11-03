#!/usr/bin/env python3
"""
检查认证问题的脚本
"""

import os
import sys
import sqlite3
import requests
import json

# 切换到backend目录
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if os.path.exists(backend_path):
    os.chdir(backend_path)

def check_database_users():
    """检查数据库中的用户"""
    print("🔍 检查数据库中的用户...")
    print("=" * 50)
    
    db_path = "simple_app.db"
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查用户表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("❌ 用户表不存在")
            return False
        
        # 查询所有用户
        cursor.execute("SELECT id, username, identity, is_active FROM users;")
        users = cursor.fetchall()
        
        if users:
            print(f"✅ 找到 {len(users)} 个用户:")
            for user in users:
                print(f"   ID: {user[0]}, 用户名: {user[1]}, 身份: {user[2]}, 激活: {user[3]}")
        else:
            print("❌ 数据库中没有用户")
            return False
        
        # 特别检查super_admin用户
        cursor.execute("SELECT * FROM users WHERE username = 'super_admin';")
        super_admin = cursor.fetchone()
        
        if super_admin:
            print(f"✅ 找到super_admin用户: {super_admin}")
        else:
            print("❌ 未找到super_admin用户")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def test_backend_api():
    """测试后端API"""
    print("\n🔍 测试后端API...")
    print("=" * 50)
    
    base_url = "http://localhost:9000"
    
    # 1. 测试健康检查
    print("📍 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   根路径状态: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 根路径访问失败: {e}")
        return False
    
    # 2. 测试文档
    print("📍 测试API文档...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"   文档状态: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 文档访问失败: {e}")
    
    # 3. 测试OpenAPI规范
    print("📍 获取API路径列表...")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            print(f"   找到 {len(paths)} 个API路径:")
            auth_paths = [path for path in paths.keys() if 'auth' in path]
            if auth_paths:
                print("   认证相关路径:")
                for path in auth_paths:
                    methods = list(paths[path].keys())
                    print(f"      {path} - {', '.join(methods).upper()}")
            else:
                print("   ❌ 未找到认证相关路径")
        else:
            print(f"   ❌ OpenAPI规范获取失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ OpenAPI规范获取异常: {e}")
    
    # 4. 测试登录API
    print("📍 测试登录API...")
    login_url = f"{base_url}/api/v1/auth/login"
    
    # 测试不同的用户名
    test_users = ["super_admin", "admin", "test_user"]
    
    for username in test_users:
        print(f"   测试用户: {username}")
        try:
            login_data = {"username": username}
            response = requests.post(login_url, json=login_data, timeout=5)
            print(f"      状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ 登录成功")
                print(f"      用户信息: {result.get('user', {})}")
                
                # 测试获取当前用户信息
                cookies = response.cookies
                me_response = requests.get(f"{base_url}/api/v1/auth/me", cookies=cookies, timeout=5)
                print(f"      获取用户信息状态: {me_response.status_code}")
                
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    print(f"      当前用户: {user_info}")
                    return True
                    
            elif response.status_code == 404:
                print(f"      ❌ 用户不存在")
            else:
                print(f"      ❌ 登录失败: {response.text}")
                
        except Exception as e:
            print(f"      ❌ 登录测试异常: {e}")
    
    return False

def check_frontend_config():
    """检查前端配置"""
    print("\n🔍 检查前端配置...")
    print("=" * 50)
    
    frontend_path = os.path.join(os.path.dirname(backend_path), 'frontend')
    
    # 检查.env文件
    env_file = os.path.join(frontend_path, '.env')
    if os.path.exists(env_file):
        print("✅ 找到前端.env文件:")
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"   内容:\n{content}")
    else:
        print("❌ 未找到前端.env文件")
    
    # 检查API配置
    api_file = os.path.join(frontend_path, 'src', 'utils', 'api.js')
    if os.path.exists(api_file):
        print("✅ 找到API配置文件:")
        with open(api_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:20], 1):  # 只显示前20行
                if 'baseURL' in line or 'localhost' in line:
                    print(f"   第{i}行: {line.strip()}")
    else:
        print("❌ 未找到API配置文件")

def main():
    """主函数"""
    print("🚀 认证问题诊断")
    print("=" * 50)
    
    # 1. 检查数据库用户
    db_ok = check_database_users()
    
    # 2. 测试后端API
    api_ok = test_backend_api()
    
    # 3. 检查前端配置
    check_frontend_config()
    
    print("\n" + "=" * 50)
    print("📊 诊断结果:")
    print(f"   数据库用户: {'✅ 正常' if db_ok else '❌ 异常'}")
    print(f"   后端API: {'✅ 正常' if api_ok else '❌ 异常'}")
    
    if not db_ok:
        print("\n💡 建议:")
        print("   1. 检查数据库是否正确初始化")
        print("   2. 运行数据库初始化脚本")
        print("   3. 确认用户数据是否正确插入")
    
    if not api_ok:
        print("\n💡 建议:")
        print("   1. 检查后端服务是否正常运行")
        print("   2. 检查API路径是否正确")
        print("   3. 检查认证逻辑是否有问题")

if __name__ == "__main__":
    main()
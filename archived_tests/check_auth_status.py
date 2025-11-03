#!/usr/bin/env python3
"""
检查认证状态
"""

import requests
import json

def check_auth_status():
    print("🔍 检查认证状态...")
    
    # 创建session保持cookie
    session = requests.Session()
    
    try:
        # 1. 登录
        print("\n1. 尝试登录...")
        login_response = session.post(
            'http://localhost:8000/api/v1/auth/login',
            json={
                'username': 'admin',
                'password': 'admin123'
            }
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            print("✅ 登录成功")
            print(f"用户信息: {json.dumps(login_data, indent=2, ensure_ascii=False)}")
            
            user = login_data.get('user', {})
            print(f"\n用户角色: {user.get('role')}")
            print(f"是否管理员: {user.get('role') in ['admin', 'super_admin']}")
            print(f"是否超级管理员: {user.get('role') == 'super_admin'}")
            
        else:
            print(f"❌ 登录失败: {login_response.status_code}")
            print(f"错误信息: {login_response.text}")
            return
        
        # 2. 检查当前用户信息
        print("\n2. 获取当前用户信息...")
        me_response = session.get('http://localhost:8000/api/v1/auth/me')
        
        if me_response.status_code == 200:
            me_data = me_response.json()
            print("✅ 获取用户信息成功")
            print(f"当前用户: {json.dumps(me_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取用户信息失败: {me_response.status_code}")
            print(f"错误信息: {me_response.text}")
        
        # 3. 测试超级管理员权限的API
        print("\n3. 测试超级管理员API...")
        
        # 测试AI设置API
        ai_settings_response = session.get('http://localhost:8000/api/v1/settings/ai')
        if ai_settings_response.status_code == 200:
            print("✅ AI设置API访问成功")
        else:
            print(f"❌ AI设置API访问失败: {ai_settings_response.status_code}")
        
        # 测试系统设置API
        system_settings_response = session.get('http://localhost:8000/api/v1/settings/system')
        if system_settings_response.status_code == 200:
            print("✅ 系统设置API访问成功")
        else:
            print(f"❌ 系统设置API访问失败: {system_settings_response.status_code}")
        
        # 测试指标API
        metrics_response = session.get('http://localhost:8000/api/v1/admin/metrics')
        if metrics_response.status_code == 200:
            print("✅ 指标API访问成功")
        else:
            print(f"❌ 指标API访问失败: {metrics_response.status_code}")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_auth_status()
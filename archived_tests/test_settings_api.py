#!/usr/bin/env python3
"""
测试设置API功能
"""

import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_settings_api():
    """测试设置API功能"""
    print("🧪 开始测试设置API功能...")
    
    # 创建session来保持cookie
    session = requests.Session()
    
    # 1. 登录获取cookie
    print("\n1. 登录超级管理员...")
    login_response = session.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin"
    })
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        print(login_response.text)
        return
    
    login_data = login_response.json()
    print(f"✅ 登录成功，用户: {login_data['user']['username']}, 角色: {login_data['user']['role']}")
    
    # 2. 测试获取AI设置
    print("\n2. 测试获取AI设置...")
    ai_settings_response = session.get(f"{BASE_URL}/settings/ai")
    
    if ai_settings_response.status_code == 200:
        ai_settings = ai_settings_response.json()
        print("✅ 获取AI设置成功:")
        print(f"   - 提供商: {ai_settings['provider']}")
        print(f"   - 模型: {ai_settings['model_name']}")
        print(f"   - 最大tokens: {ai_settings['max_tokens']}")
        print(f"   - 温度: {ai_settings['temperature']}")
    else:
        print(f"❌ 获取AI设置失败: {ai_settings_response.status_code}")
        print(ai_settings_response.text)
    
    # 3. 测试更新AI设置
    print("\n3. 测试更新AI设置...")
    update_ai_data = {
        "provider": "openai",
        "model_name": "gpt-4",
        "max_tokens": 4000,
        "temperature": 0.8
    }
    
    update_ai_response = session.put(f"{BASE_URL}/settings/ai", json=update_ai_data)
    
    if update_ai_response.status_code == 200:
        updated_ai_settings = update_ai_response.json()
        print("✅ 更新AI设置成功:")
        print(f"   - 提供商: {updated_ai_settings['provider']}")
        print(f"   - 模型: {updated_ai_settings['model_name']}")
        print(f"   - 最大tokens: {updated_ai_settings['max_tokens']}")
        print(f"   - 温度: {updated_ai_settings['temperature']}")
    else:
        print(f"❌ 更新AI设置失败: {update_ai_response.status_code}")
        print(update_ai_response.text)
    
    # 4. 测试获取系统设置
    print("\n4. 测试获取系统设置...")
    system_settings_response = session.get(f"{BASE_URL}/settings/system")
    
    if system_settings_response.status_code == 200:
        system_settings = system_settings_response.json()
        print("✅ 获取系统设置成功:")
        print(f"   - 系统名称: {system_settings['system_name']}")
        print(f"   - 时区: {system_settings['timezone']}")
        print(f"   - 语言: {system_settings['language']}")
        print(f"   - 自动分析: {system_settings['auto_analysis']}")
        print(f"   - 数据保留天数: {system_settings['data_retention_days']}")
    else:
        print(f"❌ 获取系统设置失败: {system_settings_response.status_code}")
        print(system_settings_response.text)
    
    # 5. 测试更新系统设置
    print("\n5. 测试更新系统设置...")
    update_system_data = {
        "system_name": "OpSight运营洞察系统 v2.0",
        "timezone": "Asia/Shanghai",
        "language": "zh-CN",
        "auto_analysis": True,
        "data_retention_days": 730
    }
    
    update_system_response = session.put(f"{BASE_URL}/settings/system", json=update_system_data)
    
    if update_system_response.status_code == 200:
        updated_system_settings = update_system_response.json()
        print("✅ 更新系统设置成功:")
        print(f"   - 系统名称: {updated_system_settings['system_name']}")
        print(f"   - 时区: {updated_system_settings['timezone']}")
        print(f"   - 语言: {updated_system_settings['language']}")
        print(f"   - 自动分析: {updated_system_settings['auto_analysis']}")
        print(f"   - 数据保留天数: {updated_system_settings['data_retention_days']}")
    else:
        print(f"❌ 更新系统设置失败: {update_system_response.status_code}")
        print(update_system_response.text)
    
    print("\n🎉 设置API测试完成!")

if __name__ == "__main__":
    test_settings_api()
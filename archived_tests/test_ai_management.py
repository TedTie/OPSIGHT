#!/usr/bin/env python3
"""
AI管理功能测试脚本
测试智能体配置、AI功能配置和调用日志功能
"""

import requests
import json
import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# 切换到backend目录，确保使用正确的数据库文件
os.chdir(backend_path)

BASE_URL = "http://localhost:9000/api/v1"

def login():
    """登录获取session"""
    login_data = {"username": "admin"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        print("✅ 登录成功")
        return response.cookies
    else:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return None

def test_ai_stats(cookies):
    """测试AI统计接口"""
    print("\n🔍 测试AI统计接口...")
    response = requests.get(f"{BASE_URL}/ai/stats", cookies=cookies)
    if response.status_code == 200:
        print("✅ AI统计接口正常")
        print(f"   响应: {response.json()}")
    else:
        print(f"❌ AI统计接口失败: {response.status_code} - {response.text}")

def test_ai_agents(cookies):
    """测试智能体管理接口"""
    print("\n🤖 测试智能体管理接口...")
    
    # 获取智能体列表
    response = requests.get(f"{BASE_URL}/ai/agents", cookies=cookies)
    if response.status_code == 200:
        print("✅ 获取智能体列表成功")
        agents = response.json()
        print(f"   当前智能体数量: {len(agents)}")
    else:
        print(f"❌ 获取智能体列表失败: {response.status_code} - {response.text}")
        return
    
    # 创建智能体（如果不存在）
    agent_data = {
        "name": "测试智能体",
        "description": "这是一个测试智能体",
        "provider": "openrouter",
        "model_name": "openai/gpt-4",
        "api_key": "test-key",
        "system_prompt": "你是一个智能助手，请帮助用户解决问题。",
        "max_tokens": 2000,
        "temperature": 0.7,
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/ai/agents", json=agent_data, cookies=cookies)
    if response.status_code == 200:
        print("✅ 创建智能体成功")
        agent = response.json()
        print(f"   智能体ID: {agent.get('id')}")
        return agent.get('id')
    elif response.status_code == 500 and "UNIQUE constraint failed" in response.text:
        # 智能体已存在，获取现有的智能体ID
        agents_response = requests.get(f"{BASE_URL}/ai/agents", cookies=cookies)
        if agents_response.status_code == 200:
            agents = agents_response.json()
            existing_agent = next((agent for agent in agents if agent["name"] == "测试智能体"), None)
            if existing_agent:
                agent_id = existing_agent["id"]
                print(f"✅ 使用现有智能体")
                print(f"   智能体ID: {agent_id}")
                return agent_id
            else:
                return None
        else:
            return None
    else:
        print(f"❌ 创建智能体失败: {response.status_code} - {response.text}")
        return None

def test_ai_functions(cookies, agent_id):
    """测试AI功能管理接口"""
    print("\n⚙️ 测试AI功能管理接口...")
    
    # 获取AI功能列表
    response = requests.get(f"{BASE_URL}/ai/functions", cookies=cookies)
    if response.status_code == 200:
        print("✅ 获取AI功能列表成功")
        functions = response.json()
        print(f"   当前AI功能数量: {len(functions)}")
    else:
        print(f"❌ 获取AI功能列表失败: {response.status_code} - {response.text}")
        return
    
    # 创建新AI功能
    if agent_id:
        function_data = {
            "name": "文本分析",
            "description": "分析文本内容的情感和主题",
            "function_type": "emotion_analysis",
            "agent_id": agent_id,
            "prompt_template": "请分析以下文本的情感和主题：{input_text}",
            "is_active": True
        }
        
        response = requests.post(f"{BASE_URL}/ai/functions", json=function_data, cookies=cookies)
        if response.status_code == 200:
            print("✅ 创建AI功能成功")
            function = response.json()
            print(f"   功能ID: {function.get('id')}")
            return function.get('id')
        else:
            print(f"❌ 创建AI功能失败: {response.status_code} - {response.text}")
    
    return None

def test_ai_call(cookies, function_id):
    """测试AI调用接口"""
    print("\n📞 测试AI调用接口...")
    
    # 获取可用的AI功能
    functions_response = requests.get(f"{BASE_URL}/ai/functions", cookies=cookies)
    if functions_response.status_code == 200:
        functions = functions_response.json()
        if functions:
            function_id = functions[0]["id"]
            call_data = {
                "function_id": function_id,
                "input_data": {"input_text": "今天天气很好，我心情很愉快！"}
            }
            
            response = requests.post(f"{BASE_URL}/ai/call", json=call_data, cookies=cookies)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ AI调用成功")
                print(f"   调用结果: {result}")
            else:
                print(f"❌ AI调用失败: {response.status_code} - {response.text}")
        else:
            print("❌ 没有可用的AI功能进行测试")
    else:
        print("❌ 获取AI功能列表失败")

def test_ai_logs(cookies):
    """测试AI调用日志接口"""
    print("\n📋 测试AI调用日志接口...")
    
    response = requests.get(f"{BASE_URL}/ai/logs", cookies=cookies)
    if response.status_code == 200:
        print("✅ 获取AI调用日志成功")
        logs = response.json()
        print(f"   日志数量: {len(logs.get('items', []))}")
        print(f"   总数: {logs.get('total', 0)}")
    else:
        print(f"❌ 获取AI调用日志失败: {response.status_code} - {response.text}")

def main():
    print("🚀 开始AI管理功能测试...")
    print("=" * 50)
    
    # 登录
    cookies = login()
    if not cookies:
        return
    
    # 测试各个功能
    test_ai_stats(cookies)
    agent_id = test_ai_agents(cookies)
    function_id = test_ai_functions(cookies, agent_id)
    test_ai_call(cookies, function_id)
    test_ai_logs(cookies)
    
    print("\n" + "=" * 50)
    print("🎉 AI管理功能测试完成!")

if __name__ == "__main__":
    main()
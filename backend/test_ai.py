#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 AI 管理 API
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def login():
    """登录获取会话"""
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    return response

def test_ai_apis():
    """测试 AI 管理相关 API"""
    print("=" * 50)
    print("开始 AI 管理 API 测试")
    print("=" * 50)
    
    # 登录
    login_response = login()
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return
    
    session = requests.Session()
    session.cookies.update(login_response.cookies)
    
    # 1. 测试创建 AI 智能体
    print("1. 测试创建 AI 智能体...")
    agent_data = {
        "name": "测试智能体",
        "description": "用于测试的AI智能体",
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "system_prompt": "你是一个专业的工作助手，帮助用户分析工作情况并提供建议。",
        "temperature": 0.7,
        "max_tokens": 1000,
        "is_active": True
    }
    
    create_agent_response = session.post(f"{BASE_URL}/api/v1/ai/agents", json=agent_data)
    print(f"   创建智能体状态: {create_agent_response.status_code}")
    if create_agent_response.status_code == 200:
        agent_result = create_agent_response.json()
        agent_id = agent_result["id"]
        print(f"   ✓ 创建智能体成功，ID: {agent_id}")
        print(f"   智能体名称: {agent_result['name']}")
    else:
        print(f"   ❌ 创建智能体失败: {create_agent_response.text}")
        agent_id = None
    
    # 2. 测试获取智能体列表
    print("\n2. 测试获取智能体列表...")
    agents_response = session.get(f"{BASE_URL}/api/v1/ai/agents")
    print(f"   获取智能体列表状态: {agents_response.status_code}")
    if agents_response.status_code == 200:
        agents = agents_response.json()
        print(f"   ✓ 获取智能体列表成功")
        print(f"   智能体数量: {len(agents)}")
        if agents:
            print(f"   第一个智能体: {agents[0]['name']}")
    else:
        print(f"   ❌ 获取智能体列表失败: {agents_response.text}")
    
    # 3. 测试创建 AI 功能
    print("\n3. 测试创建 AI 功能...")
    if agent_id:
        function_data = {
            "name": "日报分析",
            "description": "分析用户的日报内容，提供工作建议",
            "function_type": "analysis",
            "agent_id": agent_id,
            "input_schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "日报内容"}
                }
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "analysis": {"type": "string", "description": "分析结果"}
                }
            },
            "is_active": True
        }
        
        create_function_response = session.post(f"{BASE_URL}/api/v1/ai/functions", json=function_data)
        print(f"   创建AI功能状态: {create_function_response.status_code}")
        if create_function_response.status_code == 200:
            function_result = create_function_response.json()
            function_id = function_result["id"]
            print(f"   ✓ 创建AI功能成功，ID: {function_id}")
            print(f"   功能名称: {function_result['name']}")
        else:
            print(f"   ❌ 创建AI功能失败: {create_function_response.text}")
            function_id = None
    else:
        print("   跳过创建AI功能（智能体创建失败）")
        function_id = None
    
    # 4. 测试获取 AI 功能列表
    print("\n4. 测试获取 AI 功能列表...")
    functions_response = session.get(f"{BASE_URL}/api/v1/ai/functions")
    print(f"   获取AI功能列表状态: {functions_response.status_code}")
    if functions_response.status_code == 200:
        functions = functions_response.json()
        print(f"   ✓ 获取AI功能列表成功")
        print(f"   功能数量: {len(functions)}")
        if functions:
            print(f"   第一个功能: {functions[0]['name']}")
    else:
        print(f"   ❌ 获取AI功能列表失败: {functions_response.text}")
    
    # 5. 测试调用 AI 功能
    print("\n5. 测试调用 AI 功能...")
    if function_id:
        call_data = {
            "function_id": function_id,
            "input_data": {
                "input_text": "今天完成了项目开发，遇到了一些技术难题但都解决了，心情不错。"
            }
        }
        
        call_response = session.post(f"{BASE_URL}/api/v1/ai/call", json=call_data)
        print(f"   调用AI功能状态: {call_response.status_code}")
        if call_response.status_code == 200:
            call_result = call_response.json()
            print(f"   ✓ 调用AI功能成功")
            print(f"   调用结果: {json.dumps(call_result, ensure_ascii=False, indent=2)}")
        else:
            print(f"   ❌ 调用AI功能失败: {call_response.text}")
    else:
        print("   跳过调用AI功能（功能创建失败）")
    
    # 6. 测试获取 AI 统计信息
    print("\n6. 测试获取 AI 统计信息...")
    stats_response = session.get(f"{BASE_URL}/api/v1/ai/stats")
    print(f"   获取AI统计状态: {stats_response.status_code}")
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"   ✓ 获取AI统计成功")
        print(f"   统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    else:
        print(f"   ❌ 获取AI统计失败: {stats_response.text}")
    
    # 7. 测试获取 AI 调用日志
    print("\n7. 测试获取 AI 调用日志...")
    logs_response = session.get(f"{BASE_URL}/api/v1/ai/logs")
    print(f"   获取调用日志状态: {logs_response.status_code}")
    if logs_response.status_code == 200:
        logs = logs_response.json()
        print(f"   ✓ 获取调用日志成功")
        print(f"   日志数量: {logs.get('total', 0)}")
        if logs.get('items'):
            print(f"   最新日志: {logs['items'][0]['status']}")
    else:
        print(f"   ❌ 获取调用日志失败: {logs_response.text}")
    
    print("=" * 50)
    print("AI 管理 API 测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_ai_apis()
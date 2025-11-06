#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拉取OPSIGHT系统中的实际数据记录
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://127.0.0.1:8000'

def fetch_all_data():
    """拉取所有数据"""
    # 登录获取session
    login_data = {'username': 'admin', 'password': 'admin123'}
    session = requests.Session()
    login_response = session.post(f'{BASE_URL}/api/v1/auth/login', json=login_data)
    
    if login_response.status_code != 200:
        print(f'登录失败: {login_response.status_code}')
        return
    
    print('登录成功，开始拉取数据...\n')
    
    # 1. 拉取用户信息
    print('=== 用户账号信息 ===')
    users_response = session.get(f'{BASE_URL}/api/v1/users')
    if users_response.status_code == 200:
        users = users_response.json()
        print(f'总用户数: {len(users)}')
        print()
        
        for user in users:
            print(f'用户ID: {user.get("id")}')
            print(f'用户名: {user.get("username")}')
            print(f'角色: {user.get("role")}')
            print(f'身份类型: {user.get("identity_type")}')
            print(f'组织: {user.get("organization", "未设置")}')
            print(f'用户组: {user.get("group_name", "未分组")}')
            print(f'激活状态: {"是" if user.get("is_active") else "否"}')
            print(f'创建时间: {user.get("created_at", "未知")}')
            print('-' * 40)
    else:
        print(f'获取用户失败: {users_response.status_code}')
    
    # 2. 拉取用户组信息
    print('\n=== 用户组信息 ===')
    groups_response = session.get(f'{BASE_URL}/api/v1/groups')
    if groups_response.status_code == 200:
        groups = groups_response.json()
        print(f'总用户组数: {len(groups)}')
        print()
        
        for group in groups:
            print(f'组ID: {group.get("id")}')
            print(f'组名: {group.get("name")}')
            print(f'描述: {group.get("description", "无描述")}')
            print('-' * 40)
    else:
        print(f'获取用户组失败: {groups_response.status_code}')
    
    # 3. 拉取任务信息
    print('\n=== 任务记录 ===')
    tasks_response = session.get(f'{BASE_URL}/api/v1/tasks')
    if tasks_response.status_code == 200:
        tasks_data = tasks_response.json()
        tasks = tasks_data.get('items', []) if isinstance(tasks_data, dict) else tasks_data
        print(f'总任务数: {len(tasks)}')
        print()
        
        for task in tasks:
            print(f'任务ID: {task.get("id")}')
            print(f'标题: {task.get("title")}')
            print(f'类型: {task.get("task_type")}')
            print(f'状态: {task.get("status")}')
            print(f'优先级: {task.get("priority")}')
            print(f'创建者: {task.get("created_by")}')
            print(f'分配类型: {task.get("assignment_type")}')
            if task.get("assigned_user_id"):
                print(f'分配用户ID: {task.get("assigned_user_id")}')
            if task.get("assigned_group_id"):
                print(f'分配用户组ID: {task.get("assigned_group_id")}')
            if task.get("assigned_identity"):
                print(f'分配身份: {task.get("assigned_identity")}')
            print(f'创建时间: {task.get("created_at", "未知")}')
            print('-' * 40)
    else:
        print(f'获取任务失败: {tasks_response.status_code}')
    
    # 4. 拉取日报信息
    print('\n=== 日报记录 ===')
    reports_response = session.get(f'{BASE_URL}/api/v1/reports')
    if reports_response.status_code == 200:
        reports_data = reports_response.json()
        reports = reports_data.get('items', []) if isinstance(reports_data, dict) else reports_data
        print(f'总日报数: {len(reports)}')
        print()
        
        for report in reports:
            print(f'日报ID: {report.get("id")}')
            print(f'用户ID: {report.get("user_id")}')
            print(f'工作日期: {report.get("work_date")}')
            print(f'标题: {report.get("title")}')
            print(f'工作时长: {report.get("work_hours")}小时')
            print(f'心情评分: {report.get("mood_score")}/10')
            print(f'效率评分: {report.get("efficiency_score")}/10')
            print(f'通话次数: {report.get("call_count", 0)}')
            print(f'通话时长: {report.get("call_duration", 0)}分钟')
            print(f'创建时间: {report.get("created_at", "未知")}')
            print('-' * 40)
    else:
        print(f'获取日报失败: {reports_response.status_code}')
    
    # 5. 拉取AI智能体配置
    print('\n=== AI智能体配置 ===')
    agents_response = session.get(f'{BASE_URL}/api/v1/ai/agents')
    if agents_response.status_code == 200:
        agents = agents_response.json()
        print(f'总智能体数: {len(agents)}')
        print()
        
        for agent in agents:
            print(f'智能体ID: {agent.get("id")}')
            print(f'名称: {agent.get("name")}')
            print(f'描述: {agent.get("description", "无描述")}')
            print(f'提供商: {agent.get("provider")}')
            print(f'模型: {agent.get("model_name")}')
            print(f'温度: {agent.get("temperature")}')
            print(f'最大Token: {agent.get("max_tokens")}')
            print(f'启用状态: {"是" if agent.get("is_active") else "否"}')
            print(f'默认智能体: {"是" if agent.get("is_default") else "否"}')
            print(f'创建时间: {agent.get("created_at", "未知")}')
            print('-' * 40)
    else:
        print(f'获取AI智能体失败: {agents_response.status_code}')
    
    # 6. 拉取AI功能配置
    print('\n=== AI功能配置 ===')
    functions_response = session.get(f'{BASE_URL}/api/v1/ai/functions')
    if functions_response.status_code == 200:
        functions = functions_response.json()
        print(f'总AI功能数: {len(functions)}')
        print()
        
        for func in functions:
            print(f'功能ID: {func.get("id")}')
            print(f'名称: {func.get("name")}')
            print(f'类型: {func.get("function_type")}')
            print(f'描述: {func.get("description", "无描述")}')
            print(f'关联智能体ID: {func.get("agent_id")}')
            print(f'启用状态: {"是" if func.get("is_active") else "否"}')
            print(f'创建时间: {func.get("created_at", "未知")}')
            print('-' * 40)
    else:
        print(f'获取AI功能失败: {functions_response.status_code}')

if __name__ == "__main__":
    fetch_all_data()
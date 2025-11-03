#!/usr/bin/env python3
import requests

session = requests.Session()
login_resp = session.post('http://localhost:8000/api/v1/auth/login', json={'username': 'admin', 'password': 'admin123'})

if login_resp.status_code == 200:
    session.cookies.update(login_resp.cookies)
    
    # 获取用户信息
    user_resp = session.get('http://localhost:8000/api/v1/auth/me')
    if user_resp.status_code == 200:
        user = user_resp.json()
        print(f"当前用户: {user.get('username')}")
        print(f"用户ID: {user.get('id')}")
        print(f"用户角色: {user.get('role')}")
        print(f"用户身份: {user.get('identity_type')}")
        print(f"用户组ID: {user.get('group_id')}")
        print()
    
    # 获取任务4的信息
    task_resp = session.get('http://localhost:8000/api/v1/tasks/4')
    if task_resp.status_code == 200:
        task = task_resp.json()
        print(f"任务ID: {task.get('id')}")
        print(f"任务标题: {task.get('title')}")
        print(f"任务类型: {task.get('task_type')}")
        print(f"分配类型: {task.get('assignment_type')}")
        print(f"分配给用户: {task.get('assigned_to')}")
        print(f"目标组ID: {task.get('target_group_id')}")
        print(f"目标身份: {task.get('target_identity')}")
    else:
        print(f"获取任务失败: {task_resp.status_code} - {task_resp.text}")
else:
    print(f"登录失败: {login_resp.status_code} - {login_resp.text}")
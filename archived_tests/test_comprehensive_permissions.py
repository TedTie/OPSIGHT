#!/usr/bin/env python3
"""
全面的权限功能测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_user_login(username, password="admin123"):
    """测试用户登录"""
    print(f"\n登录用户: {username}")
    
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    
    if login_response.status_code == 200:
        print(f"✅ 登录成功")
        session = requests.Session()
        session.cookies.update(login_response.cookies)
        user_data = login_response.json().get('user', {})
        return session, user_data
    else:
        print(f"❌ 登录失败: {login_response.text}")
        return None, None

def test_task_permissions(session, user_data, task_id, task_type):
    """测试任务权限"""
    username = user_data.get('username', 'unknown')
    role = user_data.get('role', 'unknown')
    
    print(f"\n测试用户 {username} ({role}) 对任务 {task_id} ({task_type}) 的权限:")
    
    results = {}
    
    # 1. 测试查看任务详情
    try:
        response = session.get(f"{BASE_URL}/tasks/{task_id}")
        results['view_task'] = {
            'status': response.status_code,
            'success': response.status_code == 200
        }
        print(f"  查看任务: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        results['view_task'] = {'status': 'error', 'success': False, 'error': str(e)}
        print(f"  查看任务: ❌ {e}")
    
    # 2. 测试编辑任务
    try:
        response = session.put(f"{BASE_URL}/tasks/{task_id}", json={
            "title": f"测试编辑-{username}",
            "description": "权限测试"
        })
        results['edit_task'] = {
            'status': response.status_code,
            'success': response.status_code == 200
        }
        print(f"  编辑任务: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        results['edit_task'] = {'status': 'error', 'success': False, 'error': str(e)}
        print(f"  编辑任务: ❌ {e}")
    
    # 3. 根据任务类型测试相应的操作
    if task_type == 'checkbox':
        # 测试完成任务
        try:
            response = session.post(f"{BASE_URL}/tasks/{task_id}/complete", json={
                "completion_data": {"completion_note": f"测试完成-{username}"}
            })
            results['complete_task'] = {
                'status': response.status_code,
                'success': response.status_code == 200
            }
            print(f"  完成任务: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        except Exception as e:
            results['complete_task'] = {'status': 'error', 'success': False, 'error': str(e)}
            print(f"  完成任务: ❌ {e}")
    
    elif task_type == 'amount':
        # 测试金额参与
        try:
            response = session.post(f"{BASE_URL}/tasks/{task_id}/amount", params={
                "amount": 50.0,
                "note": f"测试参与-{username}"
            })
            results['participate_amount'] = {
                'status': response.status_code,
                'success': response.status_code == 200
            }
            print(f"  金额参与: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        except Exception as e:
            results['participate_amount'] = {'status': 'error', 'success': False, 'error': str(e)}
            print(f"  金额参与: ❌ {e}")
    
    elif task_type == 'quantity':
        # 测试数量参与
        try:
            response = session.post(f"{BASE_URL}/tasks/{task_id}/quantity", params={
                "quantity": 2,
                "note": f"测试参与-{username}"
            })
            results['participate_quantity'] = {
                'status': response.status_code,
                'success': response.status_code == 200
            }
            print(f"  数量参与: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        except Exception as e:
            results['participate_quantity'] = {'status': 'error', 'success': False, 'error': str(e)}
            print(f"  数量参与: ❌ {e}")
    
    elif task_type == 'jielong':
        # 测试接龙参与
        try:
            response = session.post(f"{BASE_URL}/tasks/{task_id}/jielong", json={
                "entry_data": {"name": username, "content": f"测试接龙-{username}"}
            })
            results['participate_jielong'] = {
                'status': response.status_code,
                'success': response.status_code == 200
            }
            print(f"  接龙参与: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
        except Exception as e:
            results['participate_jielong'] = {'status': 'error', 'success': False, 'error': str(e)}
            print(f"  接龙参与: ❌ {e}")
    
    return results

def test_admin_permissions(session, user_data):
    """测试管理员权限"""
    username = user_data.get('username', 'unknown')
    role = user_data.get('role', 'unknown')
    
    print(f"\n测试用户 {username} ({role}) 的管理员权限:")
    
    results = {}
    
    # 1. 测试创建任务
    try:
        response = session.post(f"{BASE_URL}/tasks", json={
            "title": f"权限测试任务-{username}",
            "description": "测试管理员创建任务权限",
            "task_type": "checkbox",
            "assignment_type": "all"
        })
        results['create_task'] = {
            'status': response.status_code,
            'success': response.status_code in [200, 201]
        }
        print(f"  创建任务: {response.status_code} {'✅' if response.status_code in [200, 201] else '❌'}")
    except Exception as e:
        results['create_task'] = {'status': 'error', 'success': False, 'error': str(e)}
        print(f"  创建任务: ❌ {e}")
    
    # 2. 测试获取用户列表
    try:
        response = session.get(f"{BASE_URL}/users")
        results['list_users'] = {
            'status': response.status_code,
            'success': response.status_code == 200
        }
        print(f"  获取用户列表: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        results['list_users'] = {'status': 'error', 'success': False, 'error': str(e)}
        print(f"  获取用户列表: ❌ {e}")
    
    # 3. 测试获取组列表
    try:
        response = session.get(f"{BASE_URL}/groups")
        results['list_groups'] = {
            'status': response.status_code,
            'success': response.status_code == 200
        }
        print(f"  获取组列表: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        results['list_groups'] = {'status': 'error', 'success': False, 'error': str(e)}
        print(f"  获取组列表: ❌ {e}")
    
    return results

def main():
    """主测试函数"""
    print("🔐 开始全面权限功能测试...")
    print("=" * 60)
    
    # 测试用户列表
    test_users = [
        "admin",  # 超级管理员
        # 可以添加更多测试用户
    ]
    
    all_results = {}
    
    for username in test_users:
        session, user_data = test_user_login(username)
        if not session:
            continue
        
        user_results = {
            'user_info': user_data,
            'admin_permissions': {},
            'task_permissions': {}
        }
        
        # 测试管理员权限
        user_results['admin_permissions'] = test_admin_permissions(session, user_data)
        
        # 获取任务列表并测试任务权限
        try:
            tasks_response = session.get(f"{BASE_URL}/tasks")
            if tasks_response.status_code == 200:
                tasks_data = tasks_response.json()
                if isinstance(tasks_data, dict):
                    tasks = tasks_data.get('items', []) or tasks_data.get('data', []) or []
                else:
                    tasks = tasks_data if isinstance(tasks_data, list) else []
                
                # 测试前3个不同类型的任务
                tested_types = set()
                for task in tasks:
                    task_type = task.get('task_type')
                    if task_type not in tested_types and len(tested_types) < 3:
                        task_id = task.get('id')
                        user_results['task_permissions'][f'task_{task_id}_{task_type}'] = test_task_permissions(
                            session, user_data, task_id, task_type
                        )
                        tested_types.add(task_type)
        except Exception as e:
            print(f"❌ 获取任务列表失败: {e}")
        
        all_results[username] = user_results
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("🎯 权限测试总结:")
    
    for username, results in all_results.items():
        user_info = results['user_info']
        role = user_info.get('role', 'unknown')
        print(f"\n👤 用户: {username} ({role})")
        
        # 管理员权限总结
        admin_perms = results['admin_permissions']
        admin_success = sum(1 for perm in admin_perms.values() if perm.get('success', False))
        admin_total = len(admin_perms)
        print(f"  管理员权限: {admin_success}/{admin_total} 通过")
        
        # 任务权限总结
        task_perms = results['task_permissions']
        task_success = 0
        task_total = 0
        for task_result in task_perms.values():
            for perm in task_result.values():
                if perm.get('success', False):
                    task_success += 1
                task_total += 1
        print(f"  任务权限: {task_success}/{task_total} 通过")
    
    # 保存详细结果
    with open('permission_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细测试结果已保存到 permission_test_results.json")
    print("✅ 权限测试完成!")

if __name__ == "__main__":
    main()
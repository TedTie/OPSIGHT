#!/usr/bin/env python3
"""
测试超级管理员功能
验证超级管理员可以查看所有数据，而普通管理员只能查看其组织数据
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"

def test_login(username):
    """测试登录"""
    print(f"\n=== 测试用户 {username} 登录 ===")
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                           json={"username": username})
    
    if response.status_code == 200:
        data = response.json()
        user = data.get("user", {})
        print(f"✅ 登录成功")
        print(f"   用户名: {user.get('username')}")
        print(f"   角色: {user.get('role')}")
        print(f"   组织: {user.get('organization')}")
        print(f"   是否管理员: {user.get('is_admin')}")
        print(f"   是否超级管理员: {user.get('is_super_admin')}")
        
        # 获取cookies
        cookies = response.cookies
        return cookies, user
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"   错误信息: {response.text}")
        return None, None

def test_analytics_dashboard(cookies, user_info):
    """测试分析仪表板API"""
    print(f"\n=== 测试分析仪表板 ({user_info.get('username')}) ===")
    
    response = requests.get(f"{BASE_URL}/api/v1/analytics/dashboard", 
                          cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取分析数据成功")
        print(f"   任务总数: {data.get('total_tasks', 0)}")
        print(f"   日报总数: {data.get('total_reports', 0)}")
        print(f"   用户总数: {data.get('total_users', 0)}")
        
        # 显示任务数据范围
        tasks = data.get('recent_tasks', [])
        if tasks:
            print(f"   最近任务数量: {len(tasks)}")
            # 显示任务所属用户
            task_users = set(task.get('username') for task in tasks if task.get('username'))
            print(f"   任务涉及用户: {', '.join(task_users) if task_users else '无'}")
        
        # 显示日报数据范围
        reports = data.get('recent_reports', [])
        if reports:
            print(f"   最近日报数量: {len(reports)}")
            # 显示日报所属用户
            report_users = set(report.get('username') for report in reports if report.get('username'))
            print(f"   日报涉及用户: {', '.join(report_users) if report_users else '无'}")
            
        return data
    else:
        print(f"❌ 获取分析数据失败: {response.status_code}")
        print(f"   错误信息: {response.text}")
        return None

def test_admin_metrics(cookies, user_info):
    """测试管理员指标API"""
    print(f"\n=== 测试管理员指标 ({user_info.get('username')}) ===")
    
    response = requests.get(f"{BASE_URL}/api/v1/admin/metrics/stats", 
                          cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 获取管理员指标成功")
        print(f"   总用户数: {data.get('total_users', 0)}")
        print(f"   活跃用户数: {data.get('active_users', 0)}")
        print(f"   总任务数: {data.get('total_tasks', 0)}")
        print(f"   总日报数: {data.get('total_reports', 0)}")
        return data
    else:
        print(f"❌ 获取管理员指标失败: {response.status_code}")
        print(f"   错误信息: {response.text}")
        return None

def test_user_list(cookies, user_info):
    """测试用户列表API"""
    print(f"\n=== 测试用户列表 ({user_info.get('username')}) ===")
    
    response = requests.get(f"{BASE_URL}/api/v1/users", 
                          cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        users = data.get('items', [])
        print(f"✅ 获取用户列表成功")
        print(f"   用户总数: {data.get('total', 0)}")
        print(f"   当前页用户数: {len(users)}")
        
        # 显示用户信息
        for user in users[:5]:  # 只显示前5个用户
            print(f"   - {user.get('username')} ({user.get('role')}) - {user.get('organization', '无组织')}")
            
        return data
    else:
        print(f"❌ 获取用户列表失败: {response.status_code}")
        print(f"   错误信息: {response.text}")
        return None

def main():
    """主测试函数"""
    print("🚀 开始测试超级管理员功能")
    
    # 测试超级管理员
    print("\n" + "="*60)
    print("测试超级管理员 (admin)")
    print("="*60)
    
    admin_cookies, admin_info = test_login("admin")
    if admin_cookies and admin_info:
        # 验证超级管理员标识
        if admin_info.get('is_super_admin'):
            print("✅ 超级管理员标识正确")
        else:
            print("❌ 超级管理员标识错误")
            
        # 测试各种API
        admin_analytics = test_analytics_dashboard(admin_cookies, admin_info)
        admin_metrics = test_admin_metrics(admin_cookies, admin_info)
        admin_users = test_user_list(admin_cookies, admin_info)
    
    # 测试普通管理员
    print("\n" + "="*60)
    print("测试普通管理员 (jlpss-chenjianxiong)")
    print("="*60)
    
    manager_cookies, manager_info = test_login("jlpss-chenjianxiong")
    if manager_cookies and manager_info:
        # 验证管理员标识
        if manager_info.get('is_admin') and not manager_info.get('is_super_admin'):
            print("✅ 普通管理员标识正确")
        else:
            print("❌ 普通管理员标识错误")
            
        # 测试各种API
        manager_analytics = test_analytics_dashboard(manager_cookies, manager_info)
        manager_metrics = test_admin_metrics(manager_cookies, manager_info)
        manager_users = test_user_list(manager_cookies, manager_info)
    
    # 对比分析
    print("\n" + "="*60)
    print("权限对比分析")
    print("="*60)
    
    if admin_cookies and manager_cookies:
        print("\n📊 数据访问范围对比:")
        
        # 对比分析数据
        if admin_analytics and manager_analytics:
            admin_task_count = len(admin_analytics.get('recent_tasks', []))
            manager_task_count = len(manager_analytics.get('recent_tasks', []))
            
            print(f"   超级管理员可见任务数: {admin_task_count}")
            print(f"   普通管理员可见任务数: {manager_task_count}")
            
            if admin_task_count >= manager_task_count:
                print("   ✅ 超级管理员数据访问范围 >= 普通管理员")
            else:
                print("   ❌ 超级管理员数据访问范围 < 普通管理员 (异常)")
        
        # 对比用户列表
        if admin_users and manager_users:
            admin_user_count = admin_users.get('total', 0)
            manager_user_count = manager_users.get('total', 0)
            
            print(f"   超级管理员可见用户数: {admin_user_count}")
            print(f"   普通管理员可见用户数: {manager_user_count}")
            
            if admin_user_count >= manager_user_count:
                print("   ✅ 超级管理员用户访问范围 >= 普通管理员")
            else:
                print("   ❌ 超级管理员用户访问范围 < 普通管理员 (异常)")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main()
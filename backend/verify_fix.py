#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPSIGHT 任务可见性修复验证脚本
按照指令文档第4节验证步骤进行测试
"""

import requests
import json
import sys
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

class APITester:
    def __init__(self):
        self.sessions = {}
        
    def login(self, username: str, password: str) -> bool:
        """登录并建立session"""
        try:
            # 为每个用户创建独立的session
            session = requests.Session()
            response = session.post(
                f"{BASE_URL}/auth/login",
                json={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.sessions[username] = session
                print(f"✅ {username} 登录成功")
                return True
            else:
                print(f"❌ {username} 登录失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ {username} 登录异常: {e}")
            return False
    
    def get_tasks(self, username: str, page: int = 1, size: int = 100) -> Dict[str, Any]:
        """获取任务列表"""
        session = self.sessions.get(username)
        if not session:
            return {"error": "未登录"}
            
        try:
            response = session.get(f"{BASE_URL}/tasks?page={page}&size={size}")
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                tasks = response.json()
                result["task_count"] = len(tasks)
                result["tasks"] = tasks
                print(f"✅ {username} 获取任务列表成功: {len(tasks)} 个任务")
            else:
                result["error"] = response.text
                print(f"❌ {username} 获取任务列表失败: {response.status_code} - {response.text}")
                
            return result
        except Exception as e:
            print(f"❌ {username} 获取任务列表异常: {e}")
            return {"error": str(e)}
    
    def get_single_task(self, username: str, task_id: int) -> Dict[str, Any]:
        """获取单个任务"""
        session = self.sessions.get(username)
        if not session:
            return {"error": "未登录"}
            
        try:
            response = session.get(f"{BASE_URL}/tasks/{task_id}")
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                task = response.json()
                result["task"] = task
                print(f"✅ {username} 获取任务 {task_id} 成功: {task.get('title', 'N/A')}")
            elif response.status_code == 403:
                result["forbidden"] = True
                print(f"🔒 {username} 访问任务 {task_id} 被拒绝 (403 Forbidden) - 符合预期")
            else:
                result["error"] = response.text
                print(f"❌ {username} 获取任务 {task_id} 失败: {response.status_code} - {response.text}")
                
            return result
        except Exception as e:
            print(f"❌ {username} 获取任务 {task_id} 异常: {e}")
            return {"error": str(e)}

def main():
    """主验证流程"""
    print("🚀 开始OPSIGHT任务可见性修复验证")
    print("=" * 60)
    
    tester = APITester()
    
    # 步骤4.1: 获取test_user的Token
    print("\n📋 步骤4.1: 登录test_user")
    test_user_login = tester.login("test_user", "123456")
    if not test_user_login:
        print("❌ 无法登录test_user，终止验证")
        return False
    
    # 步骤4.2: 使用test_user进行验证
    print("\n📋 步骤4.2: 使用test_user进行验证")
    
    # 测试用例1: 获取任务列表
    print("\n🧪 测试用例1: test_user获取任务列表")
    tasks_result = tester.get_tasks("test_user")
    if tasks_result.get("success"):
        task_count = tasks_result.get("task_count", 0)
        if task_count == 6:
            print(f"✅ 预期结果: test_user应该看到6个任务，实际看到{task_count}个任务")
        else:
            print(f"⚠️  预期6个任务，实际看到{task_count}个任务")
            # 显示任务详情用于调试
            if "tasks" in tasks_result:
                print("任务详情:")
                for task in tasks_result["tasks"]:
                    print(f"  - ID:{task.get('id')} 标题:{task.get('title')} 分配类型:{task.get('assignment_type')}")
    else:
        print(f"❌ 获取任务列表失败")
        return False
    
    # 测试用例2: test_user访问任务31 (分配给all)
    print("\n🧪 测试用例2: test_user访问任务31 (分配给all)")
    task31_result = tester.get_single_task("test_user", 31)
    if not task31_result.get("success"):
        print("❌ test_user应该能访问任务31")
        return False
    
    # 测试用例3: test_user访问任务37 (分配给test_user)
    print("\n🧪 测试用例3: test_user访问任务37 (分配给test_user)")
    task37_result = tester.get_single_task("test_user", 37)
    if not task37_result.get("success"):
        print("❌ test_user应该能访问任务37")
        return False
    
    # 测试用例4: test_user访问任务39 (分配给组1)
    print("\n🧪 测试用例4: test_user访问任务39 (分配给组1)")
    task39_result = tester.get_single_task("test_user", 39)
    if not task39_result.get("success"):
        print("❌ test_user应该能访问任务39")
        return False
    
    # 测试用例5: test_user无法访问任务36 (分配给jlpss-chenjianxiong)
    print("\n🧪 测试用例5: test_user访问任务36 (分配给jlpss-chenjianxiong)")
    task36_result = tester.get_single_task("test_user", 36)
    if task36_result.get("status_code") == 403:
        print("✅ test_user正确被拒绝访问任务36")
    else:
        print("❌ test_user不应该能访问任务36")
        return False
    
    # 测试用例6: test_user无法访问任务40 (分配给组2)
    print("\n🧪 测试用例6: test_user访问任务40 (分配给组2)")
    task40_result = tester.get_single_task("test_user", 40)
    if task40_result.get("status_code") == 403:
        print("✅ test_user正确被拒绝访问任务40")
    else:
        print("❌ test_user不应该能访问任务40")
        return False
    
    # 步骤4.3: admin回归测试
    print("\n📋 步骤4.3: 使用admin进行回归测试")
    
    # admin登录
    admin_login = tester.login("admin", "admin123")
    if not admin_login:
        print("❌ admin 登录失败")
        return False
    print("✅ admin 登录成功")
    
    # admin获取任务列表
    admin_tasks = tester.get_tasks("admin", size=100)
    if not admin_tasks.get("success"):
        print("❌ admin 获取任务列表失败")
        return False
    
    admin_task_count = len(admin_tasks.get("tasks", []))
    print(f"✅ admin 获取任务列表成功: {admin_task_count} 个任务")
    
    if admin_task_count == 10:
        print("✅ 预期结果: admin应该看到10个任务，实际看到10个任务")
    else:
        print(f"❌ 预期结果: admin应该看到10个任务，实际看到{admin_task_count}个任务")
        return False
    
    admin_tasks_result = admin_tasks
    
    print("\n" + "=" * 60)
    print("🎉 所有验证测试完成！")
    
    # 总结
    test_user_tasks = tasks_result.get("task_count", 0)
    admin_tasks = admin_tasks_result.get("task_count", 0)
    
    if test_user_tasks == 6 and admin_tasks == 10:
        print("✅ P0级任务可见性逻辑修复已完成，所有验证测试通过。")
        return True
    else:
        print(f"⚠️  部分测试未达到预期: test_user={test_user_tasks}/6, admin={admin_tasks}/10")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
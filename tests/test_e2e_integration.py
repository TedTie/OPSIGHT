#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPSIGHT 端到端集成测试脚本
综合测试前端、后端、数据库的完整功能流程
"""

import requests
import json
import time
import random
import string
from datetime import datetime, timedelta

class E2EIntegrationTester:
    def __init__(self):
        self.frontend_url = "http://localhost:3001"
        self.backend_url = "http://localhost:8001"
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_id = None
        self.test_task_id = None
        
    def log_test(self, test_name, status, message, details=None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {status} {test_name} - {message}")
        
        if details:
            print(f"   详情: {details}")
    
    def test_system_health(self):
        """测试系统健康状态"""
        print("\n🏥 系统健康检查:")
        
        # 测试后端健康状态
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("后端健康检查", "PASS", f"后端服务正常，状态码: {response.status_code}")
            else:
                self.log_test("后端健康检查", "FAIL", f"后端服务异常，状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("后端健康检查", "FAIL", f"后端连接失败: {e}")
            return False
        
        # 测试前端可访问性
        try:
            response = self.session.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log_test("前端健康检查", "PASS", f"前端服务正常，状态码: {response.status_code}")
            else:
                self.log_test("前端健康检查", "FAIL", f"前端服务异常，状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("前端健康检查", "FAIL", f"前端连接失败: {e}")
            return False
        
        return True
    
    def test_authentication_flow(self):
        """测试完整的认证流程"""
        print("\n🔐 认证流程测试:")
        
        # 1. 测试登录
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # 检查登录是否成功（session-based认证）
                if "message" in data and "登录成功" in data["message"]:
                    # 获取用户信息
                    if "user" in data:
                        user_data = data["user"]
                        self.test_user_id = user_data.get("id")
                        self.log_test("用户登录", "PASS", f"登录成功，用户: {user_data.get('username')}")
                    else:
                        self.log_test("用户登录", "PASS", "登录成功（session-based认证）")
                elif "access_token" in data:
                    # 如果有token，也支持token认证
                    self.auth_token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("用户登录", "PASS", "登录成功，获取到访问令牌")
                else:
                    self.log_test("用户登录", "FAIL", "登录响应格式异常")
                    return False
            else:
                self.log_test("用户登录", "FAIL", f"登录失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("用户登录", "FAIL", f"登录异常: {e}")
            return False
        
        # 2. 测试获取当前用户信息
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/auth/me", timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data.get("id")
                self.log_test("获取用户信息", "PASS", f"成功获取用户信息，用户ID: {self.test_user_id}")
            else:
                self.log_test("获取用户信息", "FAIL", f"获取用户信息失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("获取用户信息", "FAIL", f"获取用户信息异常: {e}")
            return False
        
        # 3. 测试认证检查
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/auth/check", timeout=10)
            
            if response.status_code == 200:
                self.log_test("认证状态检查", "PASS", "认证状态正常")
            else:
                self.log_test("认证状态检查", "FAIL", f"认证状态异常，状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test("认证状态检查", "FAIL", f"认证检查异常: {e}")
        
        return True
    
    def test_user_management_flow(self):
        """测试用户管理流程"""
        print("\n👥 用户管理流程测试:")
        
        # 1. 获取用户列表
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/users", timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                user_count = len(users) if isinstance(users, list) else 0
                self.log_test("获取用户列表", "PASS", f"成功获取用户列表，用户数量: {user_count}")
            else:
                self.log_test("获取用户列表", "FAIL", f"获取用户列表失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("获取用户列表", "FAIL", f"获取用户列表异常: {e}")
            return False
        
        # 2. 获取特定用户信息
        if self.test_user_id:
            try:
                response = self.session.get(f"{self.backend_url}/api/v1/users/{self.test_user_id}", timeout=10)
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_test("获取特定用户", "PASS", f"成功获取用户详情，用户名: {user_data.get('username', 'N/A')}")
                else:
                    self.log_test("获取特定用户", "FAIL", f"获取用户详情失败，状态码: {response.status_code}")
                    
            except Exception as e:
                self.log_test("获取特定用户", "FAIL", f"获取用户详情异常: {e}")
        
        return True
    
    def test_task_management_flow(self):
        """测试任务管理完整流程"""
        print("\n📝 任务管理流程测试:")
        
        # 1. 获取任务列表
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/tasks", timeout=10)
            
            if response.status_code == 200:
                tasks = response.json()
                task_count = len(tasks) if isinstance(tasks, list) else 0
                self.log_test("获取任务列表", "PASS", f"成功获取任务列表，任务数量: {task_count}")
                
                # 如果有任务，记录第一个任务ID用于后续测试
                if task_count > 0 and isinstance(tasks, list):
                    self.test_task_id = tasks[0].get("id")
            else:
                self.log_test("获取任务列表", "FAIL", f"获取任务列表失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("获取任务列表", "FAIL", f"获取任务列表异常: {e}")
            return False
        
        # 2. 创建新任务
        try:
            task_data = {
                "title": f"集成测试任务_{int(time.time())}",
                "description": "这是一个端到端集成测试创建的任务",
                "priority": "medium",
                "due_date": (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/v1/tasks",
                json=task_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                created_task = response.json()
                new_task_id = created_task.get("id")
                self.log_test("创建新任务", "PASS", f"成功创建任务，任务ID: {new_task_id}")
                
                # 使用新创建的任务ID进行后续测试
                if new_task_id:
                    self.test_task_id = new_task_id
            else:
                self.log_test("创建新任务", "FAIL", f"创建任务失败，状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test("创建新任务", "FAIL", f"创建任务异常: {e}")
        
        # 3. 获取特定任务详情
        if self.test_task_id:
            try:
                response = self.session.get(f"{self.backend_url}/api/v1/tasks/{self.test_task_id}", timeout=10)
                
                if response.status_code == 200:
                    task_data = response.json()
                    self.log_test("获取任务详情", "PASS", f"成功获取任务详情，标题: {task_data.get('title', 'N/A')}")
                else:
                    self.log_test("获取任务详情", "FAIL", f"获取任务详情失败，状态码: {response.status_code}")
                    
            except Exception as e:
                self.log_test("获取任务详情", "FAIL", f"获取任务详情异常: {e}")
        
        # 4. 更新任务状态
        if self.test_task_id:
            try:
                status_data = {"status": "in_progress"}
                response = self.session.put(
                    f"{self.backend_url}/api/v1/tasks/{self.test_task_id}/status",
                    json=status_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test("更新任务状态", "PASS", "成功更新任务状态为进行中")
                else:
                    self.log_test("更新任务状态", "FAIL", f"更新任务状态失败，状态码: {response.status_code}")
                    
            except Exception as e:
                self.log_test("更新任务状态", "FAIL", f"更新任务状态异常: {e}")
        
        return True
    
    def test_analytics_flow(self):
        """测试数据分析流程"""
        print("\n📊 数据分析流程测试:")
        
        # 1. 测试分析仪表板API
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/analytics/dashboard", timeout=10)
            
            if response.status_code == 200:
                dashboard_data = response.json()
                self.log_test("分析仪表板", "PASS", "成功获取仪表板数据", 
                            f"数据键: {list(dashboard_data.keys()) if isinstance(dashboard_data, dict) else 'N/A'}")
            else:
                self.log_test("分析仪表板", "FAIL", f"获取仪表板数据失败，状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test("分析仪表板", "FAIL", f"获取仪表板数据异常: {e}")
        
        # 2. 测试任务类型分析API
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/analytics/task-types", timeout=10)
            
            if response.status_code == 200:
                task_types_data = response.json()
                self.log_test("任务类型分析", "PASS", "成功获取任务类型分析数据",
                            f"数据类型: {type(task_types_data).__name__}")
            else:
                self.log_test("任务类型分析", "FAIL", f"获取任务类型分析失败，状态码: {response.status_code}")
                
        except Exception as e:
            self.log_test("任务类型分析", "FAIL", f"获取任务类型分析异常: {e}")
        
        return True
    
    def test_frontend_integration(self):
        """测试前端集成"""
        print("\n🌐 前端集成测试:")
        
        # 测试主要页面的可访问性
        pages = [
            ("/", "主页"),
            ("/dashboard", "仪表板"),
            ("/tasks", "任务管理"),
            ("/analytics", "数据分析"),
            ("/users", "用户管理")
        ]
        
        for path, name in pages:
            try:
                response = self.session.get(f"{self.frontend_url}{path}", timeout=10)
                
                if response.status_code == 200:
                    content = response.text
                    # 检查页面是否包含Vue应用
                    has_vue = 'vue' in content.lower() or 'app' in content.lower()
                    # 检查是否有错误
                    has_error = 'error' in content.lower() or '404' in content
                    
                    if has_vue and not has_error:
                        self.log_test(f"前端{name}页面", "PASS", "页面正常加载且包含Vue应用")
                    else:
                        self.log_test(f"前端{name}页面", "PARTIAL", "页面可访问但可能存在问题")
                else:
                    self.log_test(f"前端{name}页面", "FAIL", f"页面访问失败，状态码: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"前端{name}页面", "FAIL", f"页面访问异常: {e}")
        
        return True
    
    def test_data_persistence(self):
        """测试数据持久化"""
        print("\n💾 数据持久化测试:")
        
        # 创建一个测试任务，然后验证它是否被正确保存
        try:
            # 创建任务
            task_data = {
                "title": f"持久化测试任务_{int(time.time())}",
                "description": "测试数据持久化功能",
                "priority": "low"
            }
            
            create_response = self.session.post(
                f"{self.backend_url}/api/v1/tasks",
                json=task_data,
                timeout=10
            )
            
            if create_response.status_code in [200, 201]:
                created_task = create_response.json()
                task_id = created_task.get("id")
                
                # 等待一下确保数据已保存
                time.sleep(1)
                
                # 重新获取任务验证持久化
                get_response = self.session.get(f"{self.backend_url}/api/v1/tasks/{task_id}", timeout=10)
                
                if get_response.status_code == 200:
                    retrieved_task = get_response.json()
                    if retrieved_task.get("title") == task_data["title"]:
                        self.log_test("数据持久化", "PASS", "任务数据成功持久化到数据库")
                    else:
                        self.log_test("数据持久化", "FAIL", "任务数据持久化后内容不匹配")
                else:
                    self.log_test("数据持久化", "FAIL", "无法重新获取已创建的任务")
            else:
                self.log_test("数据持久化", "FAIL", "无法创建测试任务")
                
        except Exception as e:
            self.log_test("数据持久化", "FAIL", f"数据持久化测试异常: {e}")
        
        return True
    
    def run_integration_tests(self):
        """运行完整的集成测试"""
        print("🚀 开始端到端集成测试")
        print("=" * 60)
        
        # 系统健康检查
        if not self.test_system_health():
            print("❌ 系统健康检查失败，停止测试")
            return
        
        # 认证流程测试
        if not self.test_authentication_flow():
            print("❌ 认证流程测试失败，停止测试")
            return
        
        # 用户管理流程测试
        self.test_user_management_flow()
        
        # 任务管理流程测试
        self.test_task_management_flow()
        
        # 数据分析流程测试
        self.test_analytics_flow()
        
        # 前端集成测试
        self.test_frontend_integration()
        
        # 数据持久化测试
        self.test_data_persistence()
    
    def generate_comprehensive_report(self):
        """生成综合测试报告"""
        print("\n" + "=" * 60)
        print("📊 端到端集成测试综合报告")
        print("=" * 60)
        
        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        partial_tests = len([r for r in self.test_results if r["status"] == "PARTIAL"])
        
        # 按类别分组显示结果
        categories = {}
        for result in self.test_results:
            test_name = result["test"]
            if "健康" in test_name:
                category = "系统健康"
            elif "登录" in test_name or "认证" in test_name or "用户信息" in test_name:
                category = "认证系统"
            elif "用户" in test_name:
                category = "用户管理"
            elif "任务" in test_name:
                category = "任务管理"
            elif "分析" in test_name or "仪表板" in test_name:
                category = "数据分析"
            elif "前端" in test_name:
                category = "前端集成"
            elif "持久化" in test_name:
                category = "数据持久化"
            else:
                category = "其他"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # 显示分类结果
        for category, results in categories.items():
            print(f"\n📋 {category}:")
            for result in results:
                status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
                print(f"  {status_icon} {result['status']} {result['test']} - {result['message']}")
        
        # 显示总体统计
        print(f"\n📈 总体统计:")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"部分通过: {partial_tests} ⚠️")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"成功率: {success_rate:.1f}%")
            
            # 评估系统状态
            if success_rate >= 90:
                system_status = "🟢 优秀 - 系统运行状态良好"
            elif success_rate >= 75:
                system_status = "🟡 良好 - 系统基本正常，有少量问题"
            elif success_rate >= 50:
                system_status = "🟠 一般 - 系统存在一些问题需要修复"
            else:
                system_status = "🔴 较差 - 系统存在严重问题"
            
            print(f"\n🎯 系统状态评估: {system_status}")
        
        # 保存详细报告
        report_data = {
            "test_type": "端到端集成测试",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "partial": partial_tests,
                "success_rate": f"{success_rate:.1f}%" if total_tests > 0 else "0%"
            },
            "categories": categories,
            "detailed_results": self.test_results
        }
        
        with open("e2e_integration_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: e2e_integration_test_report.json")

def main():
    """主函数"""
    tester = E2EIntegrationTester()
    
    # 运行集成测试
    tester.run_integration_tests()
    
    # 生成综合报告
    tester.generate_comprehensive_report()

if __name__ == "__main__":
    main()
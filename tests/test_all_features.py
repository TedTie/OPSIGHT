#!/usr/bin/env python3
"""
OPSIGHT 系统功能综合测试脚本
测试所有核心功能的完整性
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"

class OPSIGHTTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
    
    def log_test(self, test_name, success, message=""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_health_check(self):
        """测试健康检查"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            success = response.status_code == 200
            self.log_test("健康检查", success, f"状态码: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("健康检查", False, str(e))
            return False
    
    def test_login(self):
        """测试登录功能"""
        try:
            login_data = {
                "username": "admin"
            }
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data
            )
            success = response.status_code == 200
            if success:
                # 保存cookie用于后续请求
                pass
            self.log_test("用户登录", success, f"状态码: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("用户登录", False, str(e))
            return False
    
    def test_user_management(self):
        """测试用户管理功能"""
        try:
            # 获取用户列表
            response = self.session.get(f"{BASE_URL}/api/v1/users")
            success = response.status_code == 200
            self.log_test("获取用户列表", success, f"状态码: {response.status_code}")
            
            if success:
                users = response.json()
                self.log_test("用户数据解析", True, f"用户数量: {len(users)}")
            
            return success
        except Exception as e:
            self.log_test("用户管理", False, str(e))
            return False
    
    def test_task_management(self):
        """测试任务管理功能"""
        try:
            # 获取任务列表
            response = self.session.get(f"{BASE_URL}/api/v1/tasks")
            success = response.status_code == 200
            self.log_test("获取任务列表", success, f"状态码: {response.status_code}")
            
            if success:
                tasks = response.json()
                self.log_test("任务数据解析", True, f"任务数量: {len(tasks)}")
            
            return success
        except Exception as e:
            self.log_test("任务管理", False, str(e))
            return False
    
    def test_report_management(self):
        """测试日报管理功能"""
        try:
            # 获取日报列表
            response = self.session.get(f"{BASE_URL}/api/v1/reports")
            success = response.status_code == 200
            self.log_test("获取日报列表", success, f"状态码: {response.status_code}")
            
            if success:
                reports = response.json()
                self.log_test("日报数据解析", True, f"日报数量: {len(reports)}")
            
            return success
        except Exception as e:
            self.log_test("日报管理", False, str(e))
            return False
    
    def test_analytics_apis(self):
        """测试数据分析API"""
        try:
            # 测试分析仪表板
            response = self.session.get(f"{BASE_URL}/api/v1/analytics/dashboard")
            success1 = response.status_code == 200
            self.log_test("分析仪表板API", success1, f"状态码: {response.status_code}")
            
            # 测试任务类型分析
            response = self.session.get(f"{BASE_URL}/api/v1/analytics/task-types")
            success2 = response.status_code == 200
            self.log_test("任务类型分析API", success2, f"状态码: {response.status_code}")
            
            return success1 and success2
        except Exception as e:
            self.log_test("数据分析API", False, str(e))
            return False
    
    def test_frontend_accessibility(self):
        """测试前端可访问性"""
        try:
            response = requests.get("http://localhost:3001")
            success = response.status_code == 200
            self.log_test("前端页面访问", success, f"状态码: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("前端页面访问", False, str(e))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 OPSIGHT 系统功能测试")
        print("=" * 50)
        
        # 基础功能测试
        print("\n📋 基础功能测试:")
        self.test_health_check()
        self.test_frontend_accessibility()
        
        # 认证功能测试
        print("\n🔐 认证功能测试:")
        login_success = self.test_login()
        
        # 核心功能测试（需要登录）
        if login_success:
            print("\n👥 用户管理测试:")
            self.test_user_management()
            
            print("\n📝 任务管理测试:")
            self.test_task_management()
            
            print("\n📊 日报管理测试:")
            self.test_report_management()
            
            print("\n📈 数据分析测试:")
            self.test_analytics_apis()
        else:
            print("\n⚠️  登录失败，跳过需要认证的测试")
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📊 测试报告")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # 保存详细报告
        with open("test_report.json", "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "details": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: test_report.json")

if __name__ == "__main__":
    tester = OPSIGHTTester()
    tester.run_all_tests()
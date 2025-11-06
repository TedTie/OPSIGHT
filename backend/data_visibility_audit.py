#!/usr/bin/env python3
"""
OPSIGHT系统数据可见性端到端审计脚本
测试不同用户角色的API访问权限和数据可见性
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any

BASE_URL = "http://localhost:8000"

class DataVisibilityAuditor:
    def __init__(self):
        self.audit_results = {}
        self.session = requests.Session()
        
    def login_user(self, username: str) -> Dict[str, Any]:
        """登录指定用户"""
        print(f"\n🔐 正在登录用户: {username}")
        
        try:
            response = self.session.post(
                f'{BASE_URL}/api/v1/auth/login',
                json={'username': username}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✅ 登录成功: {user_data['user']['role']}")
                return {
                    'success': True,
                    'user_data': user_data['user'],
                    'error': None
                }
            else:
                print(f"   ❌ 登录失败: {response.status_code}")
                return {
                    'success': False,
                    'user_data': None,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            print(f"   ❌ 登录异常: {e}")
            return {
                'success': False,
                'user_data': None,
                'error': str(e)
            }
    
    def test_user_me_endpoint(self, username: str) -> Dict[str, Any]:
        """测试获取当前用户信息接口"""
        print(f"\n🔍 测试用户 {username} 的 /auth/me 接口")
        
        try:
            response = self.session.get(f'{BASE_URL}/api/v1/auth/me')
            
            result = {
                'endpoint': '/api/v1/auth/me',
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'data': None,
                'error': None,
                'record_count': 0
            }
            
            if response.status_code == 200:
                data = response.json()
                result['data'] = data
                result['record_count'] = 1
                print(f"   ✅ 成功获取用户信息")
                print(f"   用户角色: {data.get('role', 'N/A')}")
                print(f"   身份类型: {data.get('identity_type', 'N/A')}")
                print(f"   用户组: {data.get('group_name', 'N/A')}")
            else:
                result['error'] = response.text
                print(f"   ❌ 失败: {response.status_code} - {response.text}")
                
            return result
            
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return {
                'endpoint': '/api/v1/auth/me',
                'status_code': 0,
                'success': False,
                'data': None,
                'error': str(e),
                'record_count': 0
            }
    
    def test_tasks_endpoint(self, username: str) -> Dict[str, Any]:
        """测试获取任务列表接口"""
        print(f"\n📋 测试用户 {username} 的 /tasks 接口")
        
        try:
            response = self.session.get(f'{BASE_URL}/api/v1/tasks')
            
            result = {
                'endpoint': '/api/v1/tasks',
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'data': None,
                'error': None,
                'record_count': 0
            }
            
            if response.status_code == 200:
                data = response.json()
                result['data'] = data
                result['record_count'] = len(data) if isinstance(data, list) else 0
                print(f"   ✅ 成功获取任务列表: {result['record_count']} 条记录")
                
                # 分析任务分配类型
                if isinstance(data, list) and data:
                    assignment_types = {}
                    for task in data:
                        assignment_type = task.get('assignment_type', 'unknown')
                        assignment_types[assignment_type] = assignment_types.get(assignment_type, 0) + 1
                    print(f"   任务分配类型分布: {assignment_types}")
                    
            else:
                result['error'] = response.text
                print(f"   ❌ 失败: {response.status_code} - {response.text}")
                
            return result
            
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return {
                'endpoint': '/api/v1/tasks',
                'status_code': 0,
                'success': False,
                'data': None,
                'error': str(e),
                'record_count': 0
            }
    
    def test_users_endpoint(self, username: str) -> Dict[str, Any]:
        """测试获取用户列表接口"""
        print(f"\n👥 测试用户 {username} 的 /users 接口")
        
        try:
            response = self.session.get(f'{BASE_URL}/api/v1/users')
            
            result = {
                'endpoint': '/api/v1/users',
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'data': None,
                'error': None,
                'record_count': 0
            }
            
            if response.status_code == 200:
                data = response.json()
                result['data'] = data
                result['record_count'] = len(data) if isinstance(data, list) else 0
                print(f"   ✅ 成功获取用户列表: {result['record_count']} 条记录")
            elif response.status_code == 403:
                result['error'] = "权限不足 (预期行为)"
                print(f"   ⚠️  权限不足: {response.status_code} (这可能是预期行为)")
            else:
                result['error'] = response.text
                print(f"   ❌ 失败: {response.status_code} - {response.text}")
                
            return result
            
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return {
                'endpoint': '/api/v1/users',
                'status_code': 0,
                'success': False,
                'data': None,
                'error': str(e),
                'record_count': 0
            }
    
    def test_reports_endpoint(self, username: str) -> Dict[str, Any]:
        """测试获取日报列表接口"""
        print(f"\n📊 测试用户 {username} 的 /reports 接口")
        
        try:
            response = self.session.get(f'{BASE_URL}/api/v1/reports')
            
            result = {
                'endpoint': '/api/v1/reports',
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'data': None,
                'error': None,
                'record_count': 0
            }
            
            if response.status_code == 200:
                data = response.json()
                result['data'] = data
                result['record_count'] = len(data) if isinstance(data, list) else 0
                print(f"   ✅ 成功获取日报列表: {result['record_count']} 条记录")
            else:
                result['error'] = response.text
                print(f"   ❌ 失败: {response.status_code} - {response.text}")
                
            return result
            
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return {
                'endpoint': '/api/v1/reports',
                'status_code': 0,
                'success': False,
                'data': None,
                'error': str(e),
                'record_count': 0
            }
    
    def audit_user(self, username: str, expected_role: str) -> Dict[str, Any]:
        """审计单个用户的API访问权限"""
        print(f"\n{'='*60}")
        print(f"🔍 开始审计用户: {username} (预期角色: {expected_role})")
        print(f"{'='*60}")
        
        # 登录用户
        login_result = self.login_user(username)
        if not login_result['success']:
            return {
                'username': username,
                'expected_role': expected_role,
                'login_success': False,
                'login_error': login_result['error'],
                'api_tests': {}
            }
        
        # 测试各个API端点
        api_tests = {
            'user_me': self.test_user_me_endpoint(username),
            'tasks': self.test_tasks_endpoint(username),
            'users': self.test_users_endpoint(username),
            'reports': self.test_reports_endpoint(username)
        }
        
        return {
            'username': username,
            'expected_role': expected_role,
            'actual_user_data': login_result['user_data'],
            'login_success': True,
            'login_error': None,
            'api_tests': api_tests
        }
    
    def run_full_audit(self) -> Dict[str, Any]:
        """运行完整的数据可见性审计"""
        print("🚀 开始OPSIGHT系统数据可见性端到端审计")
        print(f"审计时间: {datetime.now().isoformat()}")
        
        # 定义测试用户
        test_users = [
            ('admin', 'super_admin'),
            ('jlpss-chenjianxiong', 'admin'),
            ('test_user', 'user')
        ]
        
        audit_results = {
            'audit_timestamp': datetime.now().isoformat(),
            'base_url': BASE_URL,
            'users_tested': [],
            'summary': {}
        }
        
        # 审计每个用户
        for username, expected_role in test_users:
            user_result = self.audit_user(username, expected_role)
            audit_results['users_tested'].append(user_result)
        
        # 生成摘要
        audit_results['summary'] = self.generate_summary(audit_results['users_tested'])
        
        return audit_results
    
    def generate_summary(self, user_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成审计摘要"""
        summary = {
            'total_users_tested': len(user_results),
            'successful_logins': 0,
            'failed_logins': 0,
            'api_success_rates': {},
            'critical_issues': []
        }
        
        for user_result in user_results:
            if user_result['login_success']:
                summary['successful_logins'] += 1
                
                # 统计API成功率
                for api_name, api_result in user_result['api_tests'].items():
                    if api_name not in summary['api_success_rates']:
                        summary['api_success_rates'][api_name] = {'success': 0, 'total': 0}
                    
                    summary['api_success_rates'][api_name]['total'] += 1
                    if api_result['success']:
                        summary['api_success_rates'][api_name]['success'] += 1
                
                # 检查关键问题
                username = user_result['username']
                if username == 'admin':
                    # 超级管理员应该能看到所有数据
                    tasks_count = user_result['api_tests']['tasks']['record_count']
                    if tasks_count == 0:
                        summary['critical_issues'].append(f"超级管理员 {username} 无法看到任何任务")
                
                elif username == 'test_user':
                    # 普通用户应该能看到分配给他的任务
                    tasks_count = user_result['api_tests']['tasks']['record_count']
                    if tasks_count == 0:
                        summary['critical_issues'].append(f"普通用户 {username} 无法看到任何任务")
            else:
                summary['failed_logins'] += 1
        
        return summary

def main():
    """主函数"""
    auditor = DataVisibilityAuditor()
    
    try:
        # 运行完整审计
        results = auditor.run_full_audit()
        
        # 保存结果到JSON文件
        with open('data_visibility_audit_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print("📊 审计完成摘要")
        print(f"{'='*60}")
        print(f"测试用户数: {results['summary']['total_users_tested']}")
        print(f"成功登录: {results['summary']['successful_logins']}")
        print(f"登录失败: {results['summary']['failed_logins']}")
        
        if results['summary']['critical_issues']:
            print(f"\n⚠️  发现 {len(results['summary']['critical_issues'])} 个关键问题:")
            for issue in results['summary']['critical_issues']:
                print(f"   - {issue}")
        else:
            print("\n✅ 未发现关键问题")
        
        print(f"\n📄 详细结果已保存到: data_visibility_audit_results.json")
        
        return results
        
    except Exception as e:
        print(f"\n❌ 审计过程中发生异常: {e}")
        return None

if __name__ == "__main__":
    main()
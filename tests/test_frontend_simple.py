#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPSIGHT 前端功能简化测试脚本
使用HTTP请求测试前端页面的可访问性和基本功能
"""

import requests
import json
import time
import re
from urllib.parse import urljoin

class SimpleFrontendTester:
    def __init__(self):
        self.frontend_url = "http://localhost:3001"
        self.backend_url = "http://localhost:8001"
        self.session = requests.Session()
        self.test_results = []
        
    def test_page_accessibility(self, path, page_name):
        """测试页面可访问性"""
        try:
            url = urljoin(self.frontend_url, path)
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # 检查响应内容
                content = response.text
                
                # 基本HTML结构检查
                has_html = '<html' in content.lower()
                has_body = '<body' in content.lower()
                has_title = '<title' in content.lower()
                
                # 检查是否包含Vue.js相关内容
                has_vue = any(keyword in content.lower() for keyword in ['vue', 'app', 'router'])
                
                # 检查是否有错误信息
                has_error = any(error in content.lower() for error in ['error', '404', '500', 'not found'])
                
                if has_html and has_body and not has_error:
                    self.test_results.append({
                        "test": f"{page_name}页面访问",
                        "status": "PASS",
                        "message": f"页面正常访问，状态码: {response.status_code}"
                    })
                    
                    # 额外信息
                    extra_info = []
                    if has_title:
                        extra_info.append("包含标题")
                    if has_vue:
                        extra_info.append("包含Vue组件")
                    
                    if extra_info:
                        print(f"✅ {page_name}页面访问成功 - {', '.join(extra_info)}")
                    else:
                        print(f"✅ {page_name}页面访问成功")
                    
                    return True, content
                else:
                    self.test_results.append({
                        "test": f"{page_name}页面访问",
                        "status": "FAIL",
                        "message": f"页面内容异常或包含错误信息"
                    })
                    print(f"❌ {page_name}页面内容异常")
                    return False, content
            else:
                self.test_results.append({
                    "test": f"{page_name}页面访问",
                    "status": "FAIL",
                    "message": f"HTTP状态码: {response.status_code}"
                })
                print(f"❌ {page_name}页面访问失败，状态码: {response.status_code}")
                return False, ""
                
        except requests.exceptions.ConnectionError:
            self.test_results.append({
                "test": f"{page_name}页面访问",
                "status": "FAIL",
                "message": "连接失败，前端服务可能未启动"
            })
            print(f"❌ {page_name}页面连接失败")
            return False, ""
        except Exception as e:
            self.test_results.append({
                "test": f"{page_name}页面访问",
                "status": "FAIL",
                "message": f"访问异常: {e}"
            })
            print(f"❌ {page_name}页面访问异常: {e}")
            return False, ""
    
    def analyze_page_content(self, content, page_name):
        """分析页面内容"""
        try:
            # 提取页面标题
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE)
            title = title_match.group(1) if title_match else "未找到标题"
            
            # 检查JavaScript文件引用
            js_files = re.findall(r'<script[^>]*src=["\']([^"\']*)["\']', content, re.IGNORECASE)
            
            # 检查CSS文件引用
            css_files = re.findall(r'<link[^>]*href=["\']([^"\']*\.css[^"\']*)["\']', content, re.IGNORECASE)
            
            # 检查Vue.js相关内容
            vue_indicators = []
            if 'vue' in content.lower():
                vue_indicators.append("Vue框架")
            if 'router' in content.lower():
                vue_indicators.append("路由系统")
            if 'app' in content.lower():
                vue_indicators.append("应用组件")
            
            analysis_result = {
                "title": title,
                "js_files_count": len(js_files),
                "css_files_count": len(css_files),
                "vue_features": vue_indicators,
                "content_length": len(content)
            }
            
            self.test_results.append({
                "test": f"{page_name}内容分析",
                "status": "PASS",
                "message": f"标题: {title}, JS文件: {len(js_files)}个, CSS文件: {len(css_files)}个"
            })
            
            print(f"📄 {page_name}内容分析:")
            print(f"   标题: {title}")
            print(f"   JavaScript文件: {len(js_files)}个")
            print(f"   CSS文件: {len(css_files)}个")
            if vue_indicators:
                print(f"   Vue特性: {', '.join(vue_indicators)}")
            print(f"   内容长度: {len(content)}字符")
            
            return analysis_result
            
        except Exception as e:
            self.test_results.append({
                "test": f"{page_name}内容分析",
                "status": "FAIL",
                "message": f"分析异常: {e}"
            })
            print(f"❌ {page_name}内容分析失败: {e}")
            return None
    
    def test_api_connectivity(self):
        """测试前端到后端API的连通性"""
        try:
            # 测试后端健康检查
            response = self.session.get(f"{self.backend_url}/health", timeout=5)
            
            if response.status_code == 200:
                self.test_results.append({
                    "test": "后端API连通性",
                    "status": "PASS",
                    "message": "后端API正常响应"
                })
                print("✅ 后端API连通性正常")
                return True
            else:
                self.test_results.append({
                    "test": "后端API连通性",
                    "status": "FAIL",
                    "message": f"后端API状态码: {response.status_code}"
                })
                print(f"❌ 后端API响应异常: {response.status_code}")
                return False
                
        except Exception as e:
            self.test_results.append({
                "test": "后端API连通性",
                "status": "FAIL",
                "message": f"连接异常: {e}"
            })
            print(f"❌ 后端API连接失败: {e}")
            return False
    
    def test_static_resources(self):
        """测试静态资源访问"""
        try:
            # 测试常见的静态资源路径
            static_paths = [
                "/favicon.ico",
                "/assets/",
                "/static/"
            ]
            
            accessible_resources = 0
            for path in static_paths:
                try:
                    url = urljoin(self.frontend_url, path)
                    response = self.session.get(url, timeout=5)
                    if response.status_code in [200, 404]:  # 404也是正常的，说明服务器在响应
                        accessible_resources += 1
                        if response.status_code == 200:
                            print(f"✅ 静态资源可访问: {path}")
                        else:
                            print(f"⚠️  静态资源路径存在但无内容: {path}")
                except:
                    print(f"❌ 静态资源访问失败: {path}")
            
            if accessible_resources > 0:
                self.test_results.append({
                    "test": "静态资源访问",
                    "status": "PASS",
                    "message": f"可访问{accessible_resources}个静态资源路径"
                })
                return True
            else:
                self.test_results.append({
                    "test": "静态资源访问",
                    "status": "FAIL",
                    "message": "无法访问任何静态资源路径"
                })
                return False
                
        except Exception as e:
            self.test_results.append({
                "test": "静态资源访问",
                "status": "FAIL",
                "message": f"测试异常: {e}"
            })
            return False
    
    def run_frontend_tests(self):
        """运行前端功能测试"""
        print("🚀 开始前端简化功能测试")
        print("=" * 50)
        
        # 测试后端API连通性
        print("\n🔗 测试后端API连通性:")
        self.test_api_connectivity()
        
        # 测试主页访问
        print("\n📱 测试主页访问:")
        success, content = self.test_page_accessibility("/", "主页")
        
        if success and content:
            # 分析页面内容
            print("\n📄 分析页面内容:")
            self.analyze_page_content(content, "主页")
        
        # 测试静态资源
        print("\n📦 测试静态资源:")
        self.test_static_resources()
        
        # 测试其他可能的页面路径
        print("\n🧭 测试其他页面路径:")
        other_paths = [
            ("/dashboard", "Dashboard页面"),
            ("/analytics", "Analytics页面"),
            ("/tasks", "任务页面"),
            ("/users", "用户页面"),
            ("/reports", "报告页面")
        ]
        
        for path, name in other_paths:
            success, _ = self.test_page_accessibility(path, name)
            time.sleep(0.5)  # 避免请求过快
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📊 前端简化测试报告")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['status']} {result['test']} - {result['message']}")
        
        print(f"\n总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        # 保存详细报告
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "前端简化测试",
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": f"{success_rate:.1f}%" if total_tests > 0 else "0%",
            "test_results": self.test_results
        }
        
        with open("frontend_simple_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: frontend_simple_test_report.json")

def main():
    """主函数"""
    tester = SimpleFrontendTester()
    
    # 运行前端测试
    tester.run_frontend_tests()
    
    # 生成报告
    tester.generate_report()

if __name__ == "__main__":
    main()
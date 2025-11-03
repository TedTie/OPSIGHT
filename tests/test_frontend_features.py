#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPSIGHT 前端功能测试脚本
测试前端页面的数据展示和交互功能
"""

import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FrontendTester:
    def __init__(self):
        self.frontend_url = "http://localhost:3001"
        self.backend_url = "http://localhost:8001"
        self.driver = None
        self.session = requests.Session()
        self.test_results = []
        
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # 无头模式
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            print(f"❌ 浏览器驱动设置失败: {e}")
            return False
    
    def login_via_api(self):
        """通过API登录获取认证信息"""
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                print("✅ API登录成功")
                return True
            else:
                print(f"❌ API登录失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API登录异常: {e}")
            return False
    
    def test_page_load(self, page_path, page_name):
        """测试页面加载"""
        try:
            url = f"{self.frontend_url}{page_path}"
            self.driver.get(url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 检查是否有错误信息
            page_source = self.driver.page_source
            if "error" in page_source.lower() or "404" in page_source:
                self.test_results.append({
                    "test": f"{page_name}页面加载",
                    "status": "FAIL",
                    "message": "页面包含错误信息"
                })
                return False
            
            self.test_results.append({
                "test": f"{page_name}页面加载",
                "status": "PASS",
                "message": f"页面成功加载: {url}"
            })
            return True
            
        except TimeoutException:
            self.test_results.append({
                "test": f"{page_name}页面加载",
                "status": "FAIL", 
                "message": "页面加载超时"
            })
            return False
        except Exception as e:
            self.test_results.append({
                "test": f"{page_name}页面加载",
                "status": "FAIL",
                "message": f"页面加载异常: {e}"
            })
            return False
    
    def test_dashboard_elements(self):
        """测试Dashboard页面元素"""
        try:
            # 查找常见的Dashboard元素
            dashboard_elements = [
                ("nav", "导航栏"),
                (".card", "卡片组件"),
                (".dashboard", "仪表板容器"),
                ("h1, h2, h3", "标题元素")
            ]
            
            found_elements = 0
            for selector, name in dashboard_elements:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        found_elements += 1
                        print(f"✅ 找到{name}: {len(elements)}个")
                    else:
                        print(f"⚠️  未找到{name}")
                except:
                    print(f"⚠️  查找{name}时出错")
            
            if found_elements > 0:
                self.test_results.append({
                    "test": "Dashboard页面元素",
                    "status": "PASS",
                    "message": f"找到{found_elements}种页面元素"
                })
                return True
            else:
                self.test_results.append({
                    "test": "Dashboard页面元素",
                    "status": "FAIL",
                    "message": "未找到任何Dashboard元素"
                })
                return False
                
        except Exception as e:
            self.test_results.append({
                "test": "Dashboard页面元素",
                "status": "FAIL",
                "message": f"元素检测异常: {e}"
            })
            return False
    
    def test_navigation(self):
        """测试页面导航功能"""
        try:
            # 查找导航链接
            nav_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/'], router-link, .nav-link")
            
            if nav_links:
                print(f"✅ 找到{len(nav_links)}个导航链接")
                
                # 测试点击第一个导航链接
                if len(nav_links) > 0:
                    try:
                        nav_links[0].click()
                        time.sleep(2)  # 等待页面跳转
                        
                        self.test_results.append({
                            "test": "页面导航功能",
                            "status": "PASS",
                            "message": "导航链接可以正常点击"
                        })
                        return True
                    except:
                        self.test_results.append({
                            "test": "页面导航功能",
                            "status": "PARTIAL",
                            "message": "找到导航链接但点击失败"
                        })
                        return False
            else:
                self.test_results.append({
                    "test": "页面导航功能",
                    "status": "FAIL",
                    "message": "未找到导航链接"
                })
                return False
                
        except Exception as e:
            self.test_results.append({
                "test": "页面导航功能",
                "status": "FAIL",
                "message": f"导航测试异常: {e}"
            })
            return False
    
    def test_data_display(self):
        """测试数据展示功能"""
        try:
            # 查找数据展示元素
            data_elements = [
                ("table", "数据表格"),
                (".chart", "图表组件"),
                (".stats", "统计数据"),
                (".list", "列表组件"),
                ("[data-testid]", "测试标识元素")
            ]
            
            found_data = 0
            for selector, name in data_elements:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        found_data += 1
                        print(f"✅ 找到{name}: {len(elements)}个")
                except:
                    pass
            
            # 检查页面文本内容是否包含数据
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            has_meaningful_content = any(keyword in page_text.lower() for keyword in 
                                       ['task', 'user', 'report', '任务', '用户', '报告', '数据'])
            
            if found_data > 0 or has_meaningful_content:
                self.test_results.append({
                    "test": "数据展示功能",
                    "status": "PASS",
                    "message": f"找到{found_data}种数据展示元素，页面包含有意义的内容"
                })
                return True
            else:
                self.test_results.append({
                    "test": "数据展示功能",
                    "status": "FAIL",
                    "message": "未找到数据展示元素或有意义的内容"
                })
                return False
                
        except Exception as e:
            self.test_results.append({
                "test": "数据展示功能",
                "status": "FAIL",
                "message": f"数据展示测试异常: {e}"
            })
            return False
    
    def run_frontend_tests(self):
        """运行前端功能测试"""
        print("🚀 开始前端功能测试")
        print("=" * 50)
        
        # 设置浏览器驱动
        if not self.setup_driver():
            print("❌ 无法设置浏览器驱动，跳过前端测试")
            return
        
        try:
            # 测试主页加载
            print("\n📱 测试页面加载:")
            self.test_page_load("/", "主页")
            
            # 测试Dashboard元素
            print("\n📊 测试Dashboard元素:")
            self.test_dashboard_elements()
            
            # 测试导航功能
            print("\n🧭 测试页面导航:")
            self.test_navigation()
            
            # 测试数据展示
            print("\n📈 测试数据展示:")
            self.test_data_display()
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📊 前端测试报告")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        partial_tests = len([r for r in self.test_results if r["status"] == "PARTIAL"])
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['status']} {result['test']} - {result['message']}")
        
        print(f"\n总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"部分通过: {partial_tests} ⚠️")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        # 保存详细报告
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "partial": partial_tests,
            "success_rate": f"{success_rate:.1f}%" if total_tests > 0 else "0%",
            "test_results": self.test_results
        }
        
        with open("frontend_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: frontend_test_report.json")

def main():
    """主函数"""
    tester = FrontendTester()
    
    # 先进行API登录
    print("🔐 进行API认证...")
    if not tester.login_via_api():
        print("⚠️  API认证失败，但继续进行前端测试")
    
    # 运行前端测试
    tester.run_frontend_tests()
    
    # 生成报告
    tester.generate_report()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
测试超级管理员页面访问权限
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def test_admin_pages():
    print("🚀 测试超级管理员页面访问权限")
    print("=" * 50)
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        # 1. 登录
        print("📍 登录系统...")
        driver.get("http://localhost:3001/login")
        
        # 输入用户名
        username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='用户名']")))
        username_input.clear()
        username_input.send_keys("admin")
        
        # 点击登录按钮
        login_button = driver.find_element(By.CSS_SELECTOR, "button.el-button--primary, button[type='submit'], .login-button")
        login_button.click()
        
        # 等待登录完成
        wait.until(EC.url_contains("dashboard"))
        print("✅ 登录成功")
        
        # 2. 测试页面访问
        pages_to_test = [
            ("/settings", "设置页面"),
            ("/admin/users", "用户管理页面"),
            ("/admin/groups", "组别管理页面"),
            ("/admin/ai", "AI配置页面"),
            ("/admin/metrics", "自定义指标页面")
        ]
        
        for url, page_name in pages_to_test:
            print(f"\n📍 测试 {page_name}...")
            try:
                driver.get(f"http://localhost:3001{url}")
                time.sleep(2)
                
                current_url = driver.current_url
                if url in current_url:
                    print(f"   ✅ {page_name} 可访问")
                    
                    # 检查页面是否有错误信息
                    try:
                        error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '403') or contains(text(), '无权限') or contains(text(), '权限不足')]")
                        if error_elements:
                            print(f"   ❌ {page_name} 显示权限错误")
                        else:
                            print(f"   ✅ {page_name} 正常显示")
                    except:
                        print(f"   ✅ {page_name} 正常显示")
                        
                elif "login" in current_url:
                    print(f"   ❌ {page_name} 重定向到登录页面")
                elif "403" in current_url or "unauthorized" in current_url:
                    print(f"   ❌ {page_name} 访问被拒绝")
                else:
                    print(f"   ⚠️ {page_name} 重定向到: {current_url}")
                    
            except Exception as e:
                print(f"   ❌ {page_name} 访问失败: {e}")
        
        # 3. 测试菜单点击
        print(f"\n📍 测试菜单导航...")
        driver.get("http://localhost:3001/dashboard")
        time.sleep(2)
        
        # 尝试点击设置菜单
        try:
            settings_link = driver.find_element(By.XPATH, "//*[contains(text(), '设置')]")
            settings_link.click()
            time.sleep(2)
            if "/settings" in driver.current_url:
                print("   ✅ 设置菜单导航成功")
            else:
                print("   ❌ 设置菜单导航失败")
        except Exception as e:
            print(f"   ❌ 设置菜单点击失败: {e}")
        
        # 尝试点击管理功能菜单
        try:
            driver.get("http://localhost:3001/dashboard")
            time.sleep(2)
            
            management_menu = driver.find_element(By.XPATH, "//*[contains(text(), '管理功能')]")
            management_menu.click()
            time.sleep(1)
            
            # 点击用户管理
            user_mgmt_link = driver.find_element(By.XPATH, "//*[contains(text(), '用户管理')]")
            user_mgmt_link.click()
            time.sleep(2)
            
            if "/admin/users" in driver.current_url:
                print("   ✅ 管理功能菜单导航成功")
            else:
                print("   ❌ 管理功能菜单导航失败")
        except Exception as e:
            print(f"   ❌ 管理功能菜单点击失败: {e}")
        
        print(f"\n📸 截图已保存: admin_pages_test.png")
        driver.save_screenshot("admin_pages_test.png")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        driver.save_screenshot("admin_pages_error.png")
        
    finally:
        driver.quit()
    
    print("\n" + "=" * 50)
    print("📊 超级管理员页面访问测试完成")

if __name__ == "__main__":
    test_admin_pages()
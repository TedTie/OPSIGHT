#!/usr/bin/env python3
"""
测试菜单修复效果
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def setup_driver():
    """设置Chrome驱动"""
    options = Options()
    options.add_argument('--disable-web-security')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

def test_menu_fix():
    """测试菜单修复效果"""
    driver = setup_driver()
    
    try:
        print("=== 测试菜单修复效果 ===")
        
        # 1. 登录
        print("\n1. 登录系统...")
        driver.get("http://localhost:3001/login")
        time.sleep(2)
        
        username_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='用户名']")
        username_input.clear()
        username_input.send_keys("admin")
        
        login_button = driver.find_element(By.CSS_SELECTOR, ".login-button")
        login_button.click()
        
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        print("✓ 登录成功")
        
        # 2. 等待页面完全加载
        print("\n2. 等待页面加载...")
        time.sleep(5)  # 给Vue组件更多时间加载
        
        # 3. 检查控制台错误
        print("\n3. 检查控制台错误...")
        logs = driver.get_log('browser')
        error_logs = [log for log in logs if log['level'] == 'SEVERE']
        
        if error_logs:
            print(f"发现 {len(error_logs)} 个严重错误:")
            for log in error_logs[-3:]:  # 只显示最后3个错误
                print(f"  - {log['message']}")
        else:
            print("✓ 无严重控制台错误")
        
        # 4. 检查管理功能菜单
        print("\n4. 检查管理功能菜单...")
        try:
            # 查找管理功能菜单
            management_menu = driver.find_element(By.XPATH, "//*[contains(text(), '管理功能')]")
            print(f"✓ 找到管理功能菜单: {management_menu.is_displayed()}")
            
            # 点击管理功能菜单展开子菜单
            if management_menu.is_displayed():
                management_menu.click()
                time.sleep(2)
                print("✓ 点击管理功能菜单")
                
                # 检查AI配置菜单
                try:
                    ai_menu = driver.find_element(By.XPATH, "//*[contains(text(), 'AI配置') or contains(text(), 'AI智能体')]")
                    print(f"✓ 找到AI配置菜单: {ai_menu.is_displayed()}")
                except:
                    print("✗ 未找到AI配置菜单")
                
                # 检查自定义指标菜单
                try:
                    metrics_menu = driver.find_element(By.XPATH, "//*[contains(text(), '自定义指标')]")
                    print(f"✓ 找到自定义指标菜单: {metrics_menu.is_displayed()}")
                except:
                    print("✗ 未找到自定义指标菜单")
            
        except Exception as e:
            print(f"✗ 检查管理功能菜单失败: {e}")
        
        # 5. 测试直接访问页面
        print("\n5. 测试直接访问AI配置页面...")
        driver.get("http://localhost:3001/admin/ai")
        time.sleep(3)
        
        # 检查页面是否正常加载
        try:
            page_title = driver.find_element(By.CSS_SELECTOR, "h1, .page-title").text
            print(f"✓ AI配置页面加载成功: {page_title}")
            
            # 检查是否有JavaScript错误
            logs = driver.get_log('browser')
            new_errors = [log for log in logs if log['level'] == 'SEVERE' and 'getCategoryTagType' in log['message']]
            
            if new_errors:
                print("✗ 仍有getCategoryTagType相关错误")
            else:
                print("✓ 无getCategoryTagType相关错误")
                
        except Exception as e:
            print(f"✗ AI配置页面加载失败: {e}")
        
        print("\n6. 测试直接访问自定义指标页面...")
        driver.get("http://localhost:3001/admin/metrics")
        time.sleep(3)
        
        try:
            page_title = driver.find_element(By.CSS_SELECTOR, "h1, .page-title").text
            print(f"✓ 自定义指标页面加载成功: {page_title}")
        except Exception as e:
            print(f"✗ 自定义指标页面加载失败: {e}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_menu_fix()
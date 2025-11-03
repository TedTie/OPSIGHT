#!/usr/bin/env python3
"""
测试localStorage修复方案
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

def test_localstorage_fix():
    """测试localStorage修复方案"""
    driver = setup_driver()
    
    try:
        print("=== localStorage修复方案测试 ===")
        
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
        time.sleep(5)
        
        # 3. 检查控制台日志中的isSuperAdmin计算
        print("\n2. 检查控制台日志...")
        logs = driver.get_log('browser')
        for log in logs:
            if 'isSuperAdmin computed' in log['message'] or 'localStorage isSuperAdmin' in log['message']:
                print(f"  {log['level']}: {log['message']}")
        
        # 4. 检查菜单显示
        print("\n3. 检查菜单显示...")
        
        # 查找管理功能菜单
        try:
            admin_menu = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='管理功能']"))
            )
            print("✓ 找到管理功能菜单")
            
            # 点击展开
            admin_menu.click()
            time.sleep(2)
            
            # 检查AI配置菜单
            ai_menus = driver.find_elements(By.XPATH, "//span[text()='AI配置']")
            if ai_menus:
                print(f"✓ 找到AI配置菜单 (数量: {len(ai_menus)})")
                for i, menu in enumerate(ai_menus):
                    print(f"  AI配置菜单 {i+1}: 可见={menu.is_displayed()}")
                    
                # 尝试点击第一个AI配置菜单
                if ai_menus[0].is_displayed():
                    ai_menus[0].click()
                    time.sleep(2)
                    
                    current_url = driver.current_url
                    if "/admin/ai" in current_url:
                        print("✓ AI配置菜单点击成功，已跳转到AI配置页面")
                        
                        # 检查页面是否正常加载
                        try:
                            page_title = driver.find_element(By.TAG_NAME, "h1")
                            print(f"✓ AI配置页面标题: {page_title.text}")
                        except:
                            print("⚠ AI配置页面可能没有h1标题")
                            
                        # 返回dashboard测试自定义指标菜单
                        driver.get("http://localhost:3001/dashboard")
                        time.sleep(2)
                        
                        # 重新展开管理功能菜单
                        admin_menu = driver.find_element(By.XPATH, "//span[text()='管理功能']")
                        admin_menu.click()
                        time.sleep(1)
                        
                    else:
                        print(f"✗ AI配置菜单点击后未跳转到正确页面，当前URL: {current_url}")
            else:
                print("✗ 未找到AI配置菜单")
            
            # 检查自定义指标菜单
            metrics_menus = driver.find_elements(By.XPATH, "//span[text()='自定义指标']")
            if metrics_menus:
                print(f"✓ 找到自定义指标菜单 (数量: {len(metrics_menus)})")
                for i, menu in enumerate(metrics_menus):
                    print(f"  自定义指标菜单 {i+1}: 可见={menu.is_displayed()}")
                    
                # 尝试点击第一个自定义指标菜单
                if metrics_menus[0].is_displayed():
                    metrics_menus[0].click()
                    time.sleep(2)
                    
                    current_url = driver.current_url
                    if "/admin/metrics" in current_url:
                        print("✓ 自定义指标菜单点击成功，已跳转到自定义指标页面")
                        
                        # 检查页面是否正常加载
                        try:
                            page_title = driver.find_element(By.TAG_NAME, "h1")
                            print(f"✓ 自定义指标页面标题: {page_title.text}")
                        except:
                            print("⚠ 自定义指标页面可能没有h1标题")
                    else:
                        print(f"✗ 自定义指标菜单点击后未跳转到正确页面，当前URL: {current_url}")
            else:
                print("✗ 未找到自定义指标菜单")
                
        except Exception as e:
            print(f"✗ 未找到管理功能菜单: {e}")
        
        # 5. 检查页面是否有错误
        print("\n4. 检查页面错误...")
        final_logs = driver.get_log('browser')
        error_count = 0
        for log in final_logs:
            if log['level'] == 'SEVERE':
                error_count += 1
                print(f"  错误: {log['message']}")
        
        if error_count == 0:
            print("✓ 页面无严重错误")
        else:
            print(f"✗ 页面有 {error_count} 个严重错误")
        
        # 6. 最终验证
        print("\n5. 最终验证...")
        verification = driver.execute_script("""
            try {
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                const aiMenus = document.querySelectorAll('[index="/admin/ai"]');
                const metricsMenus = document.querySelectorAll('[index="/admin/metrics"]');
                
                return {
                    userRole: user ? user.role : null,
                    isSuperAdmin: user ? user.role === 'super_admin' : false,
                    aiMenusCount: aiMenus.length,
                    metricsMenusCount: metricsMenus.length,
                    aiMenuVisible: aiMenus.length > 0 ? aiMenus[0].offsetParent !== null : false,
                    metricsMenuVisible: metricsMenus.length > 0 ? metricsMenus[0].offsetParent !== null : false
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"最终验证结果: {verification}")
        
        if verification.get('isSuperAdmin') and verification.get('aiMenusCount', 0) > 0 and verification.get('metricsMenusCount', 0) > 0:
            print("\n🎉 修复成功！AI配置和自定义指标菜单已正确显示")
        else:
            print("\n❌ 修复未完全成功，需要进一步调试")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_localstorage_fix()
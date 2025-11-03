#!/usr/bin/env python3
"""
测试authStore修复效果
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

def test_authstore_fix():
    """测试authStore修复效果"""
    driver = setup_driver()
    
    try:
        print("=== authStore修复效果测试 ===")
        
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
        
        # 3. 检查控制台日志
        print("\n2. 检查控制台日志...")
        logs = driver.get_log('browser')
        for log in logs[-10:]:  # 只显示最后10条日志
            if 'authStore' in log['message'] or 'initAuth' in log['message']:
                print(f"  {log['level']}: {log['message']}")
        
        # 4. 检查authStore状态
        print("\n3. 检查authStore状态...")
        authstore_status = driver.execute_script("""
            try {
                // 直接从localStorage检查
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                const token = localStorage.getItem('token');
                
                return {
                    localStorage: {
                        hasUser: !!user,
                        userRole: user ? user.role : null,
                        hasToken: !!token
                    },
                    computed: {
                        isAuthenticated: !!user,
                        isAdmin: user ? (user.role === 'admin' || user.role === 'super_admin') : false,
                        isSuperAdmin: user ? user.role === 'super_admin' : false
                    }
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"authStore状态: {authstore_status}")
        
        # 5. 检查菜单显示
        print("\n4. 检查菜单显示...")
        
        # 查找管理功能菜单
        try:
            admin_menu = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='管理功能']"))
            )
            print("✓ 找到管理功能菜单")
            
            # 点击展开
            admin_menu.click()
            time.sleep(1)
            
            # 检查AI配置菜单
            ai_menus = driver.find_elements(By.XPATH, "//span[text()='AI配置']")
            if ai_menus:
                print(f"✓ 找到AI配置菜单 (数量: {len(ai_menus)})")
                for i, menu in enumerate(ai_menus):
                    print(f"  AI配置菜单 {i+1}: 可见={menu.is_displayed()}")
            else:
                print("✗ 未找到AI配置菜单")
            
            # 检查自定义指标菜单
            metrics_menus = driver.find_elements(By.XPATH, "//span[text()='自定义指标']")
            if metrics_menus:
                print(f"✓ 找到自定义指标菜单 (数量: {len(metrics_menus)})")
                for i, menu in enumerate(metrics_menus):
                    print(f"  自定义指标菜单 {i+1}: 可见={menu.is_displayed()}")
            else:
                print("✗ 未找到自定义指标菜单")
                
        except Exception as e:
            print(f"✗ 未找到管理功能菜单: {e}")
        
        # 6. 测试菜单点击
        print("\n5. 测试菜单点击...")
        
        # 尝试点击AI配置菜单
        try:
            ai_menu = driver.find_element(By.XPATH, "//span[text()='AI配置']")
            ai_menu.click()
            time.sleep(2)
            
            current_url = driver.current_url
            if "/admin/ai" in current_url:
                print("✓ AI配置菜单点击成功，已跳转到AI配置页面")
            else:
                print(f"✗ AI配置菜单点击后未跳转到正确页面，当前URL: {current_url}")
                
        except Exception as e:
            print(f"✗ AI配置菜单点击失败: {e}")
        
        # 7. 检查页面是否有错误
        print("\n6. 检查页面错误...")
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
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_authstore_fix()
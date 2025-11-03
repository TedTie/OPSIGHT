#!/usr/bin/env python3
"""
测试前端权限状态
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_frontend_permissions():
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("🔍 测试前端权限状态...")
        
        # 1. 访问登录页面
        print("\n1. 访问登录页面...")
        driver.get("http://localhost:3001/login")
        time.sleep(2)
        
        # 2. 登录
        print("2. 使用admin账户登录...")
        username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='用户名']")))
        password_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='密码']")
        
        username_input.clear()
        username_input.send_keys("admin")
        password_input.clear()
        password_input.send_keys("admin123")
        
        # 点击登录按钮
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # 等待登录成功
        time.sleep(3)
        
        # 3. 检查当前URL
        current_url = driver.current_url
        print(f"登录后URL: {current_url}")
        
        # 4. 检查用户信息
        print("\n3. 检查用户信息...")
        
        # 执行JavaScript获取用户状态
        user_info = driver.execute_script("""
            const authStore = window.authStore || {};
            const user = JSON.parse(localStorage.getItem('user') || 'null');
            return {
                user: user,
                isAuthenticated: !!user,
                isAdmin: user && (user.role === 'admin' || user.role === 'super_admin'),
                isSuperAdmin: user && user.role === 'super_admin'
            };
        """)
        
        print(f"用户信息: {user_info}")
        
        # 5. 检查侧边栏菜单
        print("\n4. 检查侧边栏菜单...")
        
        # 查找管理功能菜单
        try:
            admin_menu = wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='管理功能']")))
            print("✅ 找到管理功能菜单")
            
            # 点击展开管理功能菜单
            admin_menu.click()
            time.sleep(1)
            
            # 检查子菜单项
            menu_items = []
            
            # 检查用户管理
            try:
                user_mgmt = driver.find_element(By.XPATH, "//span[text()='用户管理']")
                menu_items.append("用户管理")
                print("✅ 找到用户管理菜单")
            except:
                print("❌ 未找到用户管理菜单")
            
            # 检查组别管理
            try:
                group_mgmt = driver.find_element(By.XPATH, "//span[text()='组别管理']")
                menu_items.append("组别管理")
                print("✅ 找到组别管理菜单")
            except:
                print("❌ 未找到组别管理菜单")
            
            # 检查AI配置
            try:
                ai_config = driver.find_element(By.XPATH, "//span[text()='AI配置']")
                menu_items.append("AI配置")
                print("✅ 找到AI配置菜单")
            except:
                print("❌ 未找到AI配置菜单")
            
            # 检查自定义指标
            try:
                metrics = driver.find_element(By.XPATH, "//span[text()='自定义指标']")
                menu_items.append("自定义指标")
                print("✅ 找到自定义指标菜单")
            except:
                print("❌ 未找到自定义指标菜单")
            
            print(f"\n可见的管理菜单项: {menu_items}")
            
        except Exception as e:
            print(f"❌ 未找到管理功能菜单: {e}")
        
        # 6. 检查页面源码中的权限相关信息
        print("\n5. 检查页面源码...")
        page_source = driver.page_source
        
        if 'v-if="authStore.isSuperAdmin"' in page_source:
            print("✅ 页面源码包含超级管理员权限检查")
        else:
            print("❌ 页面源码不包含超级管理员权限检查")
        
        # 7. 检查控制台错误
        print("\n6. 检查控制台日志...")
        logs = driver.get_log('browser')
        for log in logs:
            if log['level'] == 'SEVERE':
                print(f"❌ 控制台错误: {log['message']}")
        
        print("\n✅ 权限测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_frontend_permissions()
#!/usr/bin/env python3
"""
测试计算属性是否正常工作
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

def test_computed_properties():
    """测试计算属性"""
    driver = setup_driver()
    
    try:
        print("=== 测试计算属性 ===")
        
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
        
        # 3. 直接在页面上测试计算属性
        print("\n2. 测试计算属性...")
        test_result = driver.execute_script("""
            try {
                // 手动创建计算属性逻辑
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                const isSuperAdmin = user && user.role === 'super_admin';
                const isAdmin = user && (user.role === 'admin' || user.role === 'super_admin');
                
                console.log('Manual computed test:', { user: user?.username, role: user?.role, isSuperAdmin, isAdmin });
                
                return {
                    user: user,
                    isSuperAdmin: isSuperAdmin,
                    isAdmin: isAdmin,
                    localStorage: {
                        user: localStorage.getItem('user'),
                        token: localStorage.getItem('token')
                    }
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"计算属性测试结果: {test_result}")
        
        # 4. 检查控制台日志
        print("\n3. 检查控制台日志...")
        logs = driver.get_log('browser')
        for log in logs:
            if 'computed' in log['message'].lower() or 'isadmin' in log['message'].lower() or 'issuperadmin' in log['message'].lower():
                print(f"  {log['level']}: {log['message']}")
        
        # 5. 手动触发Vue组件更新
        print("\n4. 手动触发Vue组件更新...")
        manual_update = driver.execute_script("""
            try {
                // 查找Vue组件实例
                const sidebarElement = document.querySelector('.el-aside');
                if (!sidebarElement) return { error: 'Sidebar not found' };
                
                const vueInstance = sidebarElement.__vueParentComponent || sidebarElement.__vue__;
                if (!vueInstance) return { error: 'Vue instance not found' };
                
                // 尝试强制更新
                if (vueInstance.proxy && vueInstance.proxy.$forceUpdate) {
                    vueInstance.proxy.$forceUpdate();
                }
                
                // 检查setupState
                const setupState = vueInstance.setupState || {};
                
                return {
                    hasVueInstance: true,
                    setupStateKeys: Object.keys(setupState),
                    setupState: setupState
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"手动更新结果: {manual_update}")
        
        # 6. 等待一下再检查DOM
        time.sleep(2)
        
        print("\n5. 检查DOM状态...")
        dom_state = driver.execute_script("""
            try {
                const adminSubMenu = document.querySelector('[index="admin-menu"]');
                const allSubMenus = document.querySelectorAll('.el-sub-menu');
                const allMenuItems = document.querySelectorAll('.el-menu-item');
                
                return {
                    adminSubMenuExists: !!adminSubMenu,
                    totalSubMenus: allSubMenus.length,
                    totalMenuItems: allMenuItems.length,
                    subMenus: Array.from(allSubMenus).map(menu => ({
                        index: menu.getAttribute('index'),
                        text: menu.textContent.trim().substring(0, 50),
                        visible: menu.offsetParent !== null
                    })),
                    menuItems: Array.from(allMenuItems).map(item => ({
                        index: item.getAttribute('index'),
                        text: item.textContent.trim(),
                        visible: item.offsetParent !== null
                    }))
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"DOM状态: {dom_state}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_computed_properties()
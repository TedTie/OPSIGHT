#!/usr/bin/env python3
"""
详细的Vue组件调试脚本
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

def debug_vue_components():
    """调试Vue组件"""
    driver = setup_driver()
    
    try:
        print("=== Vue组件详细调试 ===")
        
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
        
        # 3. 检查Vue组件状态
        print("\n2. 检查Vue组件状态...")
        component_state = driver.execute_script("""
            try {
                // 查找AppSidebar组件
                const sidebarElement = document.querySelector('.el-aside');
                if (!sidebarElement) return { error: 'Sidebar element not found' };
                
                // 尝试获取Vue实例
                const vueInstance = sidebarElement.__vueParentComponent || sidebarElement.__vue__;
                if (!vueInstance) return { error: 'Vue instance not found' };
                
                // 获取组件的响应式数据
                const setupState = vueInstance.setupState || {};
                
                return {
                    hasVueInstance: !!vueInstance,
                    setupStateKeys: Object.keys(setupState),
                    isSuperAdmin: setupState.isSuperAdmin,
                    isAdmin: setupState.isAdmin,
                    authStore: setupState.authStore ? {
                        user: setupState.authStore.user,
                        isAdmin: setupState.authStore.isAdmin,
                        isSuperAdmin: setupState.authStore.isSuperAdmin
                    } : null
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"Vue组件状态: {component_state}")
        
        # 4. 检查DOM元素
        print("\n3. 检查DOM元素...")
        dom_check = driver.execute_script("""
            try {
                const adminSubMenu = document.querySelector('[index="admin-menu"]');
                const aiMenuItem = document.querySelector('[index="/admin/ai"]');
                const metricsMenuItem = document.querySelector('[index="/admin/metrics"]');
                
                return {
                    adminSubMenuExists: !!adminSubMenu,
                    adminSubMenuVisible: adminSubMenu ? adminSubMenu.offsetParent !== null : false,
                    adminSubMenuDisplay: adminSubMenu ? getComputedStyle(adminSubMenu).display : null,
                    aiMenuItemExists: !!aiMenuItem,
                    aiMenuItemVisible: aiMenuItem ? aiMenuItem.offsetParent !== null : false,
                    metricsMenuItemExists: !!metricsMenuItem,
                    metricsMenuItemVisible: metricsMenuItem ? metricsMenuItem.offsetParent !== null : false,
                    allMenuItems: Array.from(document.querySelectorAll('.el-menu-item')).map(item => ({
                        index: item.getAttribute('index'),
                        text: item.textContent.trim(),
                        visible: item.offsetParent !== null
                    }))
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"DOM检查结果: {dom_check}")
        
        # 5. 强制触发Vue更新
        print("\n4. 强制触发Vue更新...")
        update_result = driver.execute_script("""
            try {
                // 触发localStorage事件
                window.dispatchEvent(new Event('storage'));
                
                // 等待一下
                setTimeout(() => {
                    // 强制触发Vue的响应式更新
                    const event = new CustomEvent('forceUpdate');
                    document.dispatchEvent(event);
                }, 100);
                
                return { success: true };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"更新结果: {update_result}")
        
        # 等待更新
        time.sleep(2)
        
        # 6. 再次检查DOM
        print("\n5. 更新后再次检查DOM...")
        final_dom_check = driver.execute_script("""
            try {
                const adminSubMenu = document.querySelector('[index="admin-menu"]');
                const aiMenuItem = document.querySelector('[index="/admin/ai"]');
                const metricsMenuItem = document.querySelector('[index="/admin/metrics"]');
                
                // 检查localStorage
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                const token = localStorage.getItem('token');
                
                return {
                    localStorage: {
                        hasUser: !!user,
                        userRole: user ? user.role : null,
                        hasToken: !!token,
                        isSuperAdmin: user ? user.role === 'super_admin' : false,
                        isAdmin: user ? (user.role === 'admin' || user.role === 'super_admin') : false
                    },
                    dom: {
                        adminSubMenuExists: !!adminSubMenu,
                        adminSubMenuVisible: adminSubMenu ? adminSubMenu.offsetParent !== null : false,
                        aiMenuItemExists: !!aiMenuItem,
                        aiMenuItemVisible: aiMenuItem ? aiMenuItem.offsetParent !== null : false,
                        metricsMenuItemExists: !!metricsMenuItem,
                        metricsMenuItemVisible: metricsMenuItem ? metricsMenuItem.offsetParent !== null : false
                    }
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"最终检查结果: {final_dom_check}")
        
        # 7. 检查控制台日志
        print("\n6. 检查控制台日志...")
        logs = driver.get_log('browser')
        relevant_logs = []
        for log in logs:
            if any(keyword in log['message'] for keyword in ['isSuperAdmin', 'isAdmin', 'computed', 'authStore']):
                relevant_logs.append(f"  {log['level']}: {log['message']}")
        
        if relevant_logs:
            print("相关日志:")
            for log in relevant_logs:
                print(log)
        else:
            print("未找到相关日志")
        
        print("\n=== 调试完成 ===")
        
    except Exception as e:
        print(f"调试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_vue_components()
#!/usr/bin/env python3
"""
测试authStore状态调试
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

def test_authstore_debug():
    """测试authStore状态"""
    driver = setup_driver()
    
    try:
        print("=== authStore状态调试 ===")
        
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
        
        # 2. 等待Vue应用完全加载
        time.sleep(5)
        
        # 3. 检查localStorage
        print("\n2. 检查localStorage...")
        user_data = driver.execute_script("return localStorage.getItem('user');")
        token = driver.execute_script("return localStorage.getItem('token');")
        
        print(f"User data: {user_data}")
        print(f"Token: {token}")
        
        # 4. 通过Vue devtools检查authStore
        print("\n3. 检查authStore状态...")
        authstore_check = driver.execute_script("""
            try {
                // 尝试多种方式访问authStore
                let authStore = null;
                
                // 方式1: 通过Vue app实例
                const app = document.querySelector('#app').__vue__;
                if (app && app.$pinia) {
                    const stores = app.$pinia._s;
                    authStore = stores.get('auth');
                }
                
                // 方式2: 通过全局变量
                if (!authStore && window.authStore) {
                    authStore = window.authStore;
                }
                
                // 方式3: 通过Vue 3的方式
                if (!authStore) {
                    const vueApp = document.querySelector('#app').__vueParentComponent;
                    if (vueApp && vueApp.appContext && vueApp.appContext.app) {
                        const pinia = vueApp.appContext.app.config.globalProperties.$pinia;
                        if (pinia && pinia._s) {
                            authStore = pinia._s.get('auth');
                        }
                    }
                }
                
                if (authStore) {
                    return {
                        found: true,
                        user: authStore.user,
                        isAuthenticated: authStore.isAuthenticated,
                        isAdmin: authStore.isAdmin,
                        isSuperAdmin: authStore.isSuperAdmin,
                        userRole: authStore.user ? authStore.user.role : null
                    };
                } else {
                    return { found: false, error: 'authStore not found' };
                }
            } catch (e) {
                return { found: false, error: e.message };
            }
        """)
        
        print(f"authStore检查结果: {authstore_check}")
        
        # 5. 直接在页面上执行权限检查
        print("\n4. 直接权限检查...")
        permission_check = driver.execute_script("""
            try {
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                if (!user) return { error: 'No user in localStorage' };
                
                const isAuthenticated = !!user;
                const isAdmin = user.role === 'admin' || user.role === 'super_admin';
                const isSuperAdmin = user.role === 'super_admin';
                
                return {
                    user: user,
                    isAuthenticated: isAuthenticated,
                    isAdmin: isAdmin,
                    isSuperAdmin: isSuperAdmin,
                    role: user.role
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"直接权限检查结果: {permission_check}")
        
        # 6. 检查菜单元素的v-if条件
        print("\n5. 检查菜单元素...")
        menu_check = driver.execute_script("""
            try {
                // 查找AI配置菜单元素
                const aiMenus = document.querySelectorAll('[index="/admin/ai"]');
                const metricsMenus = document.querySelectorAll('[index="/admin/metrics"]');
                
                const results = {
                    aiMenus: [],
                    metricsMenus: []
                };
                
                aiMenus.forEach((menu, index) => {
                    results.aiMenus.push({
                        index: index,
                        visible: menu.style.display !== 'none' && menu.offsetParent !== null,
                        innerHTML: menu.innerHTML.substring(0, 100),
                        hasVIf: menu.hasAttribute('v-if'),
                        vIfValue: menu.getAttribute('v-if')
                    });
                });
                
                metricsMenus.forEach((menu, index) => {
                    results.metricsMenus.push({
                        index: index,
                        visible: menu.style.display !== 'none' && menu.offsetParent !== null,
                        innerHTML: menu.innerHTML.substring(0, 100),
                        hasVIf: menu.hasAttribute('v-if'),
                        vIfValue: menu.getAttribute('v-if')
                    });
                });
                
                return results;
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"菜单元素检查: {menu_check}")
        
        # 7. 强制刷新页面并重新检查
        print("\n6. 刷新页面后重新检查...")
        driver.refresh()
        time.sleep(5)
        
        # 重新检查authStore
        authstore_after_refresh = driver.execute_script("""
            try {
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                return {
                    hasUser: !!user,
                    userRole: user ? user.role : null,
                    isSuperAdmin: user ? user.role === 'super_admin' : false
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"刷新后authStore状态: {authstore_after_refresh}")
        
        # 检查菜单是否出现
        try:
            ai_menu = driver.find_element(By.XPATH, "//el-menu-item[@index='/admin/ai']")
            print(f"✓ 找到AI配置菜单: 可见={ai_menu.is_displayed()}")
        except:
            print("✗ 未找到AI配置菜单")
            
        try:
            metrics_menu = driver.find_element(By.XPATH, "//el-menu-item[@index='/admin/metrics']")
            print(f"✓ 找到自定义指标菜单: 可见={metrics_menu.is_displayed()}")
        except:
            print("✗ 未找到自定义指标菜单")
        
        print("\n=== 调试完成 ===")
        
    except Exception as e:
        print(f"调试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_authstore_debug()
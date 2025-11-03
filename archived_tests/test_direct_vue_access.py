#!/usr/bin/env python3
"""
直接访问Vue组件状态测试
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

def test_direct_vue_access():
    """直接访问Vue组件状态"""
    driver = setup_driver()
    
    try:
        print("=== 直接Vue组件访问测试 ===")
        
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
        
        # 3. 直接在页面上执行Vue组件检查
        print("\n2. 直接检查Vue组件...")
        vue_check = driver.execute_script("""
            // 创建一个全局函数来调试
            window.debugVueComponents = function() {
                console.log('=== Vue组件调试开始 ===');
                
                const results = {
                    localStorage: {},
                    vueApp: {},
                    authStore: {},
                    menuElements: {}
                };
                
                try {
                    // 1. 检查localStorage
                    const user = JSON.parse(localStorage.getItem('user') || 'null');
                    const token = localStorage.getItem('token');
                    results.localStorage = {
                        hasUser: !!user,
                        userRole: user ? user.role : null,
                        hasToken: !!token,
                        isSuperAdmin: user ? user.role === 'super_admin' : false
                    };
                    console.log('localStorage检查:', results.localStorage);
                    
                    // 2. 检查Vue应用
                    const app = document.querySelector('#app');
                    results.vueApp = {
                        found: !!app,
                        hasVueInstance: !!(app && (app.__vue__ || app._vnode))
                    };
                    console.log('Vue应用检查:', results.vueApp);
                    
                    // 3. 尝试多种方式访问authStore
                    let authStore = null;
                    
                    // 方式1: Vue DevTools
                    if (window.__VUE_DEVTOOLS_GLOBAL_HOOK__ && window.__VUE_DEVTOOLS_GLOBAL_HOOK__.apps) {
                        const apps = window.__VUE_DEVTOOLS_GLOBAL_HOOK__.apps;
                        if (apps.length > 0) {
                            const vueApp = apps[0];
                            const pinia = vueApp.config.globalProperties.$pinia;
                            if (pinia && pinia._s) {
                                authStore = pinia._s.get('auth');
                            }
                        }
                    }
                    
                    if (authStore) {
                        results.authStore = {
                            found: true,
                            hasUser: !!authStore.user,
                            userRole: authStore.user ? authStore.user.role : null,
                            isAuthenticated: authStore.isAuthenticated,
                            isAdmin: authStore.isAdmin,
                            isSuperAdmin: authStore.isSuperAdmin
                        };
                    } else {
                        results.authStore = { found: false };
                    }
                    console.log('authStore检查:', results.authStore);
                    
                    // 4. 检查菜单元素
                    const adminMenus = document.querySelectorAll('[index="/admin/ai"], [index="/admin/metrics"]');
                    const allMenuItems = document.querySelectorAll('el-menu-item, .el-menu-item');
                    
                    results.menuElements = {
                        totalMenuItems: allMenuItems.length,
                        adminMenus: adminMenus.length,
                        menuDetails: []
                    };
                    
                    allMenuItems.forEach((item, index) => {
                        const indexAttr = item.getAttribute('index');
                        if (indexAttr && (indexAttr.includes('/admin/ai') || indexAttr.includes('/admin/metrics'))) {
                            results.menuElements.menuDetails.push({
                                index: indexAttr,
                                textContent: item.textContent.trim(),
                                visible: item.offsetParent !== null,
                                display: item.style.display,
                                hasVIf: item.hasAttribute('v-if')
                            });
                        }
                    });
                    
                    console.log('菜单元素检查:', results.menuElements);
                    
                    // 5. 强制刷新authStore（如果找到的话）
                    if (authStore && authStore.initAuth) {
                        console.log('强制刷新authStore...');
                        authStore.initAuth();
                        
                        // 重新检查authStore状态
                        results.authStoreAfterRefresh = {
                            hasUser: !!authStore.user,
                            userRole: authStore.user ? authStore.user.role : null,
                            isAuthenticated: authStore.isAuthenticated,
                            isAdmin: authStore.isAdmin,
                            isSuperAdmin: authStore.isSuperAdmin
                        };
                        console.log('刷新后authStore状态:', results.authStoreAfterRefresh);
                    }
                    
                } catch (e) {
                    console.error('Vue组件调试错误:', e);
                    results.error = e.message;
                }
                
                console.log('=== Vue组件调试结束 ===');
                return results;
            };
            
            // 执行调试
            return window.debugVueComponents();
        """)
        
        print(f"Vue组件检查结果: {vue_check}")
        
        # 4. 等待一下，然后检查是否有新的菜单元素出现
        print("\n3. 等待并重新检查菜单...")
        time.sleep(3)
        
        # 重新检查菜单
        menu_recheck = driver.execute_script("""
            const adminMenus = document.querySelectorAll('[index="/admin/ai"], [index="/admin/metrics"]');
            const aiMenus = document.querySelectorAll('[index="/admin/ai"]');
            const metricsMenus = document.querySelectorAll('[index="/admin/metrics"]');
            
            return {
                totalAdminMenus: adminMenus.length,
                aiMenus: aiMenus.length,
                metricsMenus: metricsMenus.length,
                aiMenuVisible: aiMenus.length > 0 ? aiMenus[0].offsetParent !== null : false,
                metricsMenuVisible: metricsMenus.length > 0 ? metricsMenus[0].offsetParent !== null : false
            };
        """)
        
        print(f"菜单重新检查结果: {menu_recheck}")
        
        # 5. 尝试手动创建菜单元素（测试用）
        print("\n4. 测试手动创建菜单元素...")
        manual_test = driver.execute_script("""
            try {
                // 查找管理功能子菜单容器
                const adminSubMenu = document.querySelector('el-sub-menu .el-menu, .el-sub-menu .el-menu');
                if (adminSubMenu) {
                    console.log('找到管理功能子菜单容器');
                    
                    // 创建测试菜单项
                    const testMenuItem = document.createElement('el-menu-item');
                    testMenuItem.setAttribute('index', '/admin/ai');
                    testMenuItem.innerHTML = '<span>AI配置 (测试)</span>';
                    testMenuItem.style.color = 'red';
                    
                    adminSubMenu.appendChild(testMenuItem);
                    
                    return { success: true, message: '测试菜单项已添加' };
                } else {
                    return { success: false, message: '未找到管理功能子菜单容器' };
                }
            } catch (e) {
                return { success: false, error: e.message };
            }
        """)
        
        print(f"手动测试结果: {manual_test}")
        
        # 6. 最终检查
        time.sleep(2)
        final_check = driver.find_elements(By.XPATH, "//span[contains(text(), 'AI配置')]")
        print(f"\n5. 最终检查 - AI配置菜单数量: {len(final_check)}")
        
        for i, menu in enumerate(final_check):
            print(f"  菜单 {i+1}: 文本='{menu.text}', 可见={menu.is_displayed()}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_direct_vue_access()
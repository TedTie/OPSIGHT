#!/usr/bin/env python3
"""
找到正确的Vue组件实例
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

def test_correct_vue_instance():
    """找到正确的Vue组件实例"""
    driver = setup_driver()
    
    try:
        print("=== 找到正确的Vue组件实例 ===")
        
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
        
        # 3. 查找所有可能的Vue实例
        print("\n2. 查找所有可能的Vue实例...")
        vue_instances = driver.execute_script("""
            try {
                const instances = [];
                
                // 查找所有可能包含Vue实例的元素
                const elements = document.querySelectorAll('*');
                
                elements.forEach((el, index) => {
                    if (el.__vueParentComponent || el.__vue__) {
                        const instance = el.__vueParentComponent || el.__vue__;
                        
                        instances.push({
                            index: index,
                            tagName: el.tagName,
                            className: el.className,
                            id: el.id,
                            componentType: instance.type ? instance.type.name : 'unknown',
                            hasSetupState: !!instance.setupState,
                            setupStateKeys: instance.setupState ? Object.keys(instance.setupState) : [],
                            hasProxy: !!instance.proxy,
                            proxyKeys: instance.proxy ? Object.keys(instance.proxy).slice(0, 10) : [] // 只取前10个
                        });
                    }
                });
                
                return instances;
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"找到 {len(vue_instances)} 个Vue实例:")
        for i, instance in enumerate(vue_instances):
            print(f"  实例 {i+1}: {instance}")
        
        # 4. 查找包含isSuperAdmin的Vue实例
        print("\n3. 查找包含isSuperAdmin的Vue实例...")
        target_instance = driver.execute_script("""
            try {
                const elements = document.querySelectorAll('*');
                
                for (let el of elements) {
                    const instance = el.__vueParentComponent || el.__vue__;
                    if (instance && instance.setupState) {
                        const keys = Object.keys(instance.setupState);
                        if (keys.includes('isSuperAdmin') || keys.includes('isAdmin')) {
                            return {
                                tagName: el.tagName,
                                className: el.className,
                                componentType: instance.type ? instance.type.name : 'unknown',
                                setupStateKeys: keys,
                                isSuperAdmin: instance.setupState.isSuperAdmin,
                                isAdmin: instance.setupState.isAdmin,
                                authStore: instance.setupState.authStore ? {
                                    user: instance.setupState.authStore.user,
                                    isAdmin: instance.setupState.authStore.isAdmin,
                                    isSuperAdmin: instance.setupState.authStore.isSuperAdmin
                                } : null
                            };
                        }
                    }
                }
                
                return { notFound: true };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"目标实例: {target_instance}")
        
        # 5. 直接在页面上测试计算属性
        print("\n4. 直接在页面上测试计算属性...")
        direct_test = driver.execute_script("""
            try {
                // 手动创建计算属性逻辑
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                const isSuperAdmin = user && user.role === 'super_admin';
                const isAdmin = user && (user.role === 'admin' || user.role === 'super_admin');
                
                console.log('Direct test - isSuperAdmin:', isSuperAdmin);
                console.log('Direct test - isAdmin:', isAdmin);
                
                // 检查菜单项是否应该显示
                const shouldShowAI = isSuperAdmin;
                const shouldShowMetrics = isSuperAdmin;
                const shouldShowAdminMenu = isAdmin;
                
                return {
                    user: user,
                    isSuperAdmin: isSuperAdmin,
                    isAdmin: isAdmin,
                    shouldShowAI: shouldShowAI,
                    shouldShowMetrics: shouldShowMetrics,
                    shouldShowAdminMenu: shouldShowAdminMenu
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"直接测试结果: {direct_test}")
        
        # 6. 检查菜单项的实际显示状态
        print("\n5. 检查菜单项的实际显示状态...")
        menu_status = driver.execute_script("""
            try {
                // 查找管理功能菜单
                const adminMenu = document.querySelector('[index="admin-menu"]');
                
                // 查找AI配置和自定义指标菜单项
                const aiMenu = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.trim() === 'AI配置'
                );
                
                const metricsMenu = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.trim() === '自定义指标'
                );
                
                return {
                    adminMenuExists: !!adminMenu,
                    adminMenuVisible: adminMenu ? adminMenu.offsetParent !== null : false,
                    adminMenuHTML: adminMenu ? adminMenu.outerHTML.substring(0, 200) + '...' : null,
                    
                    aiMenuExists: !!aiMenu,
                    aiMenuVisible: aiMenu ? aiMenu.offsetParent !== null : false,
                    aiMenuIndex: aiMenu ? aiMenu.getAttribute('index') : null,
                    
                    metricsMenuExists: !!metricsMenu,
                    metricsMenuVisible: metricsMenu ? metricsMenu.offsetParent !== null : false,
                    metricsMenuIndex: metricsMenu ? metricsMenu.getAttribute('index') : null
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"菜单状态: {menu_status}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_correct_vue_instance()
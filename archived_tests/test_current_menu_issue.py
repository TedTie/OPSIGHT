#!/usr/bin/env python3
"""
测试当前菜单问题的具体状态
"""

import time
import json
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

def test_current_menu_issue():
    """测试当前菜单问题的具体状态"""
    driver = setup_driver()
    
    try:
        print("=== 测试当前菜单问题状态 ===")
        
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
        time.sleep(3)
        
        # 3. 检查用户权限状态
        print("\n2. 检查用户权限状态...")
        auth_status = driver.execute_script("""
            try {
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                return {
                    user: user,
                    role: user?.role,
                    isSuperAdmin: user?.role === 'super_admin',
                    isAdmin: user?.role === 'admin' || user?.role === 'super_admin'
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        print(f"用户权限状态: {json.dumps(auth_status, indent=2, ensure_ascii=False)}")
        
        # 4. 检查Vue组件的计算属性
        print("\n3. 检查Vue组件的计算属性...")
        vue_state = driver.execute_script("""
            try {
                const sidebar = document.querySelector('.app-sidebar');
                if (!sidebar) return { error: 'Sidebar not found' };
                
                // 尝试获取Vue实例
                const vueInstance = sidebar.__vueParentComponent || sidebar.__vue__;
                if (!vueInstance) return { error: 'Vue instance not found' };
                
                const setupState = vueInstance.setupState || {};
                
                return {
                    hasVueInstance: true,
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
        print(f"Vue组件状态: {json.dumps(vue_state, indent=2, ensure_ascii=False)}")
        
        # 5. 检查菜单DOM结构
        print("\n4. 检查菜单DOM结构...")
        menu_structure = driver.execute_script("""
            try {
                const adminSubMenu = document.querySelector('[index="admin-menu"]');
                const aiMenuItem = document.querySelector('[index="/admin/ai"]');
                const metricsMenuItem = document.querySelector('[index="/admin/metrics"]');
                
                return {
                    adminSubMenu: {
                        exists: !!adminSubMenu,
                        visible: adminSubMenu ? adminSubMenu.offsetParent !== null : false,
                        display: adminSubMenu ? getComputedStyle(adminSubMenu).display : null,
                        innerHTML: adminSubMenu ? adminSubMenu.innerHTML.substring(0, 200) + '...' : null
                    },
                    aiMenuItem: {
                        exists: !!aiMenuItem,
                        visible: aiMenuItem ? aiMenuItem.offsetParent !== null : false,
                        index: aiMenuItem ? aiMenuItem.getAttribute('index') : null,
                        text: aiMenuItem ? aiMenuItem.textContent.trim() : null
                    },
                    metricsMenuItem: {
                        exists: !!metricsMenuItem,
                        visible: metricsMenuItem ? metricsMenuItem.offsetParent !== null : false,
                        index: metricsMenuItem ? metricsMenuItem.getAttribute('index') : null,
                        text: metricsMenuItem ? metricsMenuItem.textContent.trim() : null
                    }
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        print(f"菜单DOM结构: {json.dumps(menu_structure, indent=2, ensure_ascii=False)}")
        
        # 6. 检查页面源码中的路径
        print("\n5. 检查页面源码中的路径...")
        page_source = driver.page_source
        has_ai_text = 'AI配置' in page_source
        has_metrics_text = '自定义指标' in page_source
        has_ai_path = '/admin/ai' in page_source
        has_metrics_path = '/admin/metrics' in page_source
        
        print(f"页面源码检查:")
        print(f"  - 包含'AI配置'文本: {has_ai_text}")
        print(f"  - 包含'自定义指标'文本: {has_metrics_text}")
        print(f"  - 包含'/admin/ai'路径: {has_ai_path}")
        print(f"  - 包含'/admin/metrics'路径: {has_metrics_path}")
        
        # 7. 尝试点击管理功能菜单
        print("\n6. 尝试点击管理功能菜单...")
        try:
            admin_menu = driver.find_element(By.CSS_SELECTOR, '[index="admin-menu"]')
            if admin_menu:
                admin_menu.click()
                time.sleep(2)
                print("✓ 成功点击管理功能菜单")
                
                # 检查子菜单是否展开
                submenu_check = driver.execute_script("""
                    try {
                        const aiMenuItem = document.querySelector('[index="/admin/ai"]');
                        const metricsMenuItem = document.querySelector('[index="/admin/metrics"]');
                        
                        return {
                            aiMenuItem: {
                                exists: !!aiMenuItem,
                                visible: aiMenuItem ? aiMenuItem.offsetParent !== null : false,
                                index: aiMenuItem ? aiMenuItem.getAttribute('index') : null
                            },
                            metricsMenuItem: {
                                exists: !!metricsMenuItem,
                                visible: metricsMenuItem ? metricsMenuItem.offsetParent !== null : false,
                                index: metricsMenuItem ? metricsMenuItem.getAttribute('index') : null
                            }
                        };
                    } catch (e) {
                        return { error: e.message };
                    }
                """)
                print(f"子菜单展开状态: {json.dumps(submenu_check, indent=2, ensure_ascii=False)}")
            else:
                print("❌ 未找到管理功能菜单")
        except Exception as e:
            print(f"❌ 点击管理功能菜单失败: {e}")
        
        # 8. 刷新页面测试持久化
        print("\n7. 测试页面刷新后的菜单状态...")
        driver.refresh()
        time.sleep(5)
        
        refresh_check = driver.execute_script("""
            try {
                const adminSubMenu = document.querySelector('[index="admin-menu"]');
                return {
                    adminMenuExists: !!adminSubMenu,
                    adminMenuVisible: adminSubMenu ? adminSubMenu.offsetParent !== null : false,
                    currentUrl: window.location.href
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        print(f"刷新后菜单状态: {json.dumps(refresh_check, indent=2, ensure_ascii=False)}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_current_menu_issue()
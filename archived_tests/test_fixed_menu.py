#!/usr/bin/env python3
"""
测试修复后的菜单功能
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

def test_fixed_menu():
    """测试修复后的菜单功能"""
    driver = setup_driver()
    
    try:
        print("=== 测试修复后的菜单功能 ===")
        
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
        
        # 3. 检查修复后的Vue组件状态
        print("\n2. 检查修复后的Vue组件状态...")
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
                    userState: setupState.userState,
                    isSuperAdmin: setupState.isSuperAdmin,
                    isAdmin: setupState.isAdmin,
                    setupStateKeys: Object.keys(setupState)
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        print(f"Vue组件状态: {json.dumps(vue_state, indent=2, ensure_ascii=False)}")
        
        # 4. 检查管理功能菜单是否存在
        print("\n3. 检查管理功能菜单...")
        admin_menu_check = driver.execute_script("""
            try {
                const adminSubMenu = document.querySelector('[index="admin-menu"]');
                const aiMenuItem = document.querySelector('[index="/admin/ai"]');
                const metricsMenuItem = document.querySelector('[index="/admin/metrics"]');
                
                return {
                    adminSubMenu: {
                        exists: !!adminSubMenu,
                        visible: adminSubMenu ? adminSubMenu.offsetParent !== null : false,
                        text: adminSubMenu ? adminSubMenu.textContent.trim() : null
                    },
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
        print(f"管理功能菜单检查: {json.dumps(admin_menu_check, indent=2, ensure_ascii=False)}")
        
        # 5. 检查页面源码中的路径
        print("\n4. 检查页面源码中的路径...")
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
        
        # 6. 尝试点击管理功能菜单
        print("\n5. 尝试点击管理功能菜单...")
        try:
            admin_menu = driver.find_element(By.CSS_SELECTOR, '[index="admin-menu"]')
            if admin_menu:
                print("✓ 找到管理功能菜单")
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
                
                # 7. 尝试点击AI配置菜单
                print("\n6. 尝试点击AI配置菜单...")
                try:
                    ai_menu = driver.find_element(By.CSS_SELECTOR, '[index="/admin/ai"]')
                    if ai_menu:
                        ai_menu.click()
                        time.sleep(2)
                        
                        current_url = driver.current_url
                        print(f"✓ 点击AI配置菜单后的URL: {current_url}")
                        
                        if '/admin/ai' in current_url:
                            print("✓ 成功跳转到AI配置页面")
                        else:
                            print("❌ 未能跳转到AI配置页面")
                    else:
                        print("❌ 未找到AI配置菜单")
                except Exception as e:
                    print(f"❌ 点击AI配置菜单失败: {e}")
                
            else:
                print("❌ 未找到管理功能菜单")
        except Exception as e:
            print(f"❌ 点击管理功能菜单失败: {e}")
        
        # 8. 测试页面刷新后的菜单持久化
        print("\n7. 测试页面刷新后的菜单持久化...")
        driver.get("http://localhost:3001/dashboard")
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
        
        # 总结测试结果
        print("\n=== 测试结果总结 ===")
        admin_exists = admin_menu_check.get('adminSubMenu', {}).get('exists', False)
        ai_exists = admin_menu_check.get('aiMenuItem', {}).get('exists', False)
        metrics_exists = admin_menu_check.get('metricsMenuItem', {}).get('exists', False)
        refresh_persistent = refresh_check.get('adminMenuExists', False)
        
        print(f"✓ 管理功能菜单存在: {admin_exists}")
        print(f"✓ AI配置菜单存在: {ai_exists}")
        print(f"✓ 自定义指标菜单存在: {metrics_exists}")
        print(f"✓ 页面源码包含路径: {has_ai_path and has_metrics_path}")
        print(f"✓ 刷新后菜单持久化: {refresh_persistent}")
        
        if admin_exists and ai_exists and metrics_exists and has_ai_path and has_metrics_path and refresh_persistent:
            print("\n🎉 所有测试通过！菜单功能已修复！")
        else:
            print("\n⚠️ 部分测试未通过，需要进一步修复")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_fixed_menu()
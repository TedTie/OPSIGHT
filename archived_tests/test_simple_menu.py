#!/usr/bin/env python3
"""
简单测试当前菜单状态
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

def test_simple_menu():
    """简单测试菜单状态"""
    driver = setup_driver()
    
    try:
        print("=== 简单菜单测试 ===")
        
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
        
        # 3. 检查localStorage
        print("\n2. 检查localStorage...")
        storage_check = driver.execute_script("""
            const user = JSON.parse(localStorage.getItem('user') || 'null');
            const token = localStorage.getItem('token');
            return {
                user: user,
                token: !!token,
                isSuperAdmin: user && user.role === 'super_admin',
                isAdmin: user && (user.role === 'admin' || user.role === 'super_admin')
            };
        """)
        print(f"LocalStorage状态: {json.dumps(storage_check, indent=2, ensure_ascii=False)}")
        
        # 4. 检查菜单DOM结构
        print("\n3. 检查菜单DOM结构...")
        menu_check = driver.execute_script("""
            const menu = document.querySelector('.sidebar-menu');
            if (!menu) return { error: 'Menu not found' };
            
            const menuItems = Array.from(menu.querySelectorAll('.el-menu-item, .el-sub-menu'));
            const menuStructure = menuItems.map(item => ({
                tag: item.tagName,
                class: item.className,
                index: item.getAttribute('index'),
                text: item.textContent.trim(),
                visible: item.offsetParent !== null
            }));
            
            return {
                totalItems: menuItems.length,
                structure: menuStructure,
                hasAdminMenu: !!menu.querySelector('[index="admin-menu"]'),
                hasAIMenu: !!menu.querySelector('[index="/admin/ai"]'),
                hasMetricsMenu: !!menu.querySelector('[index="/admin/metrics"]')
            };
        """)
        print(f"菜单DOM结构: {json.dumps(menu_check, indent=2, ensure_ascii=False)}")
        
        # 5. 检查页面源码
        print("\n4. 检查页面源码...")
        page_source = driver.page_source
        has_admin_paths = {
            'ai_config_text': 'AI配置' in page_source,
            'metrics_text': '自定义指标' in page_source,
            'ai_path': '/admin/ai' in page_source,
            'metrics_path': '/admin/metrics' in page_source,
            'admin_menu': 'admin-menu' in page_source
        }
        print(f"页面源码检查: {json.dumps(has_admin_paths, indent=2, ensure_ascii=False)}")
        
        # 6. 尝试手动触发Vue更新
        print("\n5. 尝试手动触发Vue更新...")
        vue_update = driver.execute_script("""
            try {
                // 查找Vue应用实例
                const app = document.querySelector('#app');
                if (!app) return { error: 'App element not found' };
                
                // 尝试触发Vue的响应式更新
                const event = new Event('storage');
                window.dispatchEvent(event);
                
                // 等待一下让Vue处理
                return new Promise(resolve => {
                    setTimeout(() => {
                        const menu = document.querySelector('.sidebar-menu');
                        const hasAdminMenu = !!menu.querySelector('[index="admin-menu"]');
                        resolve({
                            success: true,
                            hasAdminMenuAfterUpdate: hasAdminMenu
                        });
                    }, 1000);
                });
            } catch (e) {
                return { error: e.message };
            }
        """)
        print(f"Vue更新结果: {json.dumps(vue_update, indent=2, ensure_ascii=False)}")
        
        # 7. 最终状态检查
        print("\n6. 最终状态检查...")
        time.sleep(2)
        final_check = driver.execute_script("""
            const menu = document.querySelector('.sidebar-menu');
            const adminMenu = menu ? menu.querySelector('[index="admin-menu"]') : null;
            const aiMenu = menu ? menu.querySelector('[index="/admin/ai"]') : null;
            const metricsMenu = menu ? menu.querySelector('[index="/admin/metrics"]') : null;
            
            return {
                menuExists: !!menu,
                adminMenuExists: !!adminMenu,
                adminMenuVisible: adminMenu ? adminMenu.offsetParent !== null : false,
                aiMenuExists: !!aiMenu,
                metricsMenuExists: !!metricsMenu,
                currentUrl: window.location.href
            };
        """)
        print(f"最终状态: {json.dumps(final_check, indent=2, ensure_ascii=False)}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_simple_menu()
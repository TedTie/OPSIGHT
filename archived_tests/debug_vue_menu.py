#!/usr/bin/env python3
"""
调试Vue菜单渲染问题
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def debug_vue_menu():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("🔍 调试Vue菜单渲染...")
        
        # 1. 登录
        print("\n1. 登录...")
        driver.get("http://localhost:3001/login")
        time.sleep(2)
        
        username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='用户名']")))
        username_input.send_keys("admin")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button")
        login_button.click()
        time.sleep(3)
        
        # 2. 检查authStore状态
        print("2. 检查authStore状态...")
        auth_state = driver.execute_script("""
            try {
                const app = document.querySelector('#app').__vue_app__;
                const pinia = app.config.globalProperties.$pinia;
                const authStore = pinia.state.value.auth;
                return {
                    isAuthenticated: authStore.user !== null,
                    isAdmin: authStore.user && (authStore.user.role === 'admin' || authStore.user.role === 'super_admin'),
                    isSuperAdmin: authStore.user && authStore.user.role === 'super_admin',
                    user: authStore.user
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"AuthStore状态: {json.dumps(auth_state, indent=2, ensure_ascii=False)}")
        
        # 3. 检查DOM中的菜单元素
        print("3. 检查DOM中的菜单元素...")
        
        # 获取所有菜单项
        menu_items = driver.find_elements(By.CSS_SELECTOR, ".el-menu-item, .el-sub-menu")
        print(f"找到 {len(menu_items)} 个菜单项")
        
        for i, item in enumerate(menu_items):
            try:
                text = item.text.strip()
                classes = item.get_attribute('class')
                index = item.get_attribute('index')
                print(f"  菜单项 {i+1}: '{text}' (index: {index}, classes: {classes})")
            except:
                print(f"  菜单项 {i+1}: [无法获取信息]")
        
        # 4. 专门检查管理功能菜单
        print("4. 检查管理功能菜单...")
        try:
            admin_submenu = driver.find_element(By.CSS_SELECTOR, ".el-sub-menu[index='admin-menu']")
            print("✅ 找到管理功能子菜单")
            
            # 点击展开
            admin_submenu.click()
            time.sleep(1)
            
            # 检查子菜单项
            sub_items = driver.find_elements(By.CSS_SELECTOR, ".el-sub-menu[index='admin-menu'] .el-menu-item")
            print(f"管理功能子菜单项数量: {len(sub_items)}")
            
            for i, item in enumerate(sub_items):
                try:
                    text = item.text.strip()
                    index = item.get_attribute('index')
                    style = item.get_attribute('style')
                    print(f"  子菜单项 {i+1}: '{text}' (index: {index}, style: {style})")
                except:
                    print(f"  子菜单项 {i+1}: [无法获取信息]")
                    
        except Exception as e:
            print(f"❌ 检查管理功能菜单失败: {e}")
        
        # 5. 检查Vue组件的条件渲染
        print("5. 检查Vue组件的条件渲染...")
        render_check = driver.execute_script("""
            try {
                // 查找AppSidebar组件实例
                const sidebarEl = document.querySelector('.app-sidebar');
                if (sidebarEl && sidebarEl.__vueParentComponent) {
                    const component = sidebarEl.__vueParentComponent;
                    const authStore = component.setupState.authStore;
                    
                    return {
                        authStore_isAdmin: authStore.isAdmin,
                        authStore_isSuperAdmin: authStore.isSuperAdmin,
                        authStore_user: authStore.user
                    };
                }
                return { error: 'Component not found' };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"Vue组件状态: {json.dumps(render_check, indent=2, ensure_ascii=False)}")
        
        # 6. 检查页面源码中的菜单
        print("6. 检查页面源码...")
        page_source = driver.page_source
        
        print(f"页面包含'AI配置': {'AI配置' in page_source}")
        print(f"页面包含'自定义指标': {'自定义指标' in page_source}")
        print(f"页面包含'admin/ai': {'/admin/ai' in page_source}")
        print(f"页面包含'admin/metrics': {'/admin/metrics' in page_source}")
        
        # 7. 强制刷新页面再检查
        print("7. 刷新页面后再检查...")
        driver.refresh()
        time.sleep(3)
        
        try:
            admin_submenu = driver.find_element(By.CSS_SELECTOR, ".el-sub-menu[index='admin-menu']")
            admin_submenu.click()
            time.sleep(1)
            
            ai_config_items = driver.find_elements(By.XPATH, "//span[text()='AI配置']")
            metrics_items = driver.find_elements(By.XPATH, "//span[text()='自定义指标']")
            
            print(f"刷新后 - AI配置菜单数量: {len(ai_config_items)}")
            print(f"刷新后 - 自定义指标菜单数量: {len(metrics_items)}")
            
        except Exception as e:
            print(f"刷新后检查失败: {e}")
        
        print("\n✅ Vue菜单调试完成")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_vue_menu()
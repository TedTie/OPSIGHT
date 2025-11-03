#!/usr/bin/env python3
"""
测试菜单HTML结构
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

def test_menu_html():
    """测试菜单HTML结构"""
    driver = setup_driver()
    
    try:
        print("=== 测试菜单HTML结构 ===")
        
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
        
        # 3. 点击管理功能菜单展开
        print("\n2. 点击管理功能菜单...")
        try:
            admin_menu = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='管理功能']"))
            )
            admin_menu.click()
            time.sleep(2)
            print("✓ 管理功能菜单已展开")
        except Exception as e:
            print(f"✗ 点击管理功能菜单失败: {e}")
            return
        
        # 4. 获取详细的HTML结构
        print("\n3. 获取详细的HTML结构...")
        html_structure = driver.execute_script("""
            try {
                // 获取整个侧边栏的HTML
                const sidebar = document.querySelector('.el-aside');
                if (!sidebar) return { error: 'Sidebar not found' };
                
                // 获取管理功能子菜单的HTML
                const adminSubMenu = document.querySelector('[index="admin-menu"]');
                const adminSubMenuHTML = adminSubMenu ? adminSubMenu.outerHTML : null;
                
                // 查找所有包含"AI配置"文本的元素
                const aiElements = Array.from(document.querySelectorAll('*')).filter(el => 
                    el.textContent && el.textContent.trim() === 'AI配置'
                );
                
                const aiElementsInfo = aiElements.map(el => ({
                    tagName: el.tagName,
                    className: el.className,
                    index: el.getAttribute('index'),
                    outerHTML: el.outerHTML,
                    parentHTML: el.parentElement ? el.parentElement.outerHTML.substring(0, 200) + '...' : null
                }));
                
                // 查找所有包含"自定义指标"文本的元素
                const metricsElements = Array.from(document.querySelectorAll('*')).filter(el => 
                    el.textContent && el.textContent.trim() === '自定义指标'
                );
                
                const metricsElementsInfo = metricsElements.map(el => ({
                    tagName: el.tagName,
                    className: el.className,
                    index: el.getAttribute('index'),
                    outerHTML: el.outerHTML,
                    parentHTML: el.parentElement ? el.parentElement.outerHTML.substring(0, 200) + '...' : null
                }));
                
                return {
                    adminSubMenuHTML: adminSubMenuHTML,
                    aiElements: aiElementsInfo,
                    metricsElements: metricsElementsInfo
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print("HTML结构分析:")
        if html_structure and 'error' not in html_structure:
            admin_html = html_structure.get('adminSubMenuHTML', 'Not found')
            if admin_html and admin_html != 'Not found':
                print(f"管理功能子菜单HTML: {admin_html[:500]}...")
            else:
                print("管理功能子菜单HTML: Not found")
            print(f"\nAI配置元素: {html_structure.get('aiElements', [])}")
            print(f"\n自定义指标元素: {html_structure.get('metricsElements', [])}")
        else:
            print(f"获取HTML结构失败: {html_structure}")
        
        # 5. 检查Vue组件的计算属性
        print("\n4. 检查Vue组件的计算属性...")
        vue_state = driver.execute_script("""
            try {
                const sidebar = document.querySelector('.el-aside');
                const vueInstance = sidebar.__vueParentComponent;
                
                if (vueInstance && vueInstance.setupState) {
                    return {
                        isSuperAdmin: vueInstance.setupState.isSuperAdmin,
                        isAdmin: vueInstance.setupState.isAdmin,
                        setupStateKeys: Object.keys(vueInstance.setupState)
                    };
                }
                return { error: 'Vue instance or setupState not found' };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"Vue组件状态: {vue_state}")
        
        # 6. 检查控制台日志
        print("\n5. 检查控制台日志...")
        logs = driver.get_log('browser')
        for log in logs[-10:]:  # 只显示最后10条日志
            if 'isSuperAdmin' in log['message'] or 'isAdmin' in log['message']:
                print(f"控制台日志: {log['message']}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_menu_html()
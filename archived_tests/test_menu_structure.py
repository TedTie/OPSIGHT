#!/usr/bin/env python3
"""
检查菜单结构
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

def test_menu_structure():
    """检查菜单结构"""
    driver = setup_driver()
    
    try:
        print("=== 检查菜单结构 ===")
        
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
        
        # 3. 获取完整的菜单结构
        print("\n2. 获取菜单结构...")
        menu_structure = driver.execute_script("""
            try {
                const menu = document.querySelector('.sidebar-menu') || 
                           document.querySelector('.el-menu') ||
                           document.querySelector('[role="menu"]') ||
                           document.querySelector('nav') ||
                           document.querySelector('.menu');
                
                if (!menu) {
                    return { error: 'No menu found' };
                }
                
                function getElementInfo(element) {
                    return {
                        tagName: element.tagName,
                        className: element.className,
                        id: element.id,
                        index: element.getAttribute('index'),
                        role: element.getAttribute('role'),
                        textContent: element.textContent ? element.textContent.trim().substring(0, 50) : '',
                        visible: element.offsetParent !== null,
                        children: Array.from(element.children).map(child => getElementInfo(child))
                    };
                }
                
                return {
                    success: true,
                    menuSelector: menu.className || menu.tagName,
                    menuStructure: getElementInfo(menu)
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"菜单结构: {menu_structure}")
        
        # 4. 查找所有可能的菜单项
        print("\n3. 查找所有菜单项...")
        menu_items = driver.execute_script("""
            try {
                const allElements = document.querySelectorAll('*');
                const menuItems = [];
                
                for (let element of allElements) {
                    const text = element.textContent ? element.textContent.trim() : '';
                    const index = element.getAttribute('index');
                    const role = element.getAttribute('role');
                    
                    // 查找可能的菜单项
                    if (
                        (text.includes('知识库') || text.includes('管理') || text.includes('AI') || text.includes('指标')) ||
                        (index && (index.includes('knowledge') || index.includes('admin') || index.includes('ai') || index.includes('metrics'))) ||
                        (role === 'menuitem')
                    ) {
                        menuItems.push({
                            tagName: element.tagName,
                            className: element.className,
                            id: element.id,
                            index: index,
                            role: role,
                            textContent: text.substring(0, 100),
                            visible: element.offsetParent !== null,
                            display: window.getComputedStyle(element).display,
                            parent: element.parentElement ? element.parentElement.tagName + '.' + element.parentElement.className : 'none'
                        });
                    }
                }
                
                return { success: true, menuItems: menuItems };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"菜单项: {menu_items}")
        
        # 5. 查找侧边栏容器
        print("\n4. 查找侧边栏容器...")
        sidebar_info = driver.execute_script("""
            try {
                const selectors = [
                    '.sidebar',
                    '.el-aside',
                    '.app-sidebar',
                    '.navigation',
                    '.nav-sidebar',
                    '[class*="sidebar"]',
                    '[class*="aside"]'
                ];
                
                const sidebars = [];
                
                for (let selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    for (let element of elements) {
                        sidebars.push({
                            selector: selector,
                            tagName: element.tagName,
                            className: element.className,
                            id: element.id,
                            visible: element.offsetParent !== null,
                            childrenCount: element.children.length,
                            textContent: element.textContent ? element.textContent.trim().substring(0, 200) : ''
                        });
                    }
                }
                
                return { success: true, sidebars: sidebars };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"侧边栏信息: {sidebar_info}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_menu_structure()
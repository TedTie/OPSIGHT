#!/usr/bin/env python3
"""
测试DOM结构
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

def test_dom_structure():
    """测试DOM结构"""
    driver = setup_driver()
    
    try:
        print("=== 测试DOM结构 ===")
        
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
        
        # 3. 检查详细的DOM结构
        print("\n2. 检查详细的DOM结构...")
        dom_structure = driver.execute_script("""
            try {
                const sidebar = document.querySelector('.el-aside');
                if (!sidebar) return { error: 'Sidebar not found' };
                
                // 获取所有子菜单的详细信息
                const subMenus = Array.from(document.querySelectorAll('.el-sub-menu')).map(menu => {
                    const titleElement = menu.querySelector('.el-sub-menu__title');
                    const menuItems = Array.from(menu.querySelectorAll('.el-menu-item')).map(item => ({
                        index: item.getAttribute('index'),
                        text: item.textContent.trim(),
                        visible: item.offsetParent !== null,
                        display: getComputedStyle(item).display
                    }));
                    
                    return {
                        index: menu.getAttribute('index'),
                        title: titleElement ? titleElement.textContent.trim() : '',
                        visible: menu.offsetParent !== null,
                        display: getComputedStyle(menu).display,
                        menuItems: menuItems,
                        outerHTML: menu.outerHTML.substring(0, 200) + '...'
                    };
                });
                
                // 获取所有菜单项的详细信息
                const allMenuItems = Array.from(document.querySelectorAll('.el-menu-item')).map(item => ({
                    index: item.getAttribute('index'),
                    text: item.textContent.trim(),
                    visible: item.offsetParent !== null,
                    display: getComputedStyle(item).display,
                    parentElement: item.parentElement.className
                }));
                
                return {
                    subMenus: subMenus,
                    allMenuItems: allMenuItems,
                    sidebarHTML: sidebar.innerHTML.substring(0, 500) + '...'
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"DOM结构: {dom_structure}")
        
        # 4. 尝试点击管理功能菜单
        print("\n3. 尝试点击管理功能菜单...")
        try:
            # 查找管理功能菜单
            admin_menu = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='管理功能']"))
            )
            print("✓ 找到管理功能菜单")
            
            # 点击展开
            admin_menu.click()
            time.sleep(2)
            
            # 再次检查DOM结构
            print("\n4. 点击后检查DOM结构...")
            expanded_structure = driver.execute_script("""
                try {
                    const aiMenus = Array.from(document.querySelectorAll('*')).filter(el => 
                        el.textContent && el.textContent.trim() === 'AI配置'
                    ).map(el => ({
                        tagName: el.tagName,
                        className: el.className,
                        index: el.getAttribute('index'),
                        visible: el.offsetParent !== null,
                        display: getComputedStyle(el).display,
                        parentClassName: el.parentElement ? el.parentElement.className : null
                    }));
                    
                    const metricsMenus = Array.from(document.querySelectorAll('*')).filter(el => 
                        el.textContent && el.textContent.trim() === '自定义指标'
                    ).map(el => ({
                        tagName: el.tagName,
                        className: el.className,
                        index: el.getAttribute('index'),
                        visible: el.offsetParent !== null,
                        display: getComputedStyle(el).display,
                        parentClassName: el.parentElement ? el.parentElement.className : null
                    }));
                    
                    return {
                        aiMenus: aiMenus,
                        metricsMenus: metricsMenus
                    };
                } catch (e) {
                    return { error: e.message };
                }
            """)
            
            print(f"展开后的结构: {expanded_structure}")
            
            # 5. 尝试点击AI配置菜单
            print("\n5. 尝试点击AI配置菜单...")
            try:
                ai_menu = driver.find_element(By.XPATH, "//span[text()='AI配置']")
                if ai_menu.is_displayed():
                    ai_menu.click()
                    time.sleep(2)
                    
                    current_url = driver.current_url
                    print(f"点击AI配置后的URL: {current_url}")
                    
                    if "/admin/ai" in current_url:
                        print("✓ 成功跳转到AI配置页面")
                    else:
                        print("✗ 未跳转到AI配置页面")
                else:
                    print("✗ AI配置菜单不可见")
            except Exception as e:
                print(f"✗ 点击AI配置菜单失败: {e}")
                
        except Exception as e:
            print(f"✗ 未找到管理功能菜单: {e}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_dom_structure()
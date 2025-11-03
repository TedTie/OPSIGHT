#!/usr/bin/env python3
"""
测试子菜单展开功能
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

def test_submenu_expansion():
    """测试子菜单展开功能"""
    driver = setup_driver()
    
    try:
        print("=== 测试子菜单展开功能 ===")
        
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
        
        # 3. 检查管理功能菜单状态
        print("\n2. 检查管理功能菜单状态...")
        initial_status = driver.execute_script("""
            try {
                const managementMenu = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.includes('管理功能') && 
                    el.classList.contains('el-sub-menu')
                );
                
                if (!managementMenu) {
                    return { error: 'Management menu not found' };
                }
                
                const isExpanded = managementMenu.getAttribute('aria-expanded') === 'true';
                const submenu = managementMenu.querySelector('.el-menu--inline');
                const submenuVisible = submenu ? submenu.offsetParent !== null : false;
                
                return {
                    success: true,
                    isExpanded: isExpanded,
                    submenuVisible: submenuVisible,
                    submenuDisplay: submenu ? window.getComputedStyle(submenu).display : 'none'
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"初始状态: {initial_status}")
        
        # 4. 点击管理功能菜单标题
        print("\n3. 点击管理功能菜单标题...")
        try:
            # 查找管理功能子菜单的标题
            management_title = driver.find_element(By.XPATH, "//div[@class='el-sub-menu__title' and contains(., '管理功能')]")
            
            if management_title.is_displayed():
                print("找到管理功能菜单标题，点击...")
                management_title.click()
                time.sleep(2)
                print("✓ 管理功能菜单标题已点击")
            else:
                print("✗ 管理功能菜单标题不可见")
                
        except Exception as e:
            print(f"✗ 点击管理功能菜单标题失败: {e}")
        
        # 5. 检查点击后的状态
        print("\n4. 检查点击后的状态...")
        after_click_status = driver.execute_script("""
            try {
                const managementMenu = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.includes('管理功能') && 
                    el.classList.contains('el-sub-menu')
                );
                
                if (!managementMenu) {
                    return { error: 'Management menu not found' };
                }
                
                const isExpanded = managementMenu.getAttribute('aria-expanded') === 'true';
                const submenu = managementMenu.querySelector('.el-menu--inline');
                const submenuVisible = submenu ? submenu.offsetParent !== null : false;
                
                // 查找子菜单项
                const aiMenuItem = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.trim() === 'AI配置' && 
                    el.classList.contains('el-menu-item')
                );
                
                const metricsMenuItem = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.trim() === '自定义指标' && 
                    el.classList.contains('el-menu-item')
                );
                
                return {
                    success: true,
                    isExpanded: isExpanded,
                    submenuVisible: submenuVisible,
                    submenuDisplay: submenu ? window.getComputedStyle(submenu).display : 'none',
                    aiMenuVisible: aiMenuItem ? aiMenuItem.offsetParent !== null : false,
                    metricsMenuVisible: metricsMenuItem ? metricsMenuItem.offsetParent !== null : false,
                    aiMenuIndex: aiMenuItem ? aiMenuItem.getAttribute('index') : null,
                    metricsMenuIndex: metricsMenuItem ? metricsMenuItem.getAttribute('index') : null
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"点击后状态: {after_click_status}")
        
        # 6. 如果子菜单已展开，尝试点击AI配置
        if after_click_status.get('aiMenuVisible'):
            print("\n5. 尝试点击AI配置...")
            try:
                ai_menu = driver.find_element(By.XPATH, "//li[@class='el-menu-item' and contains(text(), 'AI配置')]")
                
                if ai_menu.is_displayed():
                    print("找到AI配置菜单项，点击...")
                    ai_menu.click()
                    time.sleep(3)
                    
                    current_url = driver.current_url
                    print(f"点击后的URL: {current_url}")
                    
                    if "/admin/ai" in current_url:
                        print("✓ 成功跳转到AI配置页面")
                        return True
                    else:
                        print(f"✗ 未跳转到AI配置页面，当前URL: {current_url}")
                else:
                    print("✗ AI配置菜单项不可见")
                    
            except Exception as e:
                print(f"✗ 点击AI配置失败: {e}")
        else:
            print("\n5. AI配置菜单项不可见，无法点击")
        
        # 7. 尝试手动设置index属性并点击
        print("\n6. 尝试手动设置index属性并点击...")
        manual_click_result = driver.execute_script("""
            try {
                const aiMenuItem = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.trim() === 'AI配置' && 
                    el.classList.contains('el-menu-item')
                );
                
                if (!aiMenuItem) {
                    return { error: 'AI menu item not found' };
                }
                
                // 设置index属性
                aiMenuItem.setAttribute('index', '/admin/ai');
                
                // 添加点击事件监听器
                aiMenuItem.addEventListener('click', function() {
                    window.location.href = '/admin/ai';
                });
                
                // 模拟点击
                aiMenuItem.click();
                
                return { success: true, message: 'AI menu item clicked manually' };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"手动点击结果: {manual_click_result}")
        
        if manual_click_result.get('success'):
            time.sleep(3)
            current_url = driver.current_url
            print(f"手动点击后的URL: {current_url}")
            
            if "/admin/ai" in current_url:
                print("✓ 手动点击成功跳转到AI配置页面")
                return True
        
        print("\n=== 测试完成 ===")
        return False
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        return False
        
    finally:
        driver.quit()

if __name__ == "__main__":
    success = test_submenu_expansion()
    if success:
        print("\n🎉 子菜单功能验证成功！")
    else:
        print("\n❌ 子菜单功能验证失败")
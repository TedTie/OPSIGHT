#!/usr/bin/env python3
"""
测试管理功能菜单点击问题
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def test_management_menu():
    print("🚀 测试管理功能菜单点击问题")
    print("=" * 50)
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        # 1. 登录
        print("📍 登录系统...")
        driver.get("http://localhost:3001/login")
        
        # 输入用户名
        username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='用户名']")))
        username_input.clear()
        username_input.send_keys("admin")
        
        # 点击登录按钮
        login_button = driver.find_element(By.CSS_SELECTOR, "button.el-button--primary, button[type='submit'], .login-button")
        login_button.click()
        
        # 等待登录完成
        wait.until(EC.url_contains("dashboard"))
        print("✅ 登录成功")
        
        # 2. 等待页面完全加载
        time.sleep(3)
        
        # 3. 检查管理功能菜单的状态
        print("\n📍 检查管理功能菜单状态...")
        
        # 查找管理功能菜单
        management_menu_selectors = [
            "li.el-sub-menu[index='admin']",
            ".el-sub-menu:has(span:contains('管理功能'))",
            ".el-sub-menu .el-sub-menu__title:has(span:contains('管理功能'))",
            "*[data-index='admin']"
        ]
        
        management_element = None
        for selector in management_menu_selectors:
            try:
                if 'contains' in selector or 'has' in selector:
                    # 使用XPath
                    elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'el-sub-menu')]//span[contains(text(), '管理功能')]/..")
                    if elements:
                        management_element = elements[0]
                        print(f"   ✅ 找到管理功能菜单元素 (XPath)")
                        break
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        management_element = elements[0]
                        print(f"   ✅ 找到管理功能菜单元素 (CSS: {selector})")
                        break
            except Exception as e:
                continue
        
        if not management_element:
            print("   ❌ 未找到管理功能菜单元素")
            return
        
        # 4. 检查元素属性
        print("\n📍 检查管理功能菜单属性...")
        try:
            print(f"   标签名: {management_element.tag_name}")
            print(f"   类名: {management_element.get_attribute('class')}")
            print(f"   是否可见: {management_element.is_displayed()}")
            print(f"   是否可点击: {management_element.is_enabled()}")
            print(f"   文本内容: {management_element.text}")
            print(f"   位置: {management_element.location}")
            print(f"   大小: {management_element.size}")
        except Exception as e:
            print(f"   ❌ 获取元素属性失败: {e}")
        
        # 5. 尝试多种点击方式
        print("\n📍 尝试不同的点击方式...")
        
        # 方式1: 直接点击
        try:
            print("   尝试直接点击...")
            management_element.click()
            time.sleep(2)
            
            # 检查是否展开
            submenu_items = driver.find_elements(By.XPATH, "//*[contains(text(), '用户管理') or contains(text(), '组别管理')]")
            if submenu_items:
                print("   ✅ 直接点击成功，子菜单已展开")
                for item in submenu_items:
                    print(f"     子菜单项: {item.text}")
            else:
                print("   ❌ 直接点击后子菜单未展开")
        except Exception as e:
            print(f"   ❌ 直接点击失败: {e}")
        
        # 方式2: 点击标题部分
        try:
            print("   尝试点击标题部分...")
            title_element = management_element.find_element(By.CSS_SELECTOR, ".el-sub-menu__title")
            title_element.click()
            time.sleep(2)
            
            submenu_items = driver.find_elements(By.XPATH, "//*[contains(text(), '用户管理') or contains(text(), '组别管理')]")
            if submenu_items:
                print("   ✅ 点击标题成功，子菜单已展开")
                for item in submenu_items:
                    print(f"     子菜单项: {item.text}")
            else:
                print("   ❌ 点击标题后子菜单未展开")
        except Exception as e:
            print(f"   ❌ 点击标题失败: {e}")
        
        # 方式3: 使用ActionChains
        try:
            print("   尝试使用ActionChains...")
            actions = ActionChains(driver)
            actions.move_to_element(management_element).click().perform()
            time.sleep(2)
            
            submenu_items = driver.find_elements(By.XPATH, "//*[contains(text(), '用户管理') or contains(text(), '组别管理')]")
            if submenu_items:
                print("   ✅ ActionChains点击成功，子菜单已展开")
                for item in submenu_items:
                    print(f"     子菜单项: {item.text}")
            else:
                print("   ❌ ActionChains点击后子菜单未展开")
        except Exception as e:
            print(f"   ❌ ActionChains点击失败: {e}")
        
        # 方式4: JavaScript点击
        try:
            print("   尝试JavaScript点击...")
            driver.execute_script("arguments[0].click();", management_element)
            time.sleep(2)
            
            submenu_items = driver.find_elements(By.XPATH, "//*[contains(text(), '用户管理') or contains(text(), '组别管理')]")
            if submenu_items:
                print("   ✅ JavaScript点击成功，子菜单已展开")
                for item in submenu_items:
                    print(f"     子菜单项: {item.text}")
            else:
                print("   ❌ JavaScript点击后子菜单未展开")
        except Exception as e:
            print(f"   ❌ JavaScript点击失败: {e}")
        
        # 6. 检查CSS样式和状态
        print("\n📍 检查CSS样式和状态...")
        try:
            computed_style = driver.execute_script("""
                var element = arguments[0];
                var style = window.getComputedStyle(element);
                return {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    pointerEvents: style.pointerEvents,
                    zIndex: style.zIndex,
                    position: style.position
                };
            """, management_element)
            
            print(f"   CSS样式: {computed_style}")
            
            # 检查是否有遮挡元素
            overlapping = driver.execute_script("""
                var element = arguments[0];
                var rect = element.getBoundingClientRect();
                var centerX = rect.left + rect.width / 2;
                var centerY = rect.top + rect.height / 2;
                var topElement = document.elementFromPoint(centerX, centerY);
                return {
                    topElement: topElement ? topElement.tagName + '.' + topElement.className : 'null',
                    isSameElement: topElement === element
                };
            """, management_element)
            
            print(f"   元素遮挡检查: {overlapping}")
            
        except Exception as e:
            print(f"   ❌ CSS检查失败: {e}")
        
        # 7. 截图保存
        print(f"\n📸 截图已保存: management_menu_debug.png")
        driver.save_screenshot("management_menu_debug.png")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        driver.save_screenshot("management_menu_error.png")
        
    finally:
        driver.quit()
    
    print("\n" + "=" * 50)
    print("📊 管理功能菜单测试完成")

if __name__ == "__main__":
    test_management_menu()
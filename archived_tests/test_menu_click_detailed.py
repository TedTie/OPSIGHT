#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """设置Chrome驱动"""
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    return driver

def login(driver):
    """登录系统"""
    print("🔐 开始登录...")
    
    # 访问登录页面
    driver.get("http://localhost:3000/login")
    wait = WebDriverWait(driver, 10)
    
    try:
        # 等待页面加载
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        
        # 查找用户名输入框
        username_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[placeholder*='用户名'], input[type='text']")
        ))
        username_input.clear()
        username_input.send_keys("admin")
        
        # 查找密码输入框
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.clear()
        password_input.send_keys("admin123")
        
        # 查找并点击登录按钮
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-button, button.el-button--primary")
        login_button.click()
        
        # 等待登录完成
        time.sleep(3)
        
        # 检查是否跳转到仪表板
        current_url = driver.current_url
        print(f"✅ 登录成功，当前URL: {current_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return False

def check_auth_state(driver):
    """检查认证状态"""
    print("\n🔍 检查认证状态...")
    
    try:
        # 检查localStorage
        user_data = driver.execute_script("return localStorage.getItem('user');")
        token = driver.execute_script("return localStorage.getItem('token');")
        
        print(f"LocalStorage user: {user_data}")
        print(f"LocalStorage token: {token}")
        
        if user_data:
            user_obj = json.loads(user_data)
            print(f"用户角色: {user_obj.get('role', 'N/A')}")
            print(f"用户名: {user_obj.get('username', 'N/A')}")
            return user_obj
        
        return None
        
    except Exception as e:
        print(f"❌ 检查认证状态失败: {e}")
        return None

def find_management_menu(driver):
    """查找管理功能菜单"""
    print("\n🔍 查找管理功能菜单...")
    
    selectors = [
        "li.el-sub-menu[index='admin']",
        ".el-sub-menu[index='admin']",
        "li.el-sub-menu",
        ".el-sub-menu",
        "//li[contains(@class, 'el-sub-menu')]",
        "//li[contains(text(), '管理功能')]",
        "//span[contains(text(), '管理功能')]",
        "//*[contains(text(), '管理功能')]"
    ]
    
    for selector in selectors:
        try:
            if selector.startswith("//"):
                elements = driver.find_elements(By.XPATH, selector)
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            if elements:
                print(f"✅ 找到 {len(elements)} 个元素，选择器: {selector}")
                for i, element in enumerate(elements):
                    try:
                        text = element.text
                        tag = element.tag_name
                        classes = element.get_attribute('class')
                        index = element.get_attribute('index')
                        print(f"  元素 {i+1}: 标签={tag}, 文本='{text}', 类={classes}, index={index}")
                        
                        if '管理功能' in text or index == 'admin':
                            print(f"  ✅ 找到管理功能菜单: {element}")
                            return element
                    except Exception as e:
                        print(f"  ❌ 获取元素信息失败: {e}")
            else:
                print(f"❌ 未找到元素，选择器: {selector}")
                
        except Exception as e:
            print(f"❌ 选择器 {selector} 失败: {e}")
    
    return None

def analyze_menu_element(driver, element):
    """分析菜单元素"""
    print("\n🔍 分析菜单元素...")
    
    try:
        # 基本信息
        tag = element.tag_name
        text = element.text
        classes = element.get_attribute('class')
        index = element.get_attribute('index')
        
        print(f"标签: {tag}")
        print(f"文本: '{text}'")
        print(f"类: {classes}")
        print(f"index: {index}")
        
        # 位置和大小
        location = element.location
        size = element.size
        print(f"位置: {location}")
        print(f"大小: {size}")
        
        # 可见性和可点击性
        is_displayed = element.is_displayed()
        is_enabled = element.is_enabled()
        print(f"可见: {is_displayed}")
        print(f"可用: {is_enabled}")
        
        # CSS样式
        styles = driver.execute_script("""
            var element = arguments[0];
            var styles = window.getComputedStyle(element);
            return {
                display: styles.display,
                visibility: styles.visibility,
                opacity: styles.opacity,
                pointerEvents: styles.pointerEvents,
                zIndex: styles.zIndex,
                position: styles.position
            };
        """, element)
        print(f"CSS样式: {styles}")
        
        # 检查是否被遮挡
        center_x = location['x'] + size['width'] // 2
        center_y = location['y'] + size['height'] // 2
        
        top_element = driver.execute_script("""
            return document.elementFromPoint(arguments[0], arguments[1]);
        """, center_x, center_y)
        
        if top_element:
            top_tag = top_element.tag_name
            top_classes = top_element.get_attribute('class')
            print(f"顶层元素: {top_tag}, 类: {top_classes}")
            
            if top_element == element:
                print("✅ 元素未被遮挡")
            else:
                print("❌ 元素被遮挡")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析元素失败: {e}")
        return False

def try_click_methods(driver, element):
    """尝试多种点击方法"""
    print("\n🔍 尝试多种点击方法...")
    
    methods = [
        ("直接点击", lambda: element.click()),
        ("ActionChains点击", lambda: ActionChains(driver).click(element).perform()),
        ("JavaScript点击", lambda: driver.execute_script("arguments[0].click();", element)),
        ("JavaScript触发事件", lambda: driver.execute_script("""
            var event = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true
            });
            arguments[0].dispatchEvent(event);
        """, element)),
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"尝试 {method_name}...")
            
            # 记录点击前的状态
            before_classes = element.get_attribute('class')
            
            # 执行点击
            method_func()
            time.sleep(1)
            
            # 记录点击后的状态
            after_classes = element.get_attribute('class')
            
            print(f"  点击前类: {before_classes}")
            print(f"  点击后类: {after_classes}")
            
            # 检查子菜单是否展开
            submenu_items = driver.find_elements(By.CSS_SELECTOR, ".el-sub-menu .el-menu-item")
            print(f"  子菜单项数量: {len(submenu_items)}")
            
            if submenu_items:
                print(f"  ✅ {method_name} 成功，找到 {len(submenu_items)} 个子菜单项")
                for i, item in enumerate(submenu_items):
                    item_text = item.text
                    item_index = item.get_attribute('index')
                    print(f"    子菜单 {i+1}: '{item_text}' (index: {item_index})")
                return True
            else:
                print(f"  ❌ {method_name} 失败，未找到子菜单项")
                
        except Exception as e:
            print(f"  ❌ {method_name} 异常: {e}")
    
    return False

def check_submenu_expansion(driver):
    """检查子菜单展开状态"""
    print("\n🔍 检查子菜单展开状态...")
    
    try:
        # 查找所有子菜单
        submenus = driver.find_elements(By.CSS_SELECTOR, ".el-sub-menu")
        print(f"找到 {len(submenus)} 个子菜单")
        
        for i, submenu in enumerate(submenus):
            submenu_text = submenu.text
            submenu_classes = submenu.get_attribute('class')
            is_opened = 'is-opened' in submenu_classes
            
            print(f"子菜单 {i+1}: '{submenu_text}', 类: {submenu_classes}, 已展开: {is_opened}")
            
            # 查找子菜单项
            submenu_items = submenu.find_elements(By.CSS_SELECTOR, ".el-menu-item")
            print(f"  子菜单项数量: {len(submenu_items)}")
            
            for j, item in enumerate(submenu_items):
                item_text = item.text
                item_index = item.get_attribute('index')
                item_visible = item.is_displayed()
                print(f"    项 {j+1}: '{item_text}' (index: {item_index}, 可见: {item_visible})")
        
    except Exception as e:
        print(f"❌ 检查子菜单展开状态失败: {e}")

def main():
    """主函数"""
    driver = setup_driver()
    
    try:
        # 登录
        if not login(driver):
            return
        
        # 检查认证状态
        user_data = check_auth_state(driver)
        if not user_data:
            print("❌ 无法获取用户数据")
            return
        
        # 等待页面完全加载
        time.sleep(3)
        
        # 查找管理功能菜单
        management_menu = find_management_menu(driver)
        if not management_menu:
            print("❌ 未找到管理功能菜单")
            return
        
        # 分析菜单元素
        analyze_menu_element(driver, management_menu)
        
        # 检查当前子菜单状态
        check_submenu_expansion(driver)
        
        # 尝试点击
        success = try_click_methods(driver, management_menu)
        
        if success:
            print("\n✅ 管理功能菜单点击成功！")
        else:
            print("\n❌ 管理功能菜单点击失败！")
        
        # 最终检查
        print("\n🔍 最终状态检查...")
        check_submenu_expansion(driver)
        
        # 保持浏览器打开一段时间以便观察
        print("\n⏳ 保持浏览器打开10秒以便观察...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        
    finally:
        driver.quit()
        print("\n🔚 测试完成")

if __name__ == "__main__":
    main()
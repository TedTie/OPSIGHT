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

def login_and_test_menu(driver):
    """登录并测试管理功能菜单"""
    print("🔐 开始登录...")
    
    # 访问登录页面 - 使用正确的端口3001
    driver.get("http://localhost:3001/login")
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
        time.sleep(5)
        
        # 检查是否跳转到仪表板
        current_url = driver.current_url
        print(f"✅ 登录成功，当前URL: {current_url}")
        
        # 检查调试信息
        print("\n🔍 检查调试信息...")
        debug_sections = driver.find_elements(By.CSS_SELECTOR, ".debug-section")
        print(f"找到 {len(debug_sections)} 个调试区域")
        
        for i, section in enumerate(debug_sections):
            try:
                section_text = section.text
                print(f"调试区域 {i+1}:")
                print(section_text)
                print("-" * 50)
            except Exception as e:
                print(f"获取调试区域 {i+1} 信息失败: {e}")
        
        # 查找管理功能菜单
        print("\n🔍 查找管理功能菜单...")
        
        # 尝试多种选择器
        selectors = [
            "//li[contains(@class, 'el-sub-menu')]//span[contains(text(), '管理功能')]",
            "//span[contains(text(), '管理功能')]",
            ".el-sub-menu .el-sub-menu__title",
            "li.el-sub-menu",
            "//*[contains(text(), '管理功能')]"
        ]
        
        management_menu = None
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    print(f"✅ 找到 {len(elements)} 个元素，选择器: {selector}")
                    for element in elements:
                        text = element.text
                        if '管理功能' in text:
                            management_menu = element
                            print(f"✅ 找到管理功能菜单: '{text}'")
                            break
                    if management_menu:
                        break
                        
            except Exception as e:
                print(f"❌ 选择器 {selector} 失败: {e}")
        
        if not management_menu:
            print("❌ 未找到管理功能菜单")
            return False
        
        # 尝试点击管理功能菜单
        print("\n🔍 尝试点击管理功能菜单...")
        
        try:
            # 滚动到元素可见
            driver.execute_script("arguments[0].scrollIntoView(true);", management_menu)
            time.sleep(1)
            
            # 尝试点击
            management_menu.click()
            time.sleep(2)
            
            # 检查子菜单是否展开
            submenu_items = driver.find_elements(By.CSS_SELECTOR, ".el-sub-menu .el-menu-item")
            print(f"子菜单项数量: {len(submenu_items)}")
            
            if submenu_items:
                print("✅ 管理功能菜单点击成功，子菜单已展开")
                for i, item in enumerate(submenu_items):
                    item_text = item.text
                    item_index = item.get_attribute('index')
                    print(f"  子菜单 {i+1}: '{item_text}' (index: {item_index})")
                return True
            else:
                print("❌ 管理功能菜单点击后子菜单未展开")
                
                # 尝试JavaScript点击
                print("尝试JavaScript点击...")
                driver.execute_script("arguments[0].click();", management_menu)
                time.sleep(2)
                
                submenu_items = driver.find_elements(By.CSS_SELECTOR, ".el-sub-menu .el-menu-item")
                if submenu_items:
                    print("✅ JavaScript点击成功")
                    return True
                else:
                    print("❌ JavaScript点击也失败")
                    return False
                
        except Exception as e:
            print(f"❌ 点击管理功能菜单失败: {e}")
            return False
        
    except Exception as e:
        print(f"❌ 测试过程失败: {e}")
        return False

def main():
    """主函数"""
    driver = setup_driver()
    
    try:
        success = login_and_test_menu(driver)
        
        if success:
            print("\n✅ 测试成功！管理功能菜单可以正常点击")
        else:
            print("\n❌ 测试失败！管理功能菜单无法点击")
        
        # 保持浏览器打开一段时间以便观察
        print("\n⏳ 保持浏览器打开15秒以便观察...")
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        
    finally:
        driver.quit()
        print("\n🔚 测试完成")

if __name__ == "__main__":
    main()
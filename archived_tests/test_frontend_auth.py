#!/usr/bin/env python3
"""
前端认证状态和权限测试脚本
"""

import os
import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """设置Chrome驱动"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ Chrome驱动设置失败: {e}")
        return None

def test_login_and_permissions():
    """测试登录和权限状态"""
    print("🔐 开始测试前端认证状态和权限...")
    print("=" * 50)
    
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        # 1. 访问前端首页
        print("📍 步骤1: 访问前端首页...")
        driver.get("http://localhost:3000")
        time.sleep(3)
        
        current_url = driver.current_url
        print(f"   当前URL: {current_url}")
        
        # 2. 检查是否被重定向到登录页
        if "/login" in current_url:
            print("   ✅ 未登录状态，正确重定向到登录页")
            
            # 3. 执行登录
            print("📍 步骤2: 执行登录...")
            
            # 查找用户名输入框
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[placeholder*='用户名'], input[placeholder*='username']"))
            )
            username_input.clear()
            username_input.send_keys("super_admin")
            print("   ✅ 输入用户名: super_admin")
            
            # 查找密码输入框
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[placeholder*='密码'], input[placeholder*='password']")
            password_input.clear()
            password_input.send_keys("123456")
            print("   ✅ 输入密码")
            
            # 点击登录按钮
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-button, button:contains('登录')")
            login_button.click()
            print("   ✅ 点击登录按钮")
            
            # 4. 等待登录完成
            print("📍 步骤3: 等待登录完成...")
            time.sleep(5)
            
            current_url = driver.current_url
            print(f"   登录后URL: {current_url}")
            
            if "/dashboard" in current_url or "/login" not in current_url:
                print("   ✅ 登录成功")
                
                # 5. 检查localStorage中的用户信息
                print("📍 步骤4: 检查用户认证状态...")
                
                # 获取localStorage中的用户信息
                user_data = driver.execute_script("return localStorage.getItem('user');")
                token_data = driver.execute_script("return localStorage.getItem('token');")
                
                print(f"   Token存在: {'是' if token_data else '否'}")
                
                if user_data:
                    try:
                        user_info = json.loads(user_data)
                        print(f"   用户名: {user_info.get('username', '未知')}")
                        print(f"   身份: {user_info.get('identity', '未知')}")
                        print(f"   是否管理员: {'是' if user_info.get('is_admin') else '否'}")
                        print(f"   是否超级管理员: {'是' if user_info.get('is_super_admin') else '否'}")
                        print(f"   组名: {user_info.get('group_name', '未知')}")
                    except json.JSONDecodeError:
                        print("   ❌ 用户数据格式错误")
                else:
                    print("   ❌ 未找到用户数据")
                
                # 6. 检查页面元素
                print("📍 步骤5: 检查页面导航元素...")
                
                # 检查设置菜单项
                try:
                    settings_menu = driver.find_element(By.CSS_SELECTOR, "a[href='/settings'], .el-menu-item[index='/settings']")
                    if settings_menu.is_displayed():
                        print("   ✅ 设置菜单可见")
                    else:
                        print("   ❌ 设置菜单不可见")
                except NoSuchElementException:
                    print("   ❌ 未找到设置菜单")
                
                # 检查管理功能菜单
                try:
                    admin_menu = driver.find_element(By.CSS_SELECTOR, ".el-sub-menu[index='admin'], .admin-menu")
                    if admin_menu.is_displayed():
                        print("   ✅ 管理功能菜单可见")
                    else:
                        print("   ❌ 管理功能菜单不可见")
                except NoSuchElementException:
                    print("   ❌ 未找到管理功能菜单")
                
                # 7. 检查控制台错误
                print("📍 步骤6: 检查控制台错误...")
                logs = driver.get_log('browser')
                errors = [log for log in logs if log['level'] == 'SEVERE']
                
                if errors:
                    print(f"   ❌ 发现{len(errors)}个控制台错误:")
                    for error in errors[:5]:  # 只显示前5个错误
                        print(f"      - {error['message']}")
                else:
                    print("   ✅ 无控制台错误")
                
                return True
            else:
                print("   ❌ 登录失败")
                return False
        else:
            print("   ✅ 已登录状态，直接访问仪表板")
            
            # 检查已登录用户的状态
            print("📍 步骤2: 检查已登录用户状态...")
            
            # 获取localStorage中的用户信息
            user_data = driver.execute_script("return localStorage.getItem('user');")
            token_data = driver.execute_script("return localStorage.getItem('token');")
            
            print(f"   Token存在: {'是' if token_data else '否'}")
            
            if user_data:
                try:
                    user_info = json.loads(user_data)
                    print(f"   用户名: {user_info.get('username', '未知')}")
                    print(f"   身份: {user_info.get('identity', '未知')}")
                    print(f"   是否管理员: {'是' if user_info.get('is_admin') else '否'}")
                    print(f"   是否超级管理员: {'是' if user_info.get('is_super_admin') else '否'}")
                    print(f"   组名: {user_info.get('group_name', '未知')}")
                    
                    # 如果不是超级管理员，这可能是问题所在
                    if not user_info.get('is_super_admin'):
                        print("   ⚠️  当前用户不是超级管理员，这可能导致设置和管理页面不显示")
                        
                except json.JSONDecodeError:
                    print("   ❌ 用户数据格式错误")
            else:
                print("   ❌ 未找到用户数据")
            
            # 等待页面完全加载
            time.sleep(3)
            
            # 检查页面元素
            print("📍 步骤3: 检查页面导航元素...")
            
            # 检查设置菜单项
            try:
                settings_elements = driver.find_elements(By.CSS_SELECTOR, "a[href='/settings'], .el-menu-item[index='/settings'], *[href='/settings']")
                if settings_elements:
                    visible_settings = [elem for elem in settings_elements if elem.is_displayed()]
                    if visible_settings:
                        print("   ✅ 设置菜单可见")
                    else:
                        print("   ❌ 设置菜单存在但不可见")
                else:
                    print("   ❌ 未找到设置菜单")
            except Exception as e:
                print(f"   ❌ 检查设置菜单时出错: {e}")
            
            # 检查管理功能菜单
            try:
                admin_elements = driver.find_elements(By.CSS_SELECTOR, ".el-sub-menu[index='admin'], .admin-menu, *:contains('管理功能')")
                if admin_elements:
                    visible_admin = [elem for elem in admin_elements if elem.is_displayed()]
                    if visible_admin:
                        print("   ✅ 管理功能菜单可见")
                    else:
                        print("   ❌ 管理功能菜单存在但不可见")
                else:
                    print("   ❌ 未找到管理功能菜单")
            except Exception as e:
                print(f"   ❌ 检查管理功能菜单时出错: {e}")
            
            # 检查所有菜单项
            print("📍 步骤4: 检查所有可见菜单项...")
            try:
                menu_items = driver.find_elements(By.CSS_SELECTOR, ".el-menu-item, .nav-item, a[href^='/']")
                visible_menus = []
                for item in menu_items:
                    if item.is_displayed():
                        text = item.text.strip()
                        href = item.get_attribute('href') or item.get_attribute('index')
                        if text or href:
                            visible_menus.append(f"{text} ({href})")
                
                if visible_menus:
                    print(f"   找到{len(visible_menus)}个可见菜单项:")
                    for menu in visible_menus[:10]:  # 只显示前10个
                        print(f"      - {menu}")
                else:
                    print("   ❌ 未找到可见菜单项")
            except Exception as e:
                print(f"   ❌ 检查菜单项时出错: {e}")
            
            # 检查控制台错误
            print("📍 步骤5: 检查控制台错误...")
            try:
                logs = driver.get_log('browser')
                errors = [log for log in logs if log['level'] == 'SEVERE']
                
                if errors:
                    print(f"   ❌ 发现{len(errors)}个控制台错误:")
                    for error in errors[:5]:  # 只显示前5个错误
                        print(f"      - {error['message']}")
                else:
                    print("   ✅ 无控制台错误")
            except Exception as e:
                print(f"   ❌ 检查控制台错误时出错: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        driver.quit()

def main():
    """主函数"""
    print("🚀 前端认证状态和权限测试")
    print("=" * 50)
    
    # 检查服务状态
    print("📍 检查服务状态...")
    
    # 检查前端服务
    import requests
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        print(f"   前端服务状态: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 前端服务不可用: {e}")
        return False
    
    # 检查后端服务
    try:
        response = requests.get("http://localhost:9000/docs", timeout=5)
        print(f"   后端服务状态: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 后端服务不可用: {e}")
        return False
    
    # 执行测试
    success = test_login_and_permissions()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 测试完成")
    else:
        print("❌ 测试失败")
    
    return success

if __name__ == "__main__":
    main()
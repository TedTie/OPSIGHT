#!/usr/bin/env python3
"""
登录跳转测试脚本
测试登录成功后是否正确跳转到仪表板
"""

import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def test_login_redirect():
    """测试登录跳转功能"""
    print("🔍 测试登录跳转功能...")
    print("=" * 50)
    
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = None
    try:
        # 启动浏览器
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        # 1. 访问首页，应该重定向到登录页
        print("📍 步骤1: 访问首页...")
        driver.get("http://localhost:3001/")
        time.sleep(2)
        
        current_url = driver.current_url
        print(f"   当前URL: {current_url}")
        
        if "/login" in current_url:
            print("✅ 未登录用户正确重定向到登录页")
        else:
            print("❌ 未正确重定向到登录页")
            return False
        
        # 2. 填写登录表单
        print("📍 步骤2: 填写登录表单...")
        try:
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='用户名']"))
            )
            username_input.clear()
            username_input.send_keys("admin")
            print("   ✅ 用户名输入完成")
            
            # 3. 点击登录按钮
            print("📍 步骤3: 点击登录按钮...")
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-button")
            login_button.click()
            print("   ✅ 登录按钮点击完成")
            
            # 4. 等待跳转到仪表板
            print("📍 步骤4: 等待跳转...")
            WebDriverWait(driver, 10).until(
                lambda d: "/dashboard" in d.current_url or "/login" not in d.current_url
            )
            
            final_url = driver.current_url
            print(f"   最终URL: {final_url}")
            
            if "/dashboard" in final_url:
                print("✅ 登录成功后正确跳转到仪表板")
                
                # 5. 检查页面内容
                print("📍 步骤5: 检查仪表板页面...")
                try:
                    # 等待页面加载
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    page_title = driver.title
                    print(f"   页面标题: {page_title}")
                    
                    # 检查是否有导航栏或其他仪表板元素
                    nav_elements = driver.find_elements(By.CSS_SELECTOR, "nav, .nav, .sidebar, .header")
                    if nav_elements:
                        print("   ✅ 找到导航元素，页面加载正常")
                    else:
                        print("   ⚠️  未找到导航元素，可能页面未完全加载")
                    
                    return True
                    
                except Exception as e:
                    print(f"   ❌ 检查仪表板页面时出错: {e}")
                    return False
            else:
                print("❌ 登录后未正确跳转到仪表板")
                return False
                
        except Exception as e:
            print(f"❌ 登录过程中出错: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

def test_api_login():
    """测试API登录功能"""
    print("\n🔍 测试API登录功能...")
    print("-" * 30)
    
    try:
        url = "http://localhost:8001/api/v1/auth/login"
        data = {"username": "admin"}
        
        response = requests.post(url, json=data)
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API登录成功")
            print(f"   用户: {result['user']['username']}")
            print(f"   身份: {result['user']['identity']}")
            return True
        else:
            print(f"❌ API登录失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始登录跳转测试...")
    
    # 先测试API
    api_success = test_api_login()
    
    if api_success:
        # 再测试前端跳转
        ui_success = test_login_redirect()
        
        print("\n" + "=" * 50)
        print("📋 测试结果总结:")
        print(f"   API登录: {'✅ 通过' if api_success else '❌ 失败'}")
        print(f"   前端跳转: {'✅ 通过' if ui_success else '❌ 失败'}")
        
        if api_success and ui_success:
            print("🎉 所有测试通过！登录跳转功能正常")
        else:
            print("⚠️  部分测试失败，需要进一步检查")
    else:
        print("❌ API登录失败，跳过前端测试")
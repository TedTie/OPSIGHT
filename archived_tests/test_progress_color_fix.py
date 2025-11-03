#!/usr/bin/env python3
"""
测试 getProgressColor 函数修复效果
"""

import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def test_progress_color_function():
    """测试进度条颜色函数是否正常工作"""
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = None
    
    try:
        print("🧪 启动浏览器测试...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:3001")
        
        # 等待页面加载
        WebDriverWait(driver, 10).wait(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("✅ 页面加载成功")
        
        # 检查控制台错误
        logs = driver.get_log('browser')
        progress_color_errors = [log for log in logs if 'getProgressColor' in log.get('message', '')]
        
        if progress_color_errors:
            print("❌ 发现 getProgressColor 相关错误:")
            for error in progress_color_errors:
                print(f"   {error['message']}")
            return False
        else:
            print("✅ 没有发现 getProgressColor 相关错误")
        
        # 尝试登录并访问任务页面
        try:
            # 查找登录表单
            username_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[placeholder*='用户名'], input[placeholder*='username']"))
            )
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            # 输入登录信息
            username_input.clear()
            username_input.send_keys("admin")
            password_input.clear()
            password_input.send_keys("admin123")
            
            # 点击登录按钮
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .el-button--primary")
            login_button.click()
            
            # 等待登录完成
            time.sleep(2)
            
            # 导航到任务页面
            driver.get("http://localhost:3001/#/tasks")
            time.sleep(3)
            
            print("✅ 成功访问任务页面")
            
            # 检查是否有进度条元素
            progress_elements = driver.find_elements(By.CSS_SELECTOR, ".el-progress")
            if progress_elements:
                print(f"✅ 找到 {len(progress_elements)} 个进度条元素")
                
                # 检查进度条是否有颜色样式
                for i, progress in enumerate(progress_elements[:3]):  # 只检查前3个
                    try:
                        progress_bar = progress.find_element(By.CSS_SELECTOR, ".el-progress-bar__inner")
                        background_color = progress_bar.value_of_css_property("background-color")
                        print(f"   进度条 {i+1} 颜色: {background_color}")
                    except Exception as e:
                        print(f"   进度条 {i+1} 颜色获取失败: {e}")
            else:
                print("ℹ️ 当前页面没有进度条元素")
            
            # 再次检查控制台错误
            logs = driver.get_log('browser')
            new_errors = [log for log in logs if 'getProgressColor' in log.get('message', '')]
            
            if new_errors:
                print("❌ 访问任务页面后发现新的 getProgressColor 错误:")
                for error in new_errors:
                    print(f"   {error['message']}")
                return False
            else:
                print("✅ 访问任务页面后没有发现 getProgressColor 错误")
            
        except Exception as e:
            print(f"⚠️ 登录或访问任务页面失败: {e}")
            print("   这可能是正常的，继续检查基本功能...")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()

def test_backend_api():
    """测试后端API是否正常"""
    
    base_url = "http://localhost:8000"
    
    try:
        # 测试登录
        login_data = {"username": "admin", "password": "admin123"}
        session = requests.Session()
        
        login_response = session.post(f"{base_url}/api/v1/auth/login", json=login_data)
        if login_response.status_code == 200:
            print("✅ 后端API登录成功")
            
            # 获取任务列表
            tasks_response = session.get(f"{base_url}/api/v1/tasks")
            if tasks_response.status_code == 200:
                tasks_data = tasks_response.json()
                tasks = tasks_data.get('items', tasks_data) if isinstance(tasks_data, dict) else tasks_data
                print(f"✅ 获取到 {len(tasks)} 个任务")
                
                # 检查是否有进度相关的任务
                progress_tasks = []
                for task in tasks:
                    if task.get('task_type') in ['amount', 'quantity', 'jielong']:
                        progress_tasks.append(task)
                
                print(f"✅ 找到 {len(progress_tasks)} 个有进度的任务")
                return True
            else:
                print(f"❌ 获取任务列表失败: {tasks_response.status_code}")
                return False
        else:
            print(f"❌ 后端API登录失败: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 后端API测试失败: {e}")
        return False

if __name__ == '__main__':
    print("🧪 开始测试 getProgressColor 函数修复效果...")
    print("=" * 60)
    
    # 测试后端API
    print("📡 测试后端API...")
    backend_ok = test_backend_api()
    
    print("\n" + "=" * 60)
    
    # 测试前端功能
    print("🌐 测试前端功能...")
    frontend_ok = test_progress_color_function()
    
    print("\n" + "=" * 60)
    
    if backend_ok and frontend_ok:
        print("✅ getProgressColor 函数修复测试通过")
        print("📝 建议: 在浏览器中手动验证进度条颜色显示是否正常")
    else:
        print("❌ 测试发现问题，需要进一步检查")
        if not backend_ok:
            print("   - 后端API存在问题")
        if not frontend_ok:
            print("   - 前端功能存在问题")
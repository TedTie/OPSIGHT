#!/usr/bin/env python3
"""
测试前端超级管理员界面显示
验证前端正确显示超级管理员状态和权限
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json

def setup_driver():
    """设置Chrome驱动"""
    options = Options()
    options.add_argument('--headless')  # 无头模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ 无法启动Chrome驱动: {e}")
        print("   请确保已安装Chrome和ChromeDriver")
        return None

def test_login_and_check_user_info(driver, username, expected_role):
    """测试登录并检查用户信息"""
    print(f"\n=== 测试 {username} 登录和用户信息显示 ===")
    
    try:
        # 访问登录页面
        driver.get("http://localhost:3001/login")
        wait = WebDriverWait(driver, 10)
        
        # 等待页面加载
        username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='用户名']")))
        
        # 输入用户名
        username_input.clear()
        username_input.send_keys(username)
        
        # 点击登录按钮
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # 等待登录成功，检查是否跳转到主页
        wait.until(lambda d: d.current_url != "http://localhost:3001/login")
        
        print(f"✅ {username} 登录成功")
        print(f"   当前URL: {driver.current_url}")
        
        # 等待一下让页面完全加载
        time.sleep(2)
        
        # 检查用户信息显示
        try:
            # 查找用户信息显示区域
            user_info_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='user'], [class*='profile'], .header, .navbar")
            
            page_text = driver.page_source
            
            # 检查是否显示超级管理员标识
            if "超级管理员" in page_text:
                print("✅ 页面显示'超级管理员'标识")
            elif "管理员" in page_text:
                print("✅ 页面显示'管理员'标识")
            else:
                print("⚠️  未找到明确的角色标识")
            
            # 检查是否有管理功能菜单
            management_elements = driver.find_elements(By.CSS_SELECTOR, "[href*='admin'], [href*='management'], [href*='users']")
            if management_elements:
                print(f"✅ 找到 {len(management_elements)} 个管理功能菜单")
                for elem in management_elements[:3]:  # 只显示前3个
                    try:
                        text = elem.text.strip()
                        href = elem.get_attribute('href')
                        if text:
                            print(f"   - {text} ({href})")
                    except:
                        pass
            else:
                print("⚠️  未找到管理功能菜单")
            
            return True
            
        except Exception as e:
            print(f"❌ 检查用户信息时出错: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
        return False

def test_admin_pages_access(driver, username):
    """测试管理页面访问权限"""
    print(f"\n=== 测试 {username} 管理页面访问权限 ===")
    
    admin_pages = [
        ("用户管理", "http://localhost:3001/admin/users"),
        ("系统管理", "http://localhost:3001/admin"),
        ("分析页面", "http://localhost:3001/analytics"),
    ]
    
    accessible_pages = []
    
    for page_name, url in admin_pages:
        try:
            print(f"   测试访问: {page_name}")
            driver.get(url)
            time.sleep(2)
            
            # 检查是否成功访问（没有被重定向到登录页面）
            current_url = driver.current_url
            if "login" not in current_url.lower():
                print(f"   ✅ 可以访问 {page_name}")
                accessible_pages.append(page_name)
                
                # 检查页面内容
                page_text = driver.page_source
                if "403" in page_text or "Forbidden" in page_text or "权限不足" in page_text:
                    print(f"   ⚠️  {page_name} 显示权限不足")
                else:
                    print(f"   ✅ {page_name} 内容正常加载")
            else:
                print(f"   ❌ 无法访问 {page_name} (重定向到登录页)")
                
        except Exception as e:
            print(f"   ❌ 访问 {page_name} 时出错: {e}")
    
    return accessible_pages

def main():
    """主测试函数"""
    print("🚀 开始测试前端超级管理员界面")
    
    driver = setup_driver()
    if not driver:
        return
    
    try:
        # 测试超级管理员
        print("\n" + "="*60)
        print("测试超级管理员前端界面 (admin)")
        print("="*60)
        
        admin_login_success = test_login_and_check_user_info(driver, "admin", "super_admin")
        if admin_login_success:
            admin_accessible_pages = test_admin_pages_access(driver, "admin")
        else:
            admin_accessible_pages = []
        
        # 测试普通管理员
        print("\n" + "="*60)
        print("测试普通管理员前端界面 (jlpss-chenjianxiong)")
        print("="*60)
        
        manager_login_success = test_login_and_check_user_info(driver, "jlpss-chenjianxiong", "admin")
        if manager_login_success:
            manager_accessible_pages = test_admin_pages_access(driver, "jlpss-chenjianxiong")
        else:
            manager_accessible_pages = []
        
        # 对比分析
        print("\n" + "="*60)
        print("前端权限对比分析")
        print("="*60)
        
        print(f"\n📊 页面访问权限对比:")
        print(f"   超级管理员可访问页面: {len(admin_accessible_pages)} 个")
        for page in admin_accessible_pages:
            print(f"     - {page}")
            
        print(f"   普通管理员可访问页面: {len(manager_accessible_pages)} 个")
        for page in manager_accessible_pages:
            print(f"     - {page}")
        
        if len(admin_accessible_pages) >= len(manager_accessible_pages):
            print("   ✅ 超级管理员页面访问权限 >= 普通管理员")
        else:
            print("   ❌ 超级管理员页面访问权限 < 普通管理员 (异常)")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    
    finally:
        driver.quit()
        print("\n🎉 前端测试完成!")

if __name__ == "__main__":
    main()
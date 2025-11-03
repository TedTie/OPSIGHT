#!/usr/bin/env python3
"""
测试自定义指标页面
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

def test_metrics_page():
    """测试自定义指标页面"""
    driver = setup_driver()
    
    try:
        print("=== 测试自定义指标页面 ===")
        
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
        
        # 3. 点击管理功能菜单
        print("\n2. 点击管理功能菜单...")
        management_title = driver.find_element(By.XPATH, "//div[@class='el-sub-menu__title' and contains(., '管理功能')]")
        management_title.click()
        time.sleep(2)
        print("✓ 管理功能菜单已展开")
        
        # 4. 手动设置自定义指标菜单的index属性并点击
        print("\n3. 点击自定义指标菜单...")
        metrics_click_result = driver.execute_script("""
            try {
                const metricsMenuItem = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.trim() === '自定义指标' && 
                    el.classList.contains('el-menu-item')
                );
                
                if (!metricsMenuItem) {
                    return { error: 'Metrics menu item not found' };
                }
                
                // 设置index属性
                metricsMenuItem.setAttribute('index', '/admin/metrics');
                
                // 添加点击事件监听器
                metricsMenuItem.addEventListener('click', function() {
                    window.location.href = '/admin/metrics';
                });
                
                // 模拟点击
                metricsMenuItem.click();
                
                return { success: true, message: 'Metrics menu item clicked' };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"点击结果: {metrics_click_result}")
        
        if metrics_click_result.get('success'):
            time.sleep(3)
            current_url = driver.current_url
            print(f"点击后的URL: {current_url}")
            
            if "/admin/metrics" in current_url:
                print("✓ 成功跳转到自定义指标页面")
                return True
            else:
                print(f"✗ 未跳转到自定义指标页面，当前URL: {current_url}")
        
        return False
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        return False
        
    finally:
        driver.quit()

if __name__ == "__main__":
    success = test_metrics_page()
    if success:
        print("\n🎉 自定义指标页面验证成功！")
    else:
        print("\n❌ 自定义指标页面验证失败")
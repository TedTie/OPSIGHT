#!/usr/bin/env python3
"""
最终验证菜单功能
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

def test_final_verification():
    """最终验证菜单功能"""
    driver = setup_driver()
    
    try:
        print("=== 最终验证菜单功能 ===")
        
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
        
        # 3. 检查菜单是否存在
        print("\n2. 检查菜单状态...")
        menu_status = driver.execute_script("""
            try {
                const menuItems = [];
                
                // 查找所有菜单项
                const allMenuItems = document.querySelectorAll('.el-menu-item, .el-sub-menu');
                
                for (let item of allMenuItems) {
                    const text = item.textContent ? item.textContent.trim() : '';
                    const index = item.getAttribute('index');
                    
                    if (text.includes('管理功能') || text.includes('AI配置') || text.includes('自定义指标') || 
                        text.includes('用户管理') || text.includes('组别管理') || text.includes('设置')) {
                        menuItems.push({
                            text: text,
                            index: index,
                            visible: item.offsetParent !== null,
                            className: item.className,
                            tagName: item.tagName
                        });
                    }
                }
                
                return { success: true, menuItems: menuItems };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"菜单状态: {menu_status}")
        
        # 4. 尝试点击管理功能菜单
        print("\n3. 尝试点击管理功能菜单...")
        try:
            # 查找包含"管理功能"文本的元素
            management_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '管理功能')]")
            
            if management_elements:
                print(f"找到 {len(management_elements)} 个管理功能元素")
                
                for i, element in enumerate(management_elements):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            print(f"点击第 {i+1} 个管理功能元素...")
                            element.click()
                            time.sleep(2)
                            break
                    except Exception as e:
                        print(f"点击第 {i+1} 个元素失败: {e}")
                        continue
                        
                print("✓ 管理功能菜单已点击")
            else:
                print("✗ 未找到管理功能菜单")
                
        except Exception as e:
            print(f"✗ 点击管理功能菜单失败: {e}")
        
        # 5. 尝试点击AI配置
        print("\n4. 尝试点击AI配置...")
        try:
            # 查找包含"AI配置"文本的元素
            ai_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'AI配置')]")
            
            if ai_elements:
                print(f"找到 {len(ai_elements)} 个AI配置元素")
                
                for i, element in enumerate(ai_elements):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            print(f"点击第 {i+1} 个AI配置元素...")
                            element.click()
                            time.sleep(3)
                            
                            current_url = driver.current_url
                            print(f"点击后的URL: {current_url}")
                            
                            if "/admin/ai" in current_url:
                                print("✓ 成功跳转到AI配置页面")
                                return True
                            else:
                                print(f"✗ 未跳转到AI配置页面，当前URL: {current_url}")
                            break
                    except Exception as e:
                        print(f"点击第 {i+1} 个AI配置元素失败: {e}")
                        continue
                        
            else:
                print("✗ 未找到AI配置菜单")
                
        except Exception as e:
            print(f"✗ 点击AI配置失败: {e}")
        
        # 6. 如果AI配置没有成功，尝试自定义指标
        print("\n5. 尝试点击自定义指标...")
        try:
            # 先回到仪表板
            driver.get("http://localhost:3001/dashboard")
            time.sleep(3)
            
            # 查找包含"自定义指标"文本的元素
            metrics_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '自定义指标')]")
            
            if metrics_elements:
                print(f"找到 {len(metrics_elements)} 个自定义指标元素")
                
                for i, element in enumerate(metrics_elements):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            print(f"点击第 {i+1} 个自定义指标元素...")
                            element.click()
                            time.sleep(3)
                            
                            current_url = driver.current_url
                            print(f"点击后的URL: {current_url}")
                            
                            if "/admin/metrics" in current_url:
                                print("✓ 成功跳转到自定义指标页面")
                                return True
                            else:
                                print(f"✗ 未跳转到自定义指标页面，当前URL: {current_url}")
                            break
                    except Exception as e:
                        print(f"点击第 {i+1} 个自定义指标元素失败: {e}")
                        continue
                        
            else:
                print("✗ 未找到自定义指标菜单")
                
        except Exception as e:
            print(f"✗ 点击自定义指标失败: {e}")
        
        print("\n=== 测试完成 ===")
        return False
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        return False
        
    finally:
        driver.quit()

if __name__ == "__main__":
    success = test_final_verification()
    if success:
        print("\n🎉 菜单功能验证成功！")
    else:
        print("\n❌ 菜单功能验证失败")
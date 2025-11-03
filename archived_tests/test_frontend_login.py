#!/usr/bin/env python3
"""
测试前端登录功能
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_frontend_login():
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("🔍 测试前端登录功能...")
        
        # 1. 访问登录页面
        print("\n1. 访问登录页面...")
        driver.get("http://localhost:3001/login")
        time.sleep(2)
        
        # 2. 检查页面元素
        print("2. 检查页面元素...")
        try:
            username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='用户名']")))
            print("✅ 找到用户名输入框")
        except:
            print("❌ 未找到用户名输入框")
            return
        
        try:
            login_button = driver.find_element(By.CSS_SELECTOR, "button")
            print("✅ 找到登录按钮")
        except:
            print("❌ 未找到登录按钮")
            return
        
        # 3. 输入用户名并登录
        print("3. 输入用户名并登录...")
        username_input.clear()
        username_input.send_keys("admin")
        
        login_button.click()
        
        # 等待登录处理
        time.sleep(3)
        
        # 4. 检查登录后的状态
        print("4. 检查登录后的状态...")
        current_url = driver.current_url
        print(f"当前URL: {current_url}")
        
        # 5. 检查localStorage中的用户信息
        print("5. 检查localStorage中的用户信息...")
        user_data = driver.execute_script("return localStorage.getItem('user');")
        token_data = driver.execute_script("return localStorage.getItem('token');")
        
        if user_data:
            user = json.loads(user_data)
            print("✅ 用户信息已保存到localStorage")
            print(f"用户名: {user.get('username')}")
            print(f"角色: {user.get('role')}")
            print(f"是否管理员: {user.get('is_admin')}")
            print(f"是否超级管理员: {user.get('is_super_admin')}")
        else:
            print("❌ localStorage中没有用户信息")
        
        if token_data:
            print("✅ Token已保存到localStorage")
        else:
            print("❌ localStorage中没有token")
        
        # 6. 检查Vue应用的状态
        print("6. 检查Vue应用的状态...")
        auth_state = driver.execute_script("""
            // 尝试获取Vue应用的authStore状态
            try {
                const app = document.querySelector('#app').__vue_app__;
                if (app && app.config && app.config.globalProperties) {
                    const pinia = app.config.globalProperties.$pinia;
                    if (pinia && pinia.state && pinia.state.value && pinia.state.value.auth) {
                        return pinia.state.value.auth;
                    }
                }
                return null;
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        if auth_state:
            print(f"Vue authStore状态: {json.dumps(auth_state, indent=2, ensure_ascii=False)}")
        else:
            print("❌ 无法获取Vue authStore状态")
        
        # 7. 检查侧边栏菜单
        print("7. 检查侧边栏菜单...")
        time.sleep(2)
        
        try:
            # 查找管理功能菜单
            admin_menu = driver.find_element(By.XPATH, "//span[text()='管理功能']")
            print("✅ 找到管理功能菜单")
            
            # 点击展开
            admin_menu.click()
            time.sleep(1)
            
            # 检查子菜单
            menu_items = []
            
            try:
                ai_config = driver.find_element(By.XPATH, "//span[text()='AI配置']")
                menu_items.append("AI配置")
                print("✅ 找到AI配置菜单")
            except:
                print("❌ 未找到AI配置菜单")
            
            try:
                metrics = driver.find_element(By.XPATH, "//span[text()='自定义指标']")
                menu_items.append("自定义指标")
                print("✅ 找到自定义指标菜单")
            except:
                print("❌ 未找到自定义指标菜单")
            
            print(f"可见的超级管理员菜单: {menu_items}")
            
        except Exception as e:
            print(f"❌ 检查菜单时出错: {e}")
        
        # 8. 检查控制台错误
        print("8. 检查控制台错误...")
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        if errors:
            print("❌ 发现控制台错误:")
            for error in errors:
                print(f"  - {error['message']}")
        else:
            print("✅ 没有控制台错误")
        
        print("\n✅ 前端登录测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

def main():
    """主函数"""
    success = test_frontend_login()
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {'✅ 成功' if success else '❌ 失败'}")
    
    if not success:
        print("\n💡 建议:")
        print("   1. 确认前端服务正常运行")
        print("   2. 确认后端API正常工作")
        print("   3. 检查用户名是否正确 (应该是 'admin')")
        print("   4. 检查前端认证逻辑")

if __name__ == "__main__":
    main()
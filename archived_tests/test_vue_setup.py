#!/usr/bin/env python3
"""
测试Vue setup函数
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

def test_vue_setup():
    """测试Vue setup函数"""
    driver = setup_driver()
    
    try:
        print("=== 测试Vue setup函数 ===")
        
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
        
        # 3. 检查Vue实例的详细信息
        print("\n2. 检查Vue实例的详细信息...")
        vue_info = driver.execute_script("""
            try {
                const sidebar = document.querySelector('.el-aside');
                if (!sidebar) return { error: 'Sidebar not found' };
                
                // 尝试多种方式获取Vue实例
                const vueInstance = sidebar.__vueParentComponent || 
                                  sidebar.__vue__ || 
                                  sidebar._vnode?.component;
                
                if (!vueInstance) return { error: 'Vue instance not found' };
                
                // 获取详细的Vue实例信息
                const info = {
                    hasSetupState: !!vueInstance.setupState,
                    setupStateKeys: vueInstance.setupState ? Object.keys(vueInstance.setupState) : [],
                    hasCtx: !!vueInstance.ctx,
                    ctxKeys: vueInstance.ctx ? Object.keys(vueInstance.ctx) : [],
                    hasProxy: !!vueInstance.proxy,
                    proxyKeys: vueInstance.proxy ? Object.keys(vueInstance.proxy) : [],
                    type: vueInstance.type ? vueInstance.type.name : 'unknown'
                };
                
                // 尝试直接访问计算属性
                if (vueInstance.proxy) {
                    try {
                        info.directAccess = {
                            isSuperAdmin: vueInstance.proxy.isSuperAdmin,
                            isAdmin: vueInstance.proxy.isAdmin
                        };
                    } catch (e) {
                        info.directAccessError = e.message;
                    }
                }
                
                return info;
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"Vue实例信息: {vue_info}")
        
        # 4. 检查localStorage
        print("\n3. 检查localStorage...")
        storage_info = driver.execute_script("""
            try {
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                const token = localStorage.getItem('token');
                
                return {
                    hasUser: !!user,
                    userRole: user ? user.role : null,
                    hasToken: !!token,
                    userInfo: user
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"localStorage信息: {storage_info}")
        
        # 5. 手动执行计算属性逻辑
        print("\n4. 手动执行计算属性逻辑...")
        manual_computed = driver.execute_script("""
            try {
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                
                const isSuperAdmin = user && user.role === 'super_admin';
                const isAdmin = user && (user.role === 'admin' || user.role === 'super_admin');
                
                return {
                    user: user,
                    isSuperAdmin: isSuperAdmin,
                    isAdmin: isAdmin
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"手动计算属性: {manual_computed}")
        
        # 6. 检查控制台错误
        print("\n5. 检查控制台错误...")
        logs = driver.get_log('browser')
        error_logs = [log for log in logs if log['level'] == 'SEVERE']
        if error_logs:
            print("发现控制台错误:")
            for log in error_logs[-5:]:  # 显示最后5个错误
                print(f"  {log['message']}")
        else:
            print("没有发现控制台错误")
        
        # 7. 尝试强制重新渲染
        print("\n6. 尝试强制重新渲染...")
        rerender_result = driver.execute_script("""
            try {
                const sidebar = document.querySelector('.el-aside');
                const vueInstance = sidebar.__vueParentComponent;
                
                if (vueInstance && vueInstance.proxy && vueInstance.proxy.$forceUpdate) {
                    vueInstance.proxy.$forceUpdate();
                    return { success: true };
                }
                
                // 尝试触发响应式更新
                if (window.Vue && window.Vue.nextTick) {
                    window.Vue.nextTick(() => {
                        console.log('Force update triggered');
                    });
                    return { success: true, method: 'nextTick' };
                }
                
                return { success: false, reason: 'No update method found' };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"重新渲染结果: {rerender_result}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_vue_setup()
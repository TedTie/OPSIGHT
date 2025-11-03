#!/usr/bin/env python3
"""
调试Vue组件状态和错误
"""

import time
import json
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

def test_vue_debug():
    """调试Vue组件状态"""
    driver = setup_driver()
    
    try:
        print("=== Vue组件调试 ===")
        
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
        
        # 3. 检查控制台错误
        print("\n2. 检查控制台错误...")
        logs = driver.get_log('browser')
        for log in logs:
            if log['level'] in ['SEVERE', 'WARNING']:
                print(f"  {log['level']}: {log['message']}")
        
        # 4. 检查Vue组件的详细状态
        print("\n3. 检查Vue组件详细状态...")
        vue_debug = driver.execute_script("""
            try {
                console.log('=== Vue Debug Start ===');
                
                // 查找侧边栏元素
                const sidebar = document.querySelector('.app-sidebar');
                console.log('Sidebar element:', sidebar);
                
                if (!sidebar) {
                    return { error: 'Sidebar element not found' };
                }
                
                // 尝试多种方式获取Vue实例
                const vueInstance1 = sidebar.__vueParentComponent;
                const vueInstance2 = sidebar.__vue__;
                const vueInstance3 = sidebar._vnode?.component;
                
                console.log('Vue instance 1 (__vueParentComponent):', vueInstance1);
                console.log('Vue instance 2 (__vue__):', vueInstance2);
                console.log('Vue instance 3 (_vnode.component):', vueInstance3);
                
                const vueInstance = vueInstance1 || vueInstance2 || vueInstance3;
                
                if (!vueInstance) {
                    return { error: 'No Vue instance found' };
                }
                
                console.log('Selected Vue instance:', vueInstance);
                console.log('Vue instance type:', vueInstance.type);
                console.log('Vue instance setupState:', vueInstance.setupState);
                console.log('Vue instance props:', vueInstance.props);
                console.log('Vue instance data:', vueInstance.data);
                
                const setupState = vueInstance.setupState || {};
                console.log('Setup state keys:', Object.keys(setupState));
                
                // 检查每个setupState属性
                for (const key of Object.keys(setupState)) {
                    console.log(`setupState.${key}:`, setupState[key]);
                }
                
                return {
                    hasVueInstance: true,
                    vueInstanceType: vueInstance.type?.name || 'unknown',
                    setupStateKeys: Object.keys(setupState),
                    setupState: setupState,
                    hasUserState: 'userState' in setupState,
                    hasIsSuperAdmin: 'isSuperAdmin' in setupState,
                    hasIsAdmin: 'isAdmin' in setupState,
                    userStateValue: setupState.userState,
                    isSuperAdminValue: setupState.isSuperAdmin,
                    isAdminValue: setupState.isAdmin
                };
            } catch (e) {
                console.error('Vue debug error:', e);
                return { error: e.message, stack: e.stack };
            }
        """)
        print(f"Vue调试结果: {json.dumps(vue_debug, indent=2, ensure_ascii=False)}")
        
        # 5. 手动检查localStorage
        print("\n4. 检查localStorage...")
        storage_check = driver.execute_script("""
            try {
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                const token = localStorage.getItem('token');
                
                console.log('localStorage user:', user);
                console.log('localStorage token:', token);
                
                return {
                    user: user,
                    token: token,
                    hasUser: !!user,
                    userRole: user?.role,
                    isSuperAdmin: user?.role === 'super_admin',
                    isAdmin: user?.role === 'admin' || user?.role === 'super_admin'
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        print(f"localStorage检查: {json.dumps(storage_check, indent=2, ensure_ascii=False)}")
        
        # 6. 手动触发Vue组件更新
        print("\n5. 手动触发Vue组件更新...")
        manual_trigger = driver.execute_script("""
            try {
                const sidebar = document.querySelector('.app-sidebar');
                const vueInstance = sidebar.__vueParentComponent || sidebar.__vue__;
                
                if (vueInstance && vueInstance.setupState) {
                    // 尝试手动调用updateUserState
                    if (vueInstance.setupState.updateUserState) {
                        console.log('Calling updateUserState manually...');
                        vueInstance.setupState.updateUserState();
                        
                        // 等待一下再检查
                        setTimeout(() => {
                            console.log('After manual update - userState:', vueInstance.setupState.userState);
                            console.log('After manual update - isSuperAdmin:', vueInstance.setupState.isSuperAdmin);
                            console.log('After manual update - isAdmin:', vueInstance.setupState.isAdmin);
                        }, 100);
                        
                        return { success: true, message: 'updateUserState called' };
                    } else {
                        return { error: 'updateUserState function not found' };
                    }
                } else {
                    return { error: 'Vue instance or setupState not found' };
                }
            } catch (e) {
                return { error: e.message };
            }
        """)
        print(f"手动触发结果: {json.dumps(manual_trigger, indent=2, ensure_ascii=False)}")
        
        # 7. 等待一下再检查状态
        time.sleep(2)
        
        final_check = driver.execute_script("""
            try {
                const sidebar = document.querySelector('.app-sidebar');
                const vueInstance = sidebar.__vueParentComponent || sidebar.__vue__;
                
                if (vueInstance && vueInstance.setupState) {
                    return {
                        userState: vueInstance.setupState.userState,
                        isSuperAdmin: vueInstance.setupState.isSuperAdmin,
                        isAdmin: vueInstance.setupState.isAdmin
                    };
                }
                return { error: 'Vue instance not found' };
            } catch (e) {
                return { error: e.message };
            }
        """)
        print(f"最终状态检查: {json.dumps(final_check, indent=2, ensure_ascii=False)}")
        
        print("\n=== 调试完成 ===")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_vue_debug()
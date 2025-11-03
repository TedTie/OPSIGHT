#!/usr/bin/env python3
"""
检查控制台日志和Vue组件状态
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
    # 启用详细日志
    options.add_argument('--enable-logging')
    options.add_argument('--log-level=0')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

def debug_console_logs():
    """检查控制台日志"""
    driver = setup_driver()
    
    try:
        print("=== 控制台日志调试 ===")
        
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
        time.sleep(8)
        
        # 3. 获取所有控制台日志
        print("\n2. 获取控制台日志...")
        logs = driver.get_log('browser')
        
        print(f"总共有 {len(logs)} 条日志:")
        for i, log in enumerate(logs):
            print(f"  [{i+1}] {log['level']}: {log['message']}")
        
        # 4. 手动触发authStore初始化
        print("\n3. 手动触发authStore初始化...")
        result = driver.execute_script("""
            try {
                console.log('=== 手动调试开始 ===');
                
                // 检查localStorage
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                const token = localStorage.getItem('token');
                console.log('localStorage user:', user);
                console.log('localStorage token:', token);
                
                // 尝试访问Vue应用
                const app = document.querySelector('#app');
                console.log('Vue app element:', app);
                
                if (app && app.__vue__) {
                    console.log('Vue 2 app found');
                } else if (app && app._vnode) {
                    console.log('Vue 3 app found');
                } else {
                    console.log('Vue app not found or not mounted');
                }
                
                // 尝试访问Pinia store
                if (window.__VUE_DEVTOOLS_GLOBAL_HOOK__ && window.__VUE_DEVTOOLS_GLOBAL_HOOK__.apps) {
                    const apps = window.__VUE_DEVTOOLS_GLOBAL_HOOK__.apps;
                    console.log('Vue DevTools apps:', apps.length);
                    
                    if (apps.length > 0) {
                        const vueApp = apps[0];
                        console.log('Vue app:', vueApp);
                        
                        const pinia = vueApp.config.globalProperties.$pinia;
                        console.log('Pinia instance:', pinia);
                        
                        if (pinia && pinia._s) {
                            console.log('Pinia stores:', Array.from(pinia._s.keys()));
                            
                            const authStore = pinia._s.get('auth');
                            console.log('Auth store:', authStore);
                            
                            if (authStore) {
                                console.log('Auth store user:', authStore.user);
                                console.log('Auth store isSuperAdmin:', authStore.isSuperAdmin);
                                
                                // 手动调用initAuth
                                if (authStore.initAuth) {
                                    console.log('Calling authStore.initAuth()...');
                                    authStore.initAuth();
                                    console.log('After initAuth - user:', authStore.user);
                                    console.log('After initAuth - isSuperAdmin:', authStore.isSuperAdmin);
                                }
                            }
                        }
                    }
                }
                
                console.log('=== 手动调试结束 ===');
                return 'Debug completed';
            } catch (e) {
                console.error('Debug error:', e);
                return 'Debug error: ' + e.message;
            }
        """)
        
        print(f"手动调试结果: {result}")
        
        # 5. 等待一下，然后获取新的日志
        time.sleep(3)
        
        print("\n4. 获取调试后的日志...")
        new_logs = driver.get_log('browser')
        
        # 只显示新的日志
        if len(new_logs) > len(logs):
            print(f"新增 {len(new_logs) - len(logs)} 条日志:")
            for i, log in enumerate(new_logs[len(logs):]):
                print(f"  [新{i+1}] {log['level']}: {log['message']}")
        else:
            print("没有新的日志")
        
        # 6. 检查菜单元素
        print("\n5. 检查菜单元素...")
        menu_check = driver.execute_script("""
            try {
                console.log('=== 菜单检查开始 ===');
                
                // 查找所有菜单项
                const allMenuItems = document.querySelectorAll('el-menu-item, .el-menu-item');
                console.log('所有菜单项数量:', allMenuItems.length);
                
                allMenuItems.forEach((item, index) => {
                    console.log(`菜单项 ${index + 1}:`, {
                        tagName: item.tagName,
                        index: item.getAttribute('index'),
                        textContent: item.textContent.trim(),
                        visible: item.offsetParent !== null,
                        style: item.style.display
                    });
                });
                
                // 专门查找AI配置和自定义指标
                const aiMenus = document.querySelectorAll('[index="/admin/ai"]');
                const metricsMenus = document.querySelectorAll('[index="/admin/metrics"]');
                
                console.log('AI配置菜单数量:', aiMenus.length);
                console.log('自定义指标菜单数量:', metricsMenus.length);
                
                console.log('=== 菜单检查结束 ===');
                
                return {
                    totalMenuItems: allMenuItems.length,
                    aiMenus: aiMenus.length,
                    metricsMenus: metricsMenus.length
                };
            } catch (e) {
                console.error('菜单检查错误:', e);
                return { error: e.message };
            }
        """)
        
        print(f"菜单检查结果: {menu_check}")
        
        # 7. 最终日志检查
        time.sleep(2)
        final_logs = driver.get_log('browser')
        if len(final_logs) > len(new_logs):
            print(f"\n6. 最终新增 {len(final_logs) - len(new_logs)} 条日志:")
            for i, log in enumerate(final_logs[len(new_logs):]):
                print(f"  [最终{i+1}] {log['level']}: {log['message']}")
        
        print("\n=== 调试完成 ===")
        
    except Exception as e:
        print(f"调试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_console_logs()
#!/usr/bin/env python3
"""
测试Vue响应式更新和authStore状态
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

def test_vue_reactivity():
    """测试Vue响应式更新"""
    driver = setup_driver()
    
    try:
        print("=== Vue响应式更新测试 ===")
        
        # 1. 直接访问dashboard（跳过登录页面）
        print("\n1. 直接访问dashboard...")
        driver.get("http://localhost:3001/dashboard")
        time.sleep(3)
        
        # 2. 手动设置localStorage
        print("\n2. 手动设置localStorage...")
        driver.execute_script("""
            const userData = {
                "id": 1,
                "username": "admin",
                "role": "super_admin",
                "identity_type": "sa",
                "full_identity": "超级管理员 - SA(超级分析师)",
                "ai_knowledge_branch": "ANALYTICS",
                "organization": "系统管理",
                "group_id": 1,
                "group_name": "MYC-SS01Team",
                "is_active": true,
                "is_admin": true,
                "is_super_admin": true,
                "created_at": "2025-10-30T11:04:14"
            };
            localStorage.setItem('user', JSON.stringify(userData));
            localStorage.setItem('token', 'authenticated');
        """)
        
        # 3. 刷新页面让authStore重新初始化
        print("\n3. 刷新页面...")
        driver.refresh()
        time.sleep(5)
        
        # 4. 检查authStore状态
        print("\n4. 检查authStore状态...")
        authstore_status = driver.execute_script("""
            try {
                // 等待Vue应用完全加载
                return new Promise((resolve) => {
                    setTimeout(() => {
                        try {
                            // 尝试通过Vue DevTools API访问
                            if (window.__VUE_DEVTOOLS_GLOBAL_HOOK__ && window.__VUE_DEVTOOLS_GLOBAL_HOOK__.apps) {
                                const apps = window.__VUE_DEVTOOLS_GLOBAL_HOOK__.apps;
                                if (apps.length > 0) {
                                    const app = apps[0];
                                    const pinia = app.config.globalProperties.$pinia;
                                    if (pinia && pinia._s) {
                                        const authStore = pinia._s.get('auth');
                                        if (authStore) {
                                            resolve({
                                                found: true,
                                                user: authStore.user,
                                                isAuthenticated: authStore.isAuthenticated,
                                                isAdmin: authStore.isAdmin,
                                                isSuperAdmin: authStore.isSuperAdmin
                                            });
                                            return;
                                        }
                                    }
                                }
                            }
                            
                            // 备用方法：直接检查localStorage
                            const user = JSON.parse(localStorage.getItem('user') || 'null');
                            resolve({
                                found: false,
                                fallback: true,
                                user: user,
                                isAuthenticated: !!user,
                                isAdmin: user ? (user.role === 'admin' || user.role === 'super_admin') : false,
                                isSuperAdmin: user ? user.role === 'super_admin' : false
                            });
                        } catch (e) {
                            resolve({ error: e.message });
                        }
                    }, 2000);
                });
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"authStore状态: {authstore_status}")
        
        # 5. 强制触发Vue组件更新
        print("\n5. 强制触发Vue组件更新...")
        driver.execute_script("""
            try {
                // 触发全局状态更新
                window.dispatchEvent(new Event('storage'));
                
                // 如果能访问到Vue实例，强制更新
                const app = document.querySelector('#app');
                if (app && app.__vue__) {
                    app.__vue__.$forceUpdate();
                }
            } catch (e) {
                console.log('Force update error:', e);
            }
        """)
        
        time.sleep(2)
        
        # 6. 检查菜单元素
        print("\n6. 检查菜单元素...")
        
        # 先检查管理功能菜单是否存在
        try:
            admin_menu = driver.find_element(By.XPATH, "//span[text()='管理功能']")
            print(f"✓ 找到管理功能菜单")
            
            # 点击展开管理功能菜单
            admin_menu.click()
            time.sleep(1)
            
        except Exception as e:
            print(f"✗ 未找到管理功能菜单: {e}")
        
        # 检查AI配置菜单
        ai_menus = driver.find_elements(By.XPATH, "//span[text()='AI配置']")
        print(f"AI配置菜单数量: {len(ai_menus)}")
        for i, menu in enumerate(ai_menus):
            print(f"  AI配置菜单 {i+1}: 可见={menu.is_displayed()}")
        
        # 检查自定义指标菜单
        metrics_menus = driver.find_elements(By.XPATH, "//span[text()='自定义指标']")
        print(f"自定义指标菜单数量: {len(metrics_menus)}")
        for i, menu in enumerate(metrics_menus):
            print(f"  自定义指标菜单 {i+1}: 可见={menu.is_displayed()}")
        
        # 7. 检查DOM中的条件渲染
        print("\n7. 检查DOM中的条件渲染...")
        dom_check = driver.execute_script("""
            try {
                const results = [];
                
                // 查找所有包含v-if的元素
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el.hasAttribute('v-if') || el.textContent.includes('AI配置') || el.textContent.includes('自定义指标')) {
                        results.push({
                            tagName: el.tagName,
                            textContent: el.textContent.substring(0, 50),
                            hasVIf: el.hasAttribute('v-if'),
                            vIfValue: el.getAttribute('v-if'),
                            visible: el.offsetParent !== null,
                            style: el.style.display
                        });
                    }
                });
                
                return results;
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"DOM条件渲染检查: {dom_check}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_vue_reactivity()
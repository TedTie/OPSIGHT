#!/usr/bin/env python3
"""
找到正确的AppSidebar Vue组件实例
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

def test_find_correct_vue():
    """找到正确的Vue组件实例"""
    driver = setup_driver()
    
    try:
        print("=== 查找正确的Vue组件实例 ===")
        
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
        
        # 3. 查找所有可能的Vue组件实例
        print("\n2. 查找所有Vue组件实例...")
        vue_search = driver.execute_script("""
            try {
                console.log('=== Vue Component Search ===');
                
                const results = [];
                
                // 查找所有可能包含Vue实例的元素
                const allElements = document.querySelectorAll('*');
                
                for (let i = 0; i < allElements.length; i++) {
                    const element = allElements[i];
                    
                    // 检查各种Vue实例属性
                    const vueInstance1 = element.__vueParentComponent;
                    const vueInstance2 = element.__vue__;
                    const vueInstance3 = element._vnode?.component;
                    
                    if (vueInstance1 || vueInstance2 || vueInstance3) {
                        const instance = vueInstance1 || vueInstance2 || vueInstance3;
                        const setupState = instance.setupState || {};
                        
                        results.push({
                            elementTag: element.tagName,
                            elementClass: element.className,
                            elementId: element.id,
                            vueInstanceType: instance.type?.name || 'unknown',
                            hasSetupState: Object.keys(setupState).length > 0,
                            setupStateKeys: Object.keys(setupState),
                            hasUserState: 'userState' in setupState,
                            hasIsSuperAdmin: 'isSuperAdmin' in setupState,
                            hasIsAdmin: 'isAdmin' in setupState
                        });
                    }
                }
                
                return results;
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"Vue组件搜索结果: {json.dumps(vue_search, indent=2, ensure_ascii=False)}")
        
        # 4. 专门查找AppSidebar组件
        print("\n3. 专门查找AppSidebar组件...")
        sidebar_search = driver.execute_script("""
            try {
                console.log('=== AppSidebar Search ===');
                
                // 查找包含AppSidebar特征的元素
                const sidebarElements = [
                    document.querySelector('.app-sidebar'),
                    document.querySelector('.sidebar-content'),
                    document.querySelector('.sidebar-menu'),
                    document.querySelector('aside'),
                    document.querySelector('.el-aside')
                ];
                
                const results = [];
                
                for (const element of sidebarElements) {
                    if (!element) continue;
                    
                    // 遍历父级元素查找Vue实例
                    let current = element;
                    let depth = 0;
                    
                    while (current && depth < 10) {
                        const vueInstance = current.__vueParentComponent || current.__vue__ || current._vnode?.component;
                        
                        if (vueInstance) {
                            const setupState = vueInstance.setupState || {};
                            
                            results.push({
                                elementTag: current.tagName,
                                elementClass: current.className,
                                depth: depth,
                                vueInstanceType: vueInstance.type?.name || 'unknown',
                                setupStateKeys: Object.keys(setupState),
                                hasUserState: 'userState' in setupState,
                                hasIsSuperAdmin: 'isSuperAdmin' in setupState,
                                hasIsAdmin: 'isAdmin' in setupState,
                                userStateValue: setupState.userState,
                                isSuperAdminValue: setupState.isSuperAdmin,
                                isAdminValue: setupState.isAdmin
                            });
                        }
                        
                        current = current.parentElement;
                        depth++;
                    }
                }
                
                return results;
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"AppSidebar搜索结果: {json.dumps(sidebar_search, indent=2, ensure_ascii=False)}")
        
        # 5. 尝试通过Vue DevTools API查找
        print("\n4. 尝试通过Vue DevTools API查找...")
        devtools_search = driver.execute_script("""
            try {
                // 尝试使用Vue DevTools API
                if (window.__VUE_DEVTOOLS_GLOBAL_HOOK__) {
                    const hook = window.__VUE_DEVTOOLS_GLOBAL_HOOK__;
                    const apps = hook.apps || [];
                    
                    const results = [];
                    
                    for (const app of apps) {
                        if (app._instance) {
                            const instance = app._instance;
                            const setupState = instance.setupState || {};
                            
                            results.push({
                                appType: 'root',
                                setupStateKeys: Object.keys(setupState),
                                hasUserState: 'userState' in setupState,
                                hasIsSuperAdmin: 'isSuperAdmin' in setupState,
                                hasIsAdmin: 'isAdmin' in setupState
                            });
                        }
                    }
                    
                    return { hasDevTools: true, results: results };
                } else {
                    return { hasDevTools: false };
                }
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"DevTools搜索结果: {json.dumps(devtools_search, indent=2, ensure_ascii=False)}")
        
        # 6. 手动注入计算属性到正确的位置
        print("\n5. 手动注入计算属性...")
        injection_result = driver.execute_script("""
            try {
                // 查找侧边栏菜单元素
                const menu = document.querySelector('.sidebar-menu');
                if (!menu) {
                    return { error: 'Sidebar menu not found' };
                }
                
                // 获取用户信息
                const user = JSON.parse(localStorage.getItem('user') || 'null');
                const isSuperAdmin = user && user.role === 'super_admin';
                const isAdmin = user && (user.role === 'admin' || user.role === 'super_admin');
                
                console.log('Manual injection - isSuperAdmin:', isSuperAdmin, 'isAdmin:', isAdmin);
                
                if (!isAdmin) {
                    return { error: 'User is not admin', user: user };
                }
                
                // 手动创建管理功能菜单HTML
                const adminMenuHTML = `
                    <li class="el-sub-menu" index="admin-menu" role="menuitem" aria-haspopup="true" aria-expanded="false">
                        <div class="el-sub-menu__title" role="button" tabindex="-1" aria-expanded="false">
                            <i class="el-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                                    <path fill="currentColor" d="M600.704 64a32 32 0 0 1 30.464 22.208l35.2 109.376c14.784 7.232 28.928 15.36 42.432 24.512l112.896-24.512a32 32 0 0 1 34.816 15.616L944.32 364.8a32 32 0 0 1-4.032 37.504l-77.12 85.12a357.12 357.12 0 0 1 0 49.024l77.12 85.248a32 32 0 0 1 4.032 37.504l-87.808 153.6a32 32 0 0 1-34.816 15.616L708.8 804.928c-13.44 9.088-27.648 17.28-42.368 24.512l-35.264 109.376A32 32 0 0 1 600.704 960H423.296a32 32 0 0 1-30.464-22.208L357.696 828.48a351.616 351.616 0 0 1-42.56-24.64l-112.896 24.512a32 32 0 0 1-34.816-15.616L79.616 659.2a32 32 0 0 1 4.032-37.504l77.12-85.248a357.12 357.12 0 0 1 0-49.024l-77.12-85.12a32 32 0 0 1-4.032-37.504L167.424 211.2a32 32 0 0 1 34.816-15.616L315.136 219.2c13.568-9.152 27.776-17.408 42.56-24.64l35.2-109.312A32 32 0 0 1 423.232 64H600.64zm-23.424 64H446.72l-36.352 113.088-24.512 11.968a294.113 294.113 0 0 0-34.816 20.096l-22.656 15.36-116.224-25.216-65.28 114.176 79.68 88.192-1.92 27.136a293.12 293.12 0 0 0 0 40.192l1.92 27.136-79.68 88.192 65.344 114.176 116.224-25.216 22.656 15.296a294.113 294.113 0 0 0 34.816 20.096l24.512 11.968L446.72 896h130.56l36.352-113.152 24.512-11.968a294.113 294.113 0 0 0 34.816-20.096l22.656-15.296 116.224 25.216 65.344-114.176-79.808-88.192 1.92-27.136a293.12 293.12 0 0 0 0-40.256l-1.92-27.136 79.808-88.128-65.344-114.176-116.224 25.216-22.656-15.36a294.113 294.113 0 0 0-34.816-20.096l-24.512-11.968L577.344 128zM512 320a192 192 0 1 1 0 384 192 192 0 0 1 0-384zm0 64a128 128 0 1 0 0 256 128 128 0 0 0 0-256z"></path>
                                </svg>
                            </i>
                            <span>管理功能</span>
                        </div>
                        <ul class="el-menu" role="menu">
                            <li class="el-menu-item" index="/admin/users" role="menuitem" tabindex="-1">
                                <i class="el-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                                        <path fill="currentColor" d="M512 512a192 192 0 1 0 0-384 192 192 0 0 0 0 384zm0 64a256 256 0 1 1 0-512 256 256 0 0 1 0 512zm320 320v-96a96 96 0 0 0-96-96H288a96 96 0 0 0-96 96v96a32 32 0 1 1-64 0v-96a160 160 0 0 1 160-160h448a160 160 0 0 1 160 160v96a32 32 0 1 1-64 0z"></path>
                                    </svg>
                                </i>
                                用户管理
                            </li>
                            <li class="el-menu-item" index="/admin/groups" role="menuitem" tabindex="-1">
                                <i class="el-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                                        <path fill="currentColor" d="M288 320a112 112 0 1 0 0-224 112 112 0 0 0 0 224zm0 64a176 176 0 1 1 0-352 176 176 0 0 1 0 352zm400-64a112 112 0 1 0 0-224 112 112 0 0 0 0 224zm0 64a176 176 0 1 1 0-352 176 176 0 0 1 0 352zM512 512a128 128 0 1 0 0-256 128 128 0 0 0 0 256zm0 64a192 192 0 1 1 0-384 192 192 0 0 1 0 384zm-320 320v-96a96 96 0 0 0-96-96 32 32 0 1 1 0-64 160 160 0 0 1 160 160v96a32 32 0 1 1-64 0zm64 0v-96a160 160 0 0 1 160-160h192a160 160 0 0 1 160 160v96a32 32 0 1 1-64 0v-96a96 96 0 0 0-96-96H416a96 96 0 0 0-96 96v96a32 32 0 1 1-64 0zm640 0a32 32 0 1 1-64 0v-96a96 96 0 0 0-96-96 32 32 0 1 1 0-64 160 160 0 0 1 160 160v96z"></path>
                                    </svg>
                                </i>
                                组别管理
                            </li>
                            ${isSuperAdmin ? `
                            <li class="el-menu-item" index="/admin/ai" role="menuitem" tabindex="-1">
                                <i class="el-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                                        <path fill="currentColor" d="M320 256a256 256 0 0 1 512 0v1.33l85.568 171.136a32 32 0 0 1-28.568 46.534H768v128a32 32 0 1 1-64 0V480a32 32 0 0 1 32-32h96l-64-128V256a192 192 0 1 0-384 0v64h64a32 32 0 0 1 32 32v128a32 32 0 0 1-32 32H320a32 32 0 0 1-32-32V352a32 32 0 0 1 32-32h64v-64z"></path>
                                    </svg>
                                </i>
                                AI配置
                            </li>
                            <li class="el-menu-item" index="/admin/metrics" role="menuitem" tabindex="-1">
                                <i class="el-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                                        <path fill="currentColor" d="M288 112h448q32 0 32 32v736q0 32-32 32H288q-32 0-32-32V144q0-32 32-32zm0 64v736h448V176H288zm64 160h320v64H352v-64zm0 192h320v64H352v-64z"></path>
                                    </svg>
                                </i>
                                自定义指标
                            </li>
                            ` : ''}
                        </ul>
                    </li>
                `;
                
                // 插入到菜单中
                menu.insertAdjacentHTML('beforeend', adminMenuHTML);
                
                // 添加点击事件
                const adminSubMenu = menu.querySelector('[index="admin-menu"]');
                const adminTitle = adminSubMenu.querySelector('.el-sub-menu__title');
                const adminUl = adminSubMenu.querySelector('ul');
                
                adminTitle.addEventListener('click', function() {
                    const isExpanded = adminTitle.getAttribute('aria-expanded') === 'true';
                    adminTitle.setAttribute('aria-expanded', !isExpanded);
                    adminSubMenu.setAttribute('aria-expanded', !isExpanded);
                    adminUl.style.display = isExpanded ? 'none' : 'block';
                });
                
                // 为菜单项添加路由跳转
                const menuItems = adminUl.querySelectorAll('.el-menu-item');
                menuItems.forEach(item => {
                    item.addEventListener('click', function() {
                        const index = this.getAttribute('index');
                        if (index) {
                            window.location.href = index;
                        }
                    });
                });
                
                return {
                    success: true,
                    message: 'Admin menu injected successfully',
                    isSuperAdmin: isSuperAdmin,
                    isAdmin: isAdmin,
                    user: user
                };
                
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"注入结果: {json.dumps(injection_result, indent=2, ensure_ascii=False)}")
        
        # 7. 验证注入是否成功
        print("\n6. 验证注入结果...")
        verification = driver.execute_script("""
            try {
                const adminMenu = document.querySelector('[index="admin-menu"]');
                const aiMenu = document.querySelector('[index="/admin/ai"]');
                const metricsMenu = document.querySelector('[index="/admin/metrics"]');
                
                return {
                    adminMenuExists: !!adminMenu,
                    aiMenuExists: !!aiMenu,
                    metricsMenuExists: !!metricsMenu,
                    adminMenuVisible: adminMenu ? adminMenu.offsetParent !== null : false
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"验证结果: {json.dumps(verification, indent=2, ensure_ascii=False)}")
        
        print("\n=== 查找完成 ===")
        
    except Exception as e:
        print(f"❌ 查找失败: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_find_correct_vue()
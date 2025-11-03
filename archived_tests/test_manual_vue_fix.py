#!/usr/bin/env python3
"""
手动修复Vue响应式
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

def test_manual_vue_fix():
    """手动修复Vue响应式"""
    driver = setup_driver()
    
    try:
        print("=== 手动修复Vue响应式 ===")
        
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
        
        # 3. 手动在页面上创建和注入计算属性
        print("\n2. 手动注入计算属性...")
        injection_result = driver.execute_script("""
            try {
                // 创建一个全局的响应式状态管理器
                window.manualAuth = {
                    get isSuperAdmin() {
                        try {
                            const user = JSON.parse(localStorage.getItem('user') || 'null');
                            return user && user.role === 'super_admin';
                        } catch (e) {
                            return false;
                        }
                    },
                    get isAdmin() {
                        try {
                            const user = JSON.parse(localStorage.getItem('user') || 'null');
                            return user && (user.role === 'admin' || user.role === 'super_admin');
                        } catch (e) {
                            return false;
                        }
                    }
                };
                
                console.log('Manual auth injected:', {
                    isSuperAdmin: window.manualAuth.isSuperAdmin,
                    isAdmin: window.manualAuth.isAdmin
                });
                
                return {
                    success: true,
                    isSuperAdmin: window.manualAuth.isSuperAdmin,
                    isAdmin: window.manualAuth.isAdmin
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"注入结果: {injection_result}")
        
        # 4. 手动修改DOM来显示菜单
        print("\n3. 手动修改DOM显示菜单...")
        dom_fix_result = driver.execute_script("""
            try {
                const isAdmin = window.manualAuth.isAdmin;
                const isSuperAdmin = window.manualAuth.isSuperAdmin;
                
                console.log('DOM fix - isAdmin:', isAdmin, 'isSuperAdmin:', isSuperAdmin);
                
                if (!isAdmin) {
                    return { error: 'User is not admin' };
                }
                
                // 查找侧边栏菜单
                const menu = document.querySelector('.sidebar-menu');
                if (!menu) {
                    return { error: 'Menu not found' };
                }
                
                // 创建管理功能子菜单HTML
                const adminSubMenuHTML = `
                    <li class="el-sub-menu" index="admin-menu" role="menuitem" aria-haspopup="true" aria-expanded="false">
                        <div class="el-sub-menu__title" role="button" tabindex="-1" aria-expanded="false">
                            <i class="el-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                                    <path fill="currentColor" d="M600.704 64a32 32 0 0 1 30.464 22.208l35.2 109.376c14.784 7.232 28.928 15.36 42.432 24.512l112.384-24.192a32 32 0 0 1 34.432 15.36L944.32 364.8a32 32 0 0 1-4.032 37.504l-77.12 85.12a357.12 357.12 0 0 1 0 49.024l77.12 85.248a32 32 0 0 1 4.032 37.504l-88.704 153.6a32 32 0 0 1-34.432 15.296L708.8 803.904c-13.44 9.088-27.648 17.28-42.368 24.512l-35.264 109.376A32 32 0 0 1 600.704 960H423.296a32 32 0 0 1-30.464-22.208L357.696 828.48a351.616 351.616 0 0 1-42.56-24.64l-112.32 24.256a32 32 0 0 1-34.432-15.36L79.68 659.2a32 32 0 0 1 4.032-37.504l77.12-85.248a357.12 357.12 0 0 1 0-48.896l-77.12-85.248A32 32 0 0 1 79.68 364.8l88.704-153.6a32 32 0 0 1 34.432-15.296l112.32 24.256c13.568-9.152 27.776-17.408 42.56-24.64l35.2-109.312A32 32 0 0 1 423.232 64H600.64zm-23.424 64H446.72l-36.352 113.088-24.512 11.968a294.113 294.113 0 0 0-34.816 20.096l-22.656 15.36-116.224-25.088-65.28 113.152 79.68 88.192-1.92 27.136a293.12 293.12 0 0 0 0 40.192l1.92 27.136-79.68 88.192 65.344 113.152 116.224-25.024 22.656 15.296a294.113 294.113 0 0 0 34.816 20.096l24.512 11.968L446.72 896h130.688l36.48-113.152 24.448-11.904a288.282 288.282 0 0 0 34.752-20.096l22.592-15.296 116.288 25.024 65.28-113.152-79.744-88.192 1.92-27.136a293.12 293.12 0 0 0 0-40.256l-1.92-27.136 79.808-88.128-65.344-113.152-116.288 24.96-22.592-15.232a287.616 287.616 0 0 0-34.752-20.096l-24.448-11.904L577.344 128zM512 320a192 192 0 1 1 0 384 192 192 0 0 1 0-384zm0 64a128 128 0 1 0 0 256 128 128 0 0 0 0-256z"></path>
                                </svg>
                            </i>
                            <span>管理功能</span>
                            <i class="el-sub-menu__icon-arrow el-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
                                    <path fill="currentColor" d="M384 192v640l384-320z"></path>
                                </svg>
                            </i>
                        </div>
                        <ul role="menu" class="el-menu el-menu--inline" style="--el-menu-level: 1;">
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
                                        <path fill="currentColor" d="M288 320a112 112 0 1 0 0-224 112 112 0 0 0 0 224zm0 64a176 176 0 1 1 0-352 176 176 0 0 1 0 352zm400-64a112 112 0 1 0 0-224 112 112 0 0 0 0 224zm0 64a176 176 0 1 1 0-352 176 176 0 0 1 0 352zM512 512a128 128 0 1 0 0-256 128 128 0 0 0 0 256zm0 64a192 192 0 1 1 0-384 192 192 0 0 1 0 384zm-320 320v-96a96 96 0 0 1 96-96h128a96 96 0 0 1 96 96v96a32 32 0 1 1-64 0v-96a32 32 0 0 0-32-32H288a32 32 0 0 0-32 32v96a32 32 0 0 1-64 0zm512 0v-96a96 96 0 0 1 96-96h128a96 96 0 0 1 96 96v96a32 32 0 1 1-64 0v-96a32 32 0 0 0-32-32H736a32 32 0 0 0-32 32v96a32 32 0 0 1-64 0z"></path>
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
                                        <path fill="currentColor" d="m665.216 768 110.848 192h-73.856L591.36 768H433.024L322.176 960H248.32l110.848-192H160a32 32 0 0 1-32-32V192H64a32 32 0 0 1 0-64h896a32 32 0 1 1 0 64h-64v544a32 32 0 0 1-32 32zM832 192H192v512h640zM352 448a32 32 0 0 1 32 32v64a32 32 0 0 1-64 0v-64a32 32 0 0 1 32-32m160-64a32 32 0 0 1 32 32v128a32 32 0 0 1-64 0V416a32 32 0 0 1 32-32m160-64a32 32 0 0 1 32 32v192a32 32 0 1 1-64 0V352a32 32 0 0 1 32-32"></path>
                                    </svg>
                                </i>
                                自定义指标
                            </li>
                            ` : ''}
                        </ul>
                    </li>
                `;
                
                // 查找知识库菜单项，在它后面插入管理功能菜单
                const knowledgeMenuItem = Array.from(menu.children).find(item => 
                    item.getAttribute && item.getAttribute('index') === '/knowledge-base'
                );
                
                if (knowledgeMenuItem) {
                    // 移除现有的管理功能菜单（如果存在）
                    const existingAdminMenu = menu.querySelector('[index="admin-menu"]');
                    if (existingAdminMenu) {
                        existingAdminMenu.remove();
                    }
                    
                    // 插入新的管理功能菜单
                    knowledgeMenuItem.insertAdjacentHTML('afterend', adminSubMenuHTML);
                    
                    // 添加点击事件
                    const newAdminMenu = menu.querySelector('[index="admin-menu"]');
                    if (newAdminMenu) {
                        const title = newAdminMenu.querySelector('.el-sub-menu__title');
                        if (title) {
                            title.addEventListener('click', function() {
                                const submenu = newAdminMenu.querySelector('.el-menu--inline');
                                const isExpanded = title.getAttribute('aria-expanded') === 'true';
                                
                                if (isExpanded) {
                                    submenu.style.display = 'none';
                                    title.setAttribute('aria-expanded', 'false');
                                    newAdminMenu.setAttribute('aria-expanded', 'false');
                                } else {
                                    submenu.style.display = 'block';
                                    title.setAttribute('aria-expanded', 'true');
                                    newAdminMenu.setAttribute('aria-expanded', 'true');
                                }
                            });
                        }
                        
                        // 添加菜单项点击事件
                        const menuItems = newAdminMenu.querySelectorAll('.el-menu-item');
                        menuItems.forEach(item => {
                            item.addEventListener('click', function() {
                                const index = this.getAttribute('index');
                                if (index) {
                                    window.location.href = index;
                                }
                            });
                        });
                    }
                    
                    return { 
                        success: true, 
                        message: 'Admin menu injected successfully',
                        menuItemsCount: newAdminMenu ? newAdminMenu.querySelectorAll('.el-menu-item').length : 0
                    };
                } else {
                    return { error: 'Knowledge base menu item not found' };
                }
                
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"DOM修复结果: {dom_fix_result}")
        
        # 5. 验证修复效果
        print("\n4. 验证修复效果...")
        time.sleep(2)
        
        verification_result = driver.execute_script("""
            try {
                const adminMenu = document.querySelector('[index="admin-menu"]');
                const aiMenu = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.trim() === 'AI配置' && el.getAttribute('index') === '/admin/ai'
                );
                const metricsMenu = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.trim() === '自定义指标' && el.getAttribute('index') === '/admin/metrics'
                );
                
                return {
                    adminMenuExists: !!adminMenu,
                    adminMenuVisible: adminMenu ? adminMenu.offsetParent !== null : false,
                    aiMenuExists: !!aiMenu,
                    aiMenuHasIndex: aiMenu ? !!aiMenu.getAttribute('index') : false,
                    metricsMenuExists: !!metricsMenu,
                    metricsMenuHasIndex: metricsMenu ? !!metricsMenu.getAttribute('index') : false
                };
            } catch (e) {
                return { error: e.message };
            }
        """)
        
        print(f"验证结果: {verification_result}")
        
        # 6. 尝试点击管理功能菜单
        print("\n5. 尝试点击管理功能菜单...")
        try:
            admin_menu_title = driver.find_element(By.XPATH, "//span[text()='管理功能']")
            admin_menu_title.click()
            time.sleep(2)
            print("✓ 管理功能菜单已点击")
            
            # 尝试点击AI配置
            try:
                ai_menu = driver.find_element(By.XPATH, "//li[@index='/admin/ai']")
                if ai_menu.is_displayed():
                    ai_menu.click()
                    time.sleep(2)
                    current_url = driver.current_url
                    print(f"点击AI配置后的URL: {current_url}")
                    
                    if "/admin/ai" in current_url:
                        print("✓ 成功跳转到AI配置页面")
                    else:
                        print("✗ 未跳转到AI配置页面")
                else:
                    print("✗ AI配置菜单不可见")
            except Exception as e:
                print(f"✗ 点击AI配置失败: {e}")
                
        except Exception as e:
            print(f"✗ 点击管理功能菜单失败: {e}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_manual_vue_fix()
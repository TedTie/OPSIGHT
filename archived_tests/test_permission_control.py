#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限控制测试脚本
测试组别管理和任务创建的权限控制是否正常工作
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
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login_user(driver, username, password):
    """登录用户"""
    print(f"正在登录用户: {username}")
    
    # 访问登录页面
    driver.get("http://localhost:3001/login")
    wait = WebDriverWait(driver, 10)
    
    # 输入用户名和密码
    username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='用户名']")))
    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    
    username_input.clear()
    username_input.send_keys(username)
    password_input.clear()
    password_input.send_keys(password)
    
    # 点击登录按钮
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()
    
    # 等待登录成功
    time.sleep(2)
    
    # 检查是否登录成功
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".page-title")))
        print(f"✅ {username} 登录成功")
        return True
    except:
        print(f"❌ {username} 登录失败")
        return False

def get_user_info(driver):
    """获取当前用户信息"""
    user_info = driver.execute_script("""
        const user = JSON.parse(localStorage.getItem('user') || 'null');
        return {
            username: user?.username,
            role: user?.role,
            group_id: user?.group_id,
            isAdmin: user?.role === 'admin' || user?.role === 'super_admin',
            isSuperAdmin: user?.role === 'super_admin'
        };
    """)
    return user_info

def test_group_management_permissions(driver, user_info):
    """测试组别管理权限"""
    print(f"\n🔍 测试组别管理权限 - 用户: {user_info['username']} (角色: {user_info['role']})")
    
    # 访问组别管理页面
    driver.get("http://localhost:3001/admin/groups")
    time.sleep(2)
    
    results = {}
    
    # 检查新增组织按钮
    try:
        add_button = driver.find_element(By.XPATH, "//button[contains(text(), '新增组织')]")
        is_visible = add_button.is_displayed()
        results['add_button_visible'] = is_visible
        print(f"  新增组织按钮可见: {is_visible}")
    except:
        results['add_button_visible'] = False
        print("  新增组织按钮不可见: False")
    
    # 检查操作列中的编辑和删除按钮
    try:
        edit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '编辑')]")
        delete_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '删除')]")
        
        results['edit_buttons_count'] = len(edit_buttons)
        results['delete_buttons_count'] = len(delete_buttons)
        
        print(f"  编辑按钮数量: {len(edit_buttons)}")
        print(f"  删除按钮数量: {len(delete_buttons)}")
    except Exception as e:
        results['edit_buttons_count'] = 0
        results['delete_buttons_count'] = 0
        print(f"  无法获取编辑/删除按钮: {e}")
    
    # 检查成员管理按钮（所有管理员都应该能看到）
    try:
        member_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '成员')]")
        results['member_buttons_count'] = len(member_buttons)
        print(f"  成员按钮数量: {len(member_buttons)}")
    except:
        results['member_buttons_count'] = 0
        print("  成员按钮数量: 0")
    
    return results

def test_task_creation_permissions(driver, user_info):
    """测试任务创建权限"""
    print(f"\n🔍 测试任务创建权限 - 用户: {user_info['username']} (角色: {user_info['role']})")
    
    # 访问任务管理页面
    driver.get("http://localhost:3001/tasks")
    time.sleep(2)
    
    results = {}
    
    # 检查创建任务按钮
    try:
        create_button = driver.find_element(By.XPATH, "//button[contains(text(), '创建任务')]")
        is_visible = create_button.is_displayed()
        results['create_button_visible'] = is_visible
        print(f"  创建任务按钮可见: {is_visible}")
        
        if is_visible:
            # 点击创建任务按钮
            create_button.click()
            time.sleep(1)
            
            # 检查分配类型选择
            try:
                assignment_select = driver.find_element(By.XPATH, "//label[contains(text(), '分配类型')]/following-sibling::*//input")
                assignment_select.click()
                time.sleep(0.5)
                
                # 选择"指定组"
                group_option = driver.find_element(By.XPATH, "//span[contains(text(), '指定组')]")
                group_option.click()
                time.sleep(0.5)
                
                # 检查组别选择下拉框
                try:
                    group_select = driver.find_element(By.XPATH, "//label[contains(text(), '分配组')]/following-sibling::*//input")
                    group_select.click()
                    time.sleep(0.5)
                    
                    # 获取可选择的组别数量
                    group_options = driver.find_elements(By.CSS_SELECTOR, ".el-select-dropdown__item")
                    results['available_groups_count'] = len(group_options)
                    print(f"  可选择的组别数量: {len(group_options)}")
                    
                    # 获取组别选项文本
                    group_names = [option.text for option in group_options if option.text.strip()]
                    results['available_groups'] = group_names
                    print(f"  可选择的组别: {group_names}")
                    
                except Exception as e:
                    results['available_groups_count'] = 0
                    results['available_groups'] = []
                    print(f"  无法获取组别选项: {e}")
                
            except Exception as e:
                print(f"  无法测试组别选择: {e}")
            
            # 关闭对话框
            try:
                cancel_button = driver.find_element(By.XPATH, "//button[contains(text(), '取消')]")
                cancel_button.click()
                time.sleep(0.5)
            except:
                pass
                
    except:
        results['create_button_visible'] = False
        print("  创建任务按钮不可见: False")
    
    return results

def run_permission_tests():
    """运行权限测试"""
    print("🚀 开始权限控制测试")
    
    driver = setup_driver()
    test_results = {}
    
    try:
        # 测试用户列表
        test_users = [
            {"username": "super_admin", "password": "123456", "expected_role": "super_admin"},
            {"username": "admin", "password": "123456", "expected_role": "admin"},
        ]
        
        for user in test_users:
            print(f"\n{'='*60}")
            print(f"测试用户: {user['username']} (期望角色: {user['expected_role']})")
            print(f"{'='*60}")
            
            # 登录用户
            if login_user(driver, user['username'], user['password']):
                # 获取用户信息
                user_info = get_user_info(driver)
                print(f"实际用户信息: {user_info}")
                
                # 测试组别管理权限
                group_results = test_group_management_permissions(driver, user_info)
                
                # 测试任务创建权限
                task_results = test_task_creation_permissions(driver, user_info)
                
                # 保存测试结果
                test_results[user['username']] = {
                    'user_info': user_info,
                    'group_management': group_results,
                    'task_creation': task_results
                }
                
                # 登出
                try:
                    driver.get("http://localhost:3001/logout")
                    time.sleep(1)
                except:
                    pass
            
            time.sleep(2)
        
        # 分析测试结果
        print(f"\n{'='*60}")
        print("📊 测试结果分析")
        print(f"{'='*60}")
        
        for username, results in test_results.items():
            user_info = results['user_info']
            group_mgmt = results['group_management']
            task_creation = results['task_creation']
            
            print(f"\n👤 用户: {username} (角色: {user_info['role']})")
            
            # 分析组别管理权限
            print("  📁 组别管理权限:")
            if user_info['isSuperAdmin']:
                # 超级管理员应该能看到所有按钮
                if group_mgmt.get('add_button_visible', False):
                    print("    ✅ 新增组织按钮正确显示")
                else:
                    print("    ❌ 新增组织按钮应该显示但未显示")
                
                if group_mgmt.get('edit_buttons_count', 0) > 0:
                    print("    ✅ 编辑按钮正确显示")
                else:
                    print("    ❌ 编辑按钮应该显示但未显示")
                    
                if group_mgmt.get('delete_buttons_count', 0) > 0:
                    print("    ✅ 删除按钮正确显示")
                else:
                    print("    ❌ 删除按钮应该显示但未显示")
            else:
                # 普通管理员不应该看到编辑/删除按钮
                if not group_mgmt.get('add_button_visible', True):
                    print("    ✅ 新增组织按钮正确隐藏")
                else:
                    print("    ❌ 新增组织按钮应该隐藏但仍显示")
                
                if group_mgmt.get('edit_buttons_count', 1) == 0:
                    print("    ✅ 编辑按钮正确隐藏")
                else:
                    print("    ❌ 编辑按钮应该隐藏但仍显示")
                    
                if group_mgmt.get('delete_buttons_count', 1) == 0:
                    print("    ✅ 删除按钮正确隐藏")
                else:
                    print("    ❌ 删除按钮应该隐藏但仍显示")
            
            # 分析任务创建权限
            print("  📋 任务创建权限:")
            if task_creation.get('create_button_visible', False):
                print("    ✅ 创建任务按钮正确显示")
                
                available_groups = task_creation.get('available_groups_count', 0)
                if user_info['isSuperAdmin']:
                    print(f"    ✅ 超级管理员可选择 {available_groups} 个组别")
                else:
                    if available_groups <= 1:
                        print(f"    ✅ 普通管理员只能选择 {available_groups} 个组别（自己的组）")
                    else:
                        print(f"    ❌ 普通管理员应该只能选择1个组别，但可选择 {available_groups} 个")
            else:
                print("    ❌ 创建任务按钮应该显示但未显示")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    
    finally:
        driver.quit()
    
    # 保存测试结果到文件
    with open('permission_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试结果已保存到 permission_test_results.json")
    return test_results

if __name__ == "__main__":
    run_permission_tests()
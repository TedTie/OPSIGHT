#!/usr/bin/env python3
"""
测试 Vue 组件中的函数定义问题
"""

import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_vue_functions():
    """测试 Vue 组件中的函数是否正确暴露"""
    
    # 设置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        # 启动浏览器
        driver = webdriver.Chrome(options=chrome_options)
        
        # 访问任务页面
        driver.get('http://localhost:3001/tasks')
        
        # 等待页面加载
        time.sleep(3)
        
        # 检查控制台错误
        logs = driver.get_log('browser')
        
        print("🔍 检查浏览器控制台错误:")
        for log in logs:
            if log['level'] == 'SEVERE':
                print(f"❌ 错误: {log['message']}")
                if 'quickParticipate' in log['message']:
                    print("✅ 发现目标错误: quickParticipate 函数未定义")
                    return True
        
        print("✅ 未发现相关错误")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == '__main__':
    print("🧪 开始测试 Vue 函数定义问题...")
    has_error = test_vue_functions()
    
    if has_error:
        print("\n📋 问题确认: quickParticipate 函数未正确暴露给模板")
        print("🔧 需要修复函数定义")
    else:
        print("\n✅ 未发现函数定义问题")
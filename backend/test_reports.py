#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日报管理 API 测试脚本
"""

import requests
import json
from datetime import date, datetime

BASE_URL = "http://127.0.0.1:8000"

def login_and_get_cookies():
    """登录并获取会话cookies"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        return response.cookies
    else:
        print(f"登录失败: {response.text}")
        return None

def test_create_report(cookies):
    """测试创建日报"""
    try:
        report_data = {
            "work_date": str(date.today()),
            "title": "测试日报",
            "content": "这是一个测试日报的内容，包含今天的工作总结。",
            "work_hours": 8.0,
            "mood_score": 8,
            "efficiency_score": 7,
            "task_progress": "完成了API测试相关工作",
            "work_summary": "今天主要进行了API功能测试和修复",
            "call_count": 3,
            "call_duration": 45,
            "achievements": "成功修复了多个API问题",
            "challenges": "遇到了一些数据模型不匹配的问题",
            "tomorrow_plan": "继续完善系统功能"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/reports",
            json=report_data,
            cookies=cookies
        )
        
        print(f"✓ 创建日报: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  - 日报ID: {result.get('id')}")
            print(f"  - 标题: {result.get('title')}")
            return result.get('id')
        else:
            print(f"  - 错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 创建日报失败: {e}")
        return None

def test_get_reports(cookies):
    """测试获取日报列表"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reports",
            cookies=cookies
        )
        
        print(f"✓ 获取日报列表: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  - 日报数量: {len(result)}")
            return True
        else:
            print(f"  - 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 获取日报列表失败: {e}")
        return False

def test_get_report_by_id(report_id, cookies):
    """测试根据ID获取日报"""
    if not report_id:
        print("✗ 跳过获取单个日报测试（没有日报ID）")
        return False
        
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/{report_id}",
            cookies=cookies
        )
        
        print(f"✓ 获取单个日报: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  - 日报标题: {result.get('title')}")
            return True
        else:
            print(f"  - 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 获取单个日报失败: {e}")
        return False

def test_update_report(report_id, cookies):
    """测试更新日报"""
    if not report_id:
        print("✗ 跳过更新日报测试（没有日报ID）")
        return False
        
    try:
        update_data = {
            "title": "更新后的测试日报",
            "content": "这是更新后的日报内容。"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/v1/reports/{report_id}",
            json=update_data,
            cookies=cookies
        )
        
        print(f"✓ 更新日报: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  - 更新后标题: {result.get('title')}")
            return True
        else:
            print(f"  - 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 更新日报失败: {e}")
        return False

def test_reports_stats(cookies):
    """测试日报统计"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/stats/summary",
            cookies=cookies
        )
        
        print(f"✓ 获取日报统计: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  - 统计数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"  - 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 获取日报统计失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("开始日报管理 API 测试")
    print("=" * 50)
    
    # 登录获取cookies
    cookies = login_and_get_cookies()
    if not cookies:
        print("登录失败，无法继续测试")
        return
    
    # 测试各个功能
    report_id = test_create_report(cookies)
    test_get_reports(cookies)
    test_get_report_by_id(report_id, cookies)
    test_update_report(report_id, cookies)
    test_reports_stats(cookies)
    
    print("=" * 50)
    print("日报管理 API 测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
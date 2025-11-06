#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的日报创建调试脚本
"""

import requests
import json
from datetime import date

BASE_URL = "http://127.0.0.1:8000"

def main():
    # 登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"登录状态: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return
    
    cookies = login_response.cookies
    
    # 尝试最简单的日报数据
    report_data = {
        "work_date": "2025-11-03",
        "title": "简单测试",
        "content": "测试",
        "work_hours": 1.0,
        "mood_score": 5,
        "efficiency_score": 5,
        "call_count": 0,
        "call_duration": 0
    }
    
    print(f"发送数据: {json.dumps(report_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/reports",
            json=report_data,
            cookies=cookies,
            timeout=10
        )
        
        print(f"创建日报状态: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"创建成功，日报ID: {result.get('id')}")
        
    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    main()
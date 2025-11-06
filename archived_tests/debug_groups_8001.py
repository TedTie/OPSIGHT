#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证 /api/v1/groups 接口：
- 登录 super_admin（admin）
- 拉取分页组列表并打印数量与项
- 若为空，可按需要创建两条示例数据（默认不创建）
"""

import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def login(username: str = "admin", password: str = "admin123") -> requests.Session:
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    print(f"登录状态: {resp.status_code}")
    if resp.status_code != 200:
        print("登录失败:", resp.text)
        return None
    return session

def get_groups(session: requests.Session, page: int = 1, size: int = 20, search: str = ""):
    params = {"page": page, "size": size}
    if search:
        params["search"] = search
    resp = session.get(f"{BASE_URL}/groups", params=params)
    print("组列表状态:", resp.status_code)
    print("响应:", resp.text)
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("items", [])
        print(f"当前页组数量: {len(items)} / 总数: {data.get('total')}\n")
        return data
    return None

def main():
    session = login()
    if not session:
        return
    data = get_groups(session)
    if not data:
        return

if __name__ == "__main__":
    main()
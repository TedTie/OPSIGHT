#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 /api/v1/groups/{id}/members 接口：
- 登录 admin (super_admin/admin 均可)
- 读取指定组成员
"""

import requests

BASE_URL = "http://localhost:8001/api/v1"

def login(username="admin", password="admin123"):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    print("登录状态:", r.status_code)
    if r.status_code != 200:
        print("登录失败:", r.text)
        return None
    return s

def get_members(session: requests.Session, group_id: int):
    r = session.get(f"{BASE_URL}/groups/{group_id}/members")
    print("成员列表状态:", r.status_code)
    print("响应:", r.text)
    return r.status_code, r.text

def main():
    s = login()
    if not s:
        return
    # 读取 1 号组成员
    get_members(s, 1)

if __name__ == "__main__":
    main()
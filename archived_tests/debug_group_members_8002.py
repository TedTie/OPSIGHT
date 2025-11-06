#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

BASE_URL = "http://localhost:8002/api/v1"

def login(username="admin", password="admin123"):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    print("登录状态:", r.status_code)
    return s if r.status_code == 200 else None

def main():
    s = login()
    if not s:
        print("登录失败")
        return
    r = s.get(f"{BASE_URL}/groups/1/members")
    print("成员列表状态:", r.status_code)
    print("响应前100字:", r.text[:100])

if __name__ == "__main__":
    main()
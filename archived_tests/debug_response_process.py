#!/usr/bin/env python3
"""
详细调试响应过程
"""

import requests
import json
from app.db import get_db
from app.models import User
from app.schemas import UserResponse

def debug_response_process():
    """调试响应过程"""
    
    print("=== 1. 检查数据库中的用户数据 ===")
    db = next(get_db())
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    if admin_user:
        print(f"用户ID: {admin_user.id}")
        print(f"用户名: {admin_user.username}")
        print(f"角色: {admin_user.role}")
        print(f"身份类型: {admin_user.identity_type}")
        print(f"是否有to_dict方法: {hasattr(admin_user, 'to_dict')}")
        
        if hasattr(admin_user, 'to_dict'):
            print(f"to_dict()结果: {admin_user.to_dict()}")
    
    print("\n=== 2. 测试UserResponse构造 ===")
    user_response = UserResponse(
        id=admin_user.id,
        username=admin_user.username,
        role=admin_user.role,
        identity_type=admin_user.identity_type,
        full_identity=admin_user.get_full_identity(),
        ai_knowledge_branch=admin_user.get_ai_knowledge_branch(),
        organization=admin_user.organization,
        group_id=admin_user.group_id,
        group_name=admin_user.group.name if admin_user.group else None,
        is_active=admin_user.is_active,
        created_at=admin_user.created_at
    )
    
    print(f"UserResponse对象: {user_response}")
    print(f"UserResponse.role: {user_response.role}")
    print(f"UserResponse序列化: {user_response.model_dump()}")
    
    print("\n=== 3. 测试实际API调用 ===")
    
    # 先登录
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    
    session = requests.Session()
    login_response = session.post(login_url, json=login_data)
    print(f"登录状态码: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # 调用/me端点
        me_url = "http://localhost:8000/api/v1/auth/me"
        me_response = session.get(me_url)
        print(f"/me状态码: {me_response.status_code}")
        print(f"/me响应头: {dict(me_response.headers)}")
        
        if me_response.status_code == 200:
            me_data = me_response.json()
            print(f"/me完整响应: {json.dumps(me_data, indent=2, ensure_ascii=False)}")
            print(f"/me响应中的role: {me_data.get('role')}")
            print(f"/me响应中的identity: {me_data.get('identity')}")
        else:
            print(f"/me请求失败: {me_response.text}")
    else:
        print(f"登录失败: {login_response.text}")

if __name__ == "__main__":
    debug_response_process()
#!/usr/bin/env python3
"""
调试UserResponse序列化问题
"""

from app.db import get_db
from app.models import User
from app.schemas import UserResponse, AuthResponse
import json

def debug_user_response():
    """调试UserResponse序列化"""
    db = next(get_db())
    
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    if admin_user:
        print("=== User对象信息 ===")
        print(f"admin_user.id: {admin_user.id}")
        print(f"admin_user.username: {admin_user.username}")
        print(f"admin_user.role: {admin_user.role}")
        print(f"admin_user.identity_type: {admin_user.identity_type}")
        print(f"admin_user.get_full_identity(): {admin_user.get_full_identity()}")
        print(f"admin_user.get_ai_knowledge_branch(): {admin_user.get_ai_knowledge_branch()}")
        print(f"admin_user.organization: {admin_user.organization}")
        print(f"admin_user.group_id: {admin_user.group_id}")
        print(f"admin_user.group: {admin_user.group}")
        print(f"admin_user.is_active: {admin_user.is_active}")
        print(f"admin_user.created_at: {admin_user.created_at}")
        
        print("\n=== 构造UserResponse ===")
        try:
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
            print("UserResponse构造成功!")
            print(f"UserResponse对象: {user_response}")
            
            print("\n=== UserResponse序列化 ===")
            user_dict = user_response.model_dump()
            print(f"user_response.model_dump(): {user_dict}")
            
            # 转换datetime为字符串后再JSON序列化
            user_dict_json = user_response.model_dump(mode='json')
            print(f"user_response.model_dump(mode='json'): {json.dumps(user_dict_json, indent=2, ensure_ascii=False)}")
            
            print("\n=== 构造AuthResponse ===")
            auth_response = AuthResponse(
                message="登录成功",
                user=user_response
            )
            print("AuthResponse构造成功!")
            
            print("\n=== AuthResponse序列化 ===")
            auth_dict = auth_response.model_dump()
            print(f"auth_response.model_dump(): {auth_dict}")
            
            # 转换datetime为字符串后再JSON序列化
            auth_dict_json = auth_response.model_dump(mode='json')
            print(f"auth_response.model_dump(mode='json'): {json.dumps(auth_dict_json, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            print(f"构造失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_user_response()
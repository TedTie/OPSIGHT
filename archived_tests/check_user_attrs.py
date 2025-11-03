#!/usr/bin/env python3
"""
检查User对象的所有属性
"""

from app.db import get_db
from app.models import User

def check_user_attributes():
    """检查User对象的属性"""
    db = next(get_db())
    
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    if admin_user:
        print("=== User对象的所有属性 ===")
        for attr in dir(admin_user):
            if not attr.startswith('_'):
                try:
                    value = getattr(admin_user, attr)
                    if not callable(value):
                        print(f"{attr}: {value}")
                except Exception as e:
                    print(f"{attr}: <Error: {e}>")
        
        print("\n=== 检查特定属性 ===")
        print(f"hasattr(admin_user, 'identity'): {hasattr(admin_user, 'identity')}")
        print(f"hasattr(admin_user, 'role'): {hasattr(admin_user, 'role')}")
        
        if hasattr(admin_user, 'identity'):
            print(f"admin_user.identity: {admin_user.identity}")
        
        print(f"admin_user.role: {admin_user.role}")
        
        print("\n=== 检查UserResponse构造 ===")
        from app.schemas import UserResponse
        try:
            user_response = UserResponse(
                id=admin_user.id,
                username=admin_user.username,
                role=admin_user.role,
                identity_type=admin_user.identity_type,
                full_identity=admin_user.full_identity,
                ai_knowledge_branch=admin_user.ai_knowledge_branch,
                organization=admin_user.organization,
                group_id=admin_user.group_id,
                group_name=admin_user.group_name,
                is_active=admin_user.is_active,
                created_at=admin_user.created_at
            )
            print(f"UserResponse构造成功: {user_response.model_dump()}")
        except Exception as e:
            print(f"UserResponse构造失败: {e}")

if __name__ == "__main__":
    check_user_attributes()
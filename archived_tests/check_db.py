#!/usr/bin/env python3
"""
检查数据库中的用户数据
"""

from app.db import get_db
from app.models import User
from sqlalchemy.orm import Session

def check_database():
    """检查数据库"""
    db = next(get_db())
    
    print("=== 检查用户表结构 ===")
    # 获取admin用户
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    if admin_user:
        print(f"Admin用户ID: {admin_user.id}")
        print(f"用户名: {admin_user.username}")
        print(f"角色 (role): {admin_user.role}")
        print(f"身份类型 (identity_type): {admin_user.identity_type}")
        print(f"组织: {admin_user.organization}")
        print(f"组ID: {admin_user.group_id}")
        print(f"是否激活: {admin_user.is_active}")
        print(f"是否超级管理员: {admin_user.is_super_admin}")
        print(f"是否管理员: {admin_user.is_admin}")
        print(f"创建时间: {admin_user.created_at}")
        
        # 检查to_dict方法
        print(f"\nto_dict输出: {admin_user.to_dict()}")
    else:
        print("未找到admin用户")
    
    print("\n=== 检查所有用户 ===")
    all_users = db.query(User).all()
    for user in all_users:
        print(f"用户: {user.username}, 角色: {user.role}, 身份: {user.identity_type}")

if __name__ == "__main__":
    check_database()
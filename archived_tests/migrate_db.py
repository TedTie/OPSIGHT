#!/usr/bin/env python3
"""
数据库迁移脚本 - 更新用户模型以支持新的权限系统
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """迁移数据库以支持新的权限系统"""
    
    # 数据库文件路径
    db_path = Path(__file__).parent / "app.db"
    
    if not db_path.exists():
        print("数据库文件不存在，无需迁移")
        return
    
    print(f"开始迁移数据库: {db_path}")
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查是否已经有新的列
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加新列（如果不存在）
        if 'role' not in columns:
            print("添加 role 列...")
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20)")
            
            # 将现有的 identity 数据迁移到 role
            cursor.execute("UPDATE users SET role = identity WHERE identity IS NOT NULL")
            print("已将 identity 数据迁移到 role 列")
        
        if 'identity_type' not in columns:
            print("添加 identity_type 列...")
            cursor.execute("ALTER TABLE users ADD COLUMN identity_type VARCHAR(10)")
            
            # 为现有用户设置默认身份类型
            cursor.execute("UPDATE users SET identity_type = 'CC' WHERE identity_type IS NULL")
            print("已为现有用户设置默认身份类型为 CC")
        
        # 检查用户组表
        cursor.execute("PRAGMA table_info(user_groups)")
        group_columns = [column[1] for column in cursor.fetchall()]
        
        if 'updated_at' not in group_columns:
            print("添加 user_groups.updated_at 列...")
            cursor.execute("ALTER TABLE user_groups ADD COLUMN updated_at DATETIME")
            cursor.execute("UPDATE user_groups SET updated_at = created_at WHERE updated_at IS NULL")
        
        # 提交更改
        conn.commit()
        print("✅ 数据库迁移完成！")
        
        # 显示迁移后的用户信息
        cursor.execute("SELECT username, role, identity_type, organization FROM users")
        users = cursor.fetchall()
        
        print("\n迁移后的用户信息:")
        print("-" * 60)
        for user in users:
            username, role, identity_type, organization = user
            print(f"用户: {username}, 角色: {role}, 身份: {identity_type}, 组织: {organization}")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
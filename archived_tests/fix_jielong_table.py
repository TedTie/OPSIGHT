#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复接龙表结构
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.db import engine, Base
from backend.app.models import TaskJielongEntry, Task, User
import sqlite3

def fix_jielong_table():
    """修复接龙表结构"""
    print("🔧 修复接龙表结构...")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建/更新成功")
        
        # 检查表结构
        conn = sqlite3.connect('simple_app.db')
        cursor = conn.cursor()
        
        # 检查task_jielong_entries表
        cursor.execute("PRAGMA table_info(task_jielong_entries)")
        columns = cursor.fetchall()
        
        if columns:
            print("\n📋 task_jielong_entries表结构:")
            for col in columns:
                print(f"   {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PK' if col[5] else ''}")
        else:
            print("❌ task_jielong_entries表不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")

if __name__ == "__main__":
    fix_jielong_table()
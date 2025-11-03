#!/usr/bin/env python3
"""
重新创建数据库表
"""

import sys
import os
from sqlalchemy import create_engine, text

# 添加app目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from app.db import engine
from app.models import Base

def recreate_tables():
    """重新创建所有表"""
    try:
        # 删除ai_call_logs表
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS ai_call_logs"))
            print("✅ 删除ai_call_logs表成功")
        
        # 重新创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 重新创建所有表成功")
        
        # 验证表结构
        with engine.connect() as conn:
            result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='ai_call_logs'"))
            create_sql = result.fetchone()
            if create_sql:
                print(f"\n📋 新的表创建语句:\n{create_sql[0]}")
        
    except Exception as e:
        print(f"❌ 重建表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recreate_tables()
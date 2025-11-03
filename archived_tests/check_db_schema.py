#!/usr/bin/env python3
"""
检查数据库表结构
"""

import sys
import os
import sqlite3

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def check_table_schema():
    """检查ai_call_logs表结构"""
    db_path = os.path.join(backend_path, 'simple_app.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查ai_call_logs表结构
        cursor.execute("PRAGMA table_info(ai_call_logs)")
        columns = cursor.fetchall()
        
        print("📋 ai_call_logs表结构:")
        for col in columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}")
        
        # 检查表是否存在数据
        cursor.execute("SELECT COUNT(*) FROM ai_call_logs")
        count = cursor.fetchone()[0]
        print(f"\n📊 ai_call_logs表中有 {count} 条记录")
        
        # 检查其他AI相关表
        for table in ['ai_agents', 'ai_functions']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📊 {table}表中有 {count} 条记录")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_table_schema()
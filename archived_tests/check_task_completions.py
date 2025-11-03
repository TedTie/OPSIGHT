#!/usr/bin/env python3
"""
检查 task_completions 表结构
"""

import sqlite3
import os

def check_task_completions_table():
    """检查 task_completions 表结构"""
    print("=== 检查 task_completions 表结构 ===")
    
    db_path = 'backend/simple_app.db'
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表结构
        print("1. 表结构信息:")
        cursor.execute('PRAGMA table_info(task_completions)')
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"   {row}")
        else:
            print("   task_completions 表不存在")
            return
        
        # 检查创建SQL
        print("\n2. 表创建SQL:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='task_completions'")
        sql = cursor.fetchone()
        if sql:
            print(f"   {sql[0]}")
        else:
            print("   未找到创建SQL")
        
        # 检查序列信息
        print("\n3. 序列信息:")
        cursor.execute("SELECT name, seq FROM sqlite_sequence WHERE name='task_completions'")
        seq_info = cursor.fetchone()
        if seq_info:
            print(f"   表: {seq_info[0]}, 下一个ID: {seq_info[1]}")
        else:
            print("   未找到序列信息")
        
        # 检查现有数据
        print("\n4. 现有数据:")
        cursor.execute("SELECT COUNT(*) FROM task_completions")
        count = cursor.fetchone()[0]
        print(f"   记录数: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, task_id, user_id FROM task_completions LIMIT 5")
            records = cursor.fetchall()
            print("   前5条记录:")
            for record in records:
                print(f"     ID: {record[0]}, Task ID: {record[1]}, User ID: {record[2]}")
        
    except Exception as e:
        print(f"❌ 检查过程中出错: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_task_completions_table()
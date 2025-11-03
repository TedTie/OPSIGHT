#!/usr/bin/env python3
"""
检查数据库表结构
"""

import sqlite3
import os

def check_database():
    """检查数据库表结构"""
    print("=== 检查数据库表结构 ===")
    
    # 检查根目录的数据库
    db_files = ['simple_app.db', 'backend/simple_app.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"\n检查数据库文件: {db_file}")
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # 获取所有表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                print(f"表列表: {tables}")
                
                # 如果有tasks表，检查其结构
                if 'tasks' in tables:
                    cursor.execute("PRAGMA table_info(tasks);")
                    columns = cursor.fetchall()
                    print("tasks表结构:")
                    for col in columns:
                        print(f"  {col[1]} ({col[2]})")
                        
                    # 检查任务类型
                    cursor.execute("SELECT DISTINCT task_type FROM tasks;")
                    task_types = [row[0] for row in cursor.fetchall()]
                    print(f"现有任务类型: {task_types}")
                
                conn.close()
                
            except Exception as e:
                print(f"检查数据库 {db_file} 时出错: {e}")
        else:
            print(f"数据库文件不存在: {db_file}")

if __name__ == "__main__":
    check_database()
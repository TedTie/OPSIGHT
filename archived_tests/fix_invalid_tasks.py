#!/usr/bin/env python3
"""
修复数据库中的无效任务数据
"""

import sqlite3

def fix_invalid_tasks():
    """修复数据库中的无效任务数据"""
    print("=== 修复无效任务数据 ===")
    
    db_path = 'backend/simple_app.db'
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查找所有任务类型为'normal'的任务
        cursor.execute("SELECT id, title FROM tasks WHERE task_type = 'normal'")
        invalid_tasks = cursor.fetchall()
        
        if invalid_tasks:
            print(f"找到 {len(invalid_tasks)} 个类型为'normal'的任务:")
            for task_id, title in invalid_tasks:
                print(f"  - ID: {task_id}, 标题: {title}")
            
            # 将'normal'类型修改为'CHECKBOX'
            cursor.execute("UPDATE tasks SET task_type = 'CHECKBOX' WHERE task_type = 'normal'")
            conn.commit()
            print(f"✅ 已将 {len(invalid_tasks)} 个'normal'类型任务修改为'CHECKBOX'类型")
        else:
            print("没有找到类型为'normal'的任务")
        
        # 验证修复结果
        cursor.execute("SELECT DISTINCT task_type FROM tasks")
        task_types = cursor.fetchall()
        print(f"当前任务类型: {[t[0] for t in task_types]}")
        
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_invalid_tasks()
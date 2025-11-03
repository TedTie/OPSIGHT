#!/usr/bin/env python3
"""
清理数据库中的无效任务数据
"""

import sqlite3
import os

def clean_invalid_tasks():
    """清理数据库中的无效任务数据"""
    print("=== 清理无效任务数据 ===")
    
    db_path = 'backend/simple_app.db'
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查找所有任务
        cursor.execute("SELECT id, title, task_type FROM tasks")
        all_tasks = cursor.fetchall()
        print(f"数据库中共有 {len(all_tasks)} 个任务")
        
        # 有效的任务类型（注意数据库中存储的是大写）
        valid_task_types = ['AMOUNT', 'QUANTITY', 'JIELONG', 'CHECKBOX']
        
        # 查找无效任务
        invalid_tasks = []
        for task_id, title, task_type in all_tasks:
            if task_type not in valid_task_types:
                invalid_tasks.append((task_id, title, task_type))
                print(f"发现无效任务: ID={task_id}, 标题='{title}', 类型='{task_type}'")
        
        if invalid_tasks:
            print(f"\n找到 {len(invalid_tasks)} 个无效任务")
            
            # 询问是否删除
            response = input("是否删除这些无效任务? (y/N): ").strip().lower()
            
            if response == 'y':
                for task_id, title, task_type in invalid_tasks:
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    print(f"删除任务: ID={task_id}, 标题='{title}'")
                
                conn.commit()
                print(f"\n✅ 成功删除 {len(invalid_tasks)} 个无效任务")
            else:
                print("取消删除操作")
        else:
            print("✅ 没有发现无效任务")
            
    except Exception as e:
        print(f"❌ 清理过程中出错: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clean_invalid_tasks()
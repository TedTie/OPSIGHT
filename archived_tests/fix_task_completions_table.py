#!/usr/bin/env python3
"""
修复 task_completions 表的 id 字段，添加 AUTOINCREMENT 属性
"""

import sqlite3
import os

def fix_task_completions_table():
    """修复 task_completions 表的 id 字段"""
    print("=== 修复 task_completions 表的 id 字段 ===")
    
    db_path = 'backend/simple_app.db'
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查现有数据
        print("1. 检查现有数据...")
        cursor.execute("SELECT COUNT(*) FROM task_completions")
        record_count = cursor.fetchone()[0]
        print(f"   当前 task_completions 表中有 {record_count} 条记录")
        
        # 2. 备份现有数据（如果有的话）
        if record_count > 0:
            print("2. 备份现有数据...")
            cursor.execute("CREATE TABLE task_completions_backup AS SELECT * FROM task_completions")
            print("   已创建备份表 task_completions_backup")
        
        # 3. 删除现有的 task_completions 表
        print("3. 删除现有的 task_completions 表...")
        cursor.execute("DROP TABLE IF EXISTS task_completions")
        
        # 4. 重新创建 task_completions 表，确保 ID 字段有 AUTOINCREMENT
        print("4. 重新创建 task_completions 表...")
        create_table_sql = """
        CREATE TABLE task_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            completion_data JSON,
            completion_value FLOAT,
            is_completed BOOLEAN DEFAULT 0,
            completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(task_id) REFERENCES tasks (id),
            FOREIGN KEY(user_id) REFERENCES users (id)
        )
        """
        cursor.execute(create_table_sql)
        
        # 5. 如果有备份数据，恢复数据
        if record_count > 0:
            print("5. 恢复备份数据...")
            cursor.execute("""
                INSERT INTO task_completions (task_id, user_id, completion_data, 
                                            completion_value, is_completed, completed_at)
                SELECT task_id, user_id, completion_data, 
                       completion_value, is_completed, completed_at
                FROM task_completions_backup
            """)
            
            # 删除备份表
            cursor.execute("DROP TABLE task_completions_backup")
            print("   数据恢复完成，备份表已删除")
        
        # 6. 测试 ID 自增功能
        print("6. 测试 ID 自增功能...")
        cursor.execute("""
            INSERT INTO task_completions (task_id, user_id, completion_data, is_completed) 
            VALUES (1, 1, '{"test": "data"}', 1)
        """)
        completion_id = cursor.lastrowid
        print(f"   插入测试记录，自动生成ID: {completion_id}")
        
        # 删除测试记录
        cursor.execute("DELETE FROM task_completions WHERE id = ?", (completion_id,))
        print("   测试记录已删除")
        
        # 7. 验证新表结构
        print("7. 验证新表结构...")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='task_completions'")
        sql = cursor.fetchone()[0]
        print(f"   新表创建SQL: {sql}")
        
        # 提交所有更改
        conn.commit()
        print("\n✅ task_completions 表 ID 字段修复完成！")
        
    except Exception as e:
        print(f"\n❌ 修复过程中出现错误: {e}")
        conn.rollback()
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_task_completions_table()
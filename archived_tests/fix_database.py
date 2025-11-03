import sqlite3
import os
from datetime import datetime

# 数据库文件路径
db_path = 'backend/simple_app.db'

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("开始修复tasks表的ID字段自增问题...")
    
    # 1. 备份现有数据（如果有的话）
    print("1. 备份现有数据...")
    cursor.execute("SELECT COUNT(*) FROM tasks")
    task_count = cursor.fetchone()[0]
    print(f"   当前tasks表中有 {task_count} 条记录")
    
    if task_count > 0:
        cursor.execute("CREATE TABLE tasks_backup AS SELECT * FROM tasks")
        print("   已创建备份表 tasks_backup")
    
    # 2. 删除现有的tasks表
    print("2. 删除现有的tasks表...")
    cursor.execute("DROP TABLE IF EXISTS tasks")
    
    # 3. 重新创建tasks表，确保ID字段有AUTOINCREMENT
    print("3. 重新创建tasks表...")
    create_table_sql = """
    CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        task_type VARCHAR(8) NOT NULL,
        tags JSON,
        assignment_type VARCHAR(8) NOT NULL,
        assigned_to BIGINT,
        target_group_id BIGINT,
        target_identity VARCHAR(20),
        status VARCHAR(10),
        priority VARCHAR(6),
        target_amount FLOAT,
        current_amount FLOAT,
        target_quantity INTEGER,
        current_quantity INTEGER,
        jielong_target_count INTEGER,
        jielong_current_count INTEGER,
        jielong_config JSON,
        is_completed BOOLEAN,
        start_time DATETIME,
        end_time DATETIME,
        due_date DATETIME,
        created_by BIGINT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,
        FOREIGN KEY(assigned_to) REFERENCES users (id),
        FOREIGN KEY(target_group_id) REFERENCES user_groups (id),
        FOREIGN KEY(created_by) REFERENCES users (id)
    )
    """
    cursor.execute(create_table_sql)
    
    # 4. 如果有备份数据，恢复数据
    if task_count > 0:
        print("4. 恢复备份数据...")
        cursor.execute("""
            INSERT INTO tasks (title, description, task_type, tags, assignment_type, 
                             assigned_to, target_group_id, target_identity, status, priority,
                             target_amount, current_amount, target_quantity, current_quantity,
                             jielong_target_count, jielong_current_count, jielong_config,
                             is_completed, start_time, end_time, due_date, created_by, 
                             created_at, updated_at)
            SELECT title, description, task_type, tags, assignment_type, 
                   assigned_to, target_group_id, target_identity, status, priority,
                   target_amount, current_amount, target_quantity, current_quantity,
                   jielong_target_count, jielong_current_count, jielong_config,
                   is_completed, start_time, end_time, due_date, created_by, 
                   created_at, updated_at
            FROM tasks_backup
        """)
        
        # 删除备份表
        cursor.execute("DROP TABLE tasks_backup")
        print("   数据恢复完成，备份表已删除")
    
    # 5. 测试ID自增功能
    print("5. 测试ID自增功能...")
    cursor.execute("""
        INSERT INTO tasks (title, task_type, assignment_type, priority, created_by) 
        VALUES ('Test Task', 'checkbox', 'all', 'medium', 1)
    """)
    task_id = cursor.lastrowid
    print(f"   插入测试任务，自动生成ID: {task_id}")
    
    # 删除测试记录
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    print("   测试记录已删除")
    
    # 6. 验证表结构
    print("6. 验证新表结构...")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
    sql = cursor.fetchone()[0]
    print(f"   新表创建SQL: {sql}")
    
    # 提交所有更改
    conn.commit()
    print("\n✅ tasks表ID字段自增问题修复完成！")
    
except Exception as e:
    print(f"\n❌ 修复过程中出现错误: {e}")
    conn.rollback()
    
finally:
    conn.close()
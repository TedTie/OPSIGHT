import sqlite3
import os

# 检查数据库文件是否存在
db_path = 'backend/simple_app.db'
if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查tasks表结构
print("Tasks table structure:")
try:
    cursor.execute('PRAGMA table_info(tasks)')
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  {row}")
    else:
        print("  Tasks table does not exist")
except Exception as e:
    print(f"  Error checking tasks table: {e}")

# 检查表的创建SQL
print("\nTasks table creation SQL:")
try:
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
    sql = cursor.fetchone()
    if sql:
        print(f"  {sql[0]}")
    else:
        print("  No creation SQL found")
except Exception as e:
    print(f"  Error getting creation SQL: {e}")

# 检查序列信息
print("\nSQLite sequence info:")
try:
    cursor.execute("SELECT name, seq FROM sqlite_sequence WHERE name='tasks'")
    seq_info = cursor.fetchone()
    if seq_info:
        print(f"  Table: {seq_info[0]}, Next ID: {seq_info[1]}")
    else:
        print("  No sequence info found for tasks table")
except Exception as e:
    print(f"  Error checking sequence: {e}")

# 尝试插入一个测试记录来检查ID生成
print("\nTesting ID generation:")
try:
    cursor.execute("""
        INSERT INTO tasks (title, task_type, assignment_type, priority, created_by) 
        VALUES ('Test Task', 'checkbox', 'all', 'medium', 1)
    """)
    task_id = cursor.lastrowid
    print(f"  Inserted task with ID: {task_id}")
    
    # 删除测试记录
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    print(f"  Deleted test task")
    
    conn.commit()
except Exception as e:
    print(f"  Error testing ID generation: {e}")
    conn.rollback()

conn.close()
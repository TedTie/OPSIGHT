import sqlite3

conn = sqlite3.connect('simple_app.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(ai_call_logs)')
columns = cursor.fetchall()

print('ai_call_logs表结构:')
for col in columns:
    print(f'  {col[1]} {col[2]} {"NOT NULL" if col[3] else "NULL"} {"PRIMARY KEY" if col[5] else ""}')

# 检查表的创建语句
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='ai_call_logs'")
create_sql = cursor.fetchone()
if create_sql:
    print(f'\n表创建语句:\n{create_sql[0]}')

conn.close()
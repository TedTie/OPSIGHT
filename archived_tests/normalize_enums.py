#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规范化数据库中的枚举值为小写，以兼容 SQLAlchemy Enum 映射。
修复列：tasks.task_type、tasks.assignment_type、tasks.priority、tasks.status。
"""

import sqlite3
from pathlib import Path

DB_CANDIDATES = [
    Path("backend") / "simple_app.db",
    Path("simple_app.db"),
]


def find_db_path() -> str:
    for p in DB_CANDIDATES:
        if p.exists():
            return str(p)
    raise FileNotFoundError("未找到 simple_app.db 数据库文件")


def show_distinct(cur):
    for col in ["task_type", "assignment_type", "priority", "status"]:
        try:
            cur.execute(f"SELECT DISTINCT {col} FROM tasks")
            values = [row[0] for row in cur.fetchall()]
            print(f"{col} 当前值: {values}")
        except sqlite3.Error as e:
            print(f"读取 {col} 失败: {e}")


def normalize_enums(db_path: str):
    print(f"连接数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print("修正前枚举值:")
    show_distinct(cur)

    updates = [
        # task_type: 大写转小写，并将历史 'normal' 统一为 'checkbox'
        "UPDATE tasks SET task_type = LOWER(task_type) WHERE task_type IN ('AMOUNT','QUANTITY','JIELONG','CHECKBOX')",
        "UPDATE tasks SET task_type = 'checkbox' WHERE task_type = 'normal'",
        # assignment_type、priority、status: 统一转小写
        "UPDATE tasks SET assignment_type = LOWER(assignment_type) WHERE assignment_type IN ('USER','GROUP','IDENTITY','ALL')",
        "UPDATE tasks SET priority = LOWER(priority) WHERE priority IN ('LOW','MEDIUM','HIGH','URGENT')",
        "UPDATE tasks SET status = LOWER(status) WHERE status IN ('PENDING','PROCESSING','DONE','CANCELLED')",
    ]

    for sql in updates:
        cur.execute(sql)

    conn.commit()
    print("✅ 已规范化枚举值为小写")
    print("修正后枚举值:")
    show_distinct(cur)
    conn.close()


if __name__ == "__main__":
    db = find_db_path()
    normalize_enums(db)
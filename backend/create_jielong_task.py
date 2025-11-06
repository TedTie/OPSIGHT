#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速在 SQLite 数据库中插入一条接龙任务，便于接口联调。
"""

import json
import sqlite3
import os
from pathlib import Path

DB_PATHS = [
    Path("backend") / "simple_app.db",
    Path(__file__).parent / "simple_app.db",
]

def get_db_path():
    for p in DB_PATHS:
        if p.exists():
            return str(p)
    raise FileNotFoundError("找不到 simple_app.db 数据库文件")

def main():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # 获取admin用户ID
        cur.execute("SELECT id FROM users WHERE username='admin' LIMIT 1")
        row = cur.fetchone()
        admin_id = row[0] if row else 1

        jielong_config = {
            "id_enabled": True,
            "remark_enabled": True,
            "intention_enabled": False,
            "custom_field_enabled": False,
            "custom_field_name": "",
            "custom_field_type": "text"
        }

        sql = (
            "INSERT INTO tasks("
            "title, description, task_type, tags, assignment_type, "
            "assigned_to, target_group_id, target_identity, status, priority, "
            "target_amount, current_amount, target_quantity, current_quantity, "
            "jielong_target_count, jielong_current_count, jielong_config, "
            "is_completed, start_time, end_time, due_date, created_by) "
            "VALUES(?, ?, ?, NULL, ?, NULL, NULL, NULL, ?, ?, NULL, 0.0, NULL, 0, ?, 0, ?, 0, NULL, NULL, NULL, ?)"
        )

        params = (
            "测试接龙任务",
            "用于接口联调的接龙任务",
            "jielong",
            "all",
            "pending",
            "medium",
            3,
            json.dumps(jielong_config),
            admin_id,
        )

        cur.execute(sql, params)
        conn.commit()
        task_id = cur.lastrowid
        print(f"✓ 已创建接龙任务，ID: {task_id}")

    except Exception as e:
        conn.rollback()
        print("❌ 创建失败:", e)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
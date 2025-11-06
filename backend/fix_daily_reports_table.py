#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 daily_reports 表的自增ID问题
"""

from app.db import engine
from sqlalchemy import text

def main():
    with engine.connect() as conn:
        try:
            # 开始事务
            trans = conn.begin()
            
            # 备份现有数据（如果有的话）
            print("1. 检查现有数据...")
            result = conn.execute(text("SELECT COUNT(*) FROM daily_reports;"))
            count = result.fetchone()[0]
            print(f"   现有记录数: {count}")
            
            if count > 0:
                print("2. 备份现有数据...")
                conn.execute(text("""
                    CREATE TABLE daily_reports_backup AS 
                    SELECT * FROM daily_reports;
                """))
                print("   ✓ 数据备份完成")
            
            # 删除原表
            print("3. 删除原表...")
            conn.execute(text("DROP TABLE daily_reports;"))
            print("   ✓ 原表已删除")
            
            # 创建新表（带AUTOINCREMENT）
            print("4. 创建新表...")
            conn.execute(text("""
                CREATE TABLE daily_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT NOT NULL,
                    work_date DATE NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    work_hours FLOAT NOT NULL,
                    task_progress TEXT,
                    work_summary TEXT,
                    mood_score INTEGER NOT NULL,
                    efficiency_score INTEGER NOT NULL,
                    call_count INTEGER DEFAULT 0,
                    call_duration INTEGER DEFAULT 0,
                    achievements TEXT,
                    challenges TEXT,
                    tomorrow_plan TEXT,
                    ai_analysis JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users (id)
                );
            """))
            print("   ✓ 新表创建完成")
            
            # 恢复数据（如果有备份）
            if count > 0:
                print("5. 恢复数据...")
                conn.execute(text("""
                    INSERT INTO daily_reports (
                        user_id, work_date, title, content, work_hours,
                        task_progress, work_summary, mood_score, efficiency_score,
                        call_count, call_duration, achievements, challenges,
                        tomorrow_plan, ai_analysis, created_at, updated_at
                    )
                    SELECT 
                        user_id, work_date, title, content, work_hours,
                        task_progress, work_summary, mood_score, efficiency_score,
                        call_count, call_duration, achievements, challenges,
                        tomorrow_plan, ai_analysis, created_at, updated_at
                    FROM daily_reports_backup;
                """))
                
                # 删除备份表
                conn.execute(text("DROP TABLE daily_reports_backup;"))
                print("   ✓ 数据恢复完成，备份表已删除")
            
            # 提交事务
            trans.commit()
            print("✅ daily_reports 表修复完成！")
            
            # 验证新表结构
            print("\n6. 验证新表结构...")
            result = conn.execute(text("PRAGMA table_info(daily_reports);"))
            columns = result.fetchall()
            for col in columns:
                if col[1] == 'id':
                    print(f"   ID字段: {col[1]} ({col[2]}) - PK: {col[5]}, NotNull: {col[3]}")
                    break
            
            # 检查创建语句
            result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='daily_reports';"))
            create_sql = result.fetchone()
            if create_sql and 'AUTOINCREMENT' in create_sql[0]:
                print("   ✓ AUTOINCREMENT 已正确设置")
            else:
                print("   ❌ AUTOINCREMENT 设置可能有问题")
                
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            trans.rollback()
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
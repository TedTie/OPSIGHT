#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理测试数据
"""

from app.db import engine
from sqlalchemy import text

def main():
    with engine.connect() as conn:
        try:
            # 删除测试日报数据
            result = conn.execute(text("DELETE FROM daily_reports;"))
            print(f"✓ 删除了 {result.rowcount} 条日报记录")
            
            # 重置自增ID
            conn.execute(text("DELETE FROM sqlite_sequence WHERE name='daily_reports';"))
            print("✓ 重置了自增ID")
            
            conn.commit()
            print("✅ 测试数据清理完成！")
            
        except Exception as e:
            print(f"❌ 清理失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
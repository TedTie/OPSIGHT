#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接数据库操作测试脚本
"""

from app.db import SessionLocal
from app.models import DailyReport, User
from datetime import date, datetime

def main():
    db = SessionLocal()
    
    try:
        # 获取用户
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("❌ 找不到admin用户")
            return
        
        print(f"✓ 找到用户: {user.username} (ID: {user.id})")
        
        # 尝试创建日报
        report = DailyReport(
            user_id=user.id,
            work_date=date.today(),
            title="直接数据库测试",
            content="测试内容",
            work_hours=1.0,
            mood_score=5,
            efficiency_score=5,
            call_count=0,
            call_duration=0
        )
        
        print("✓ 创建日报对象成功")
        
        db.add(report)
        print("✓ 添加到会话成功")
        
        db.commit()
        print("✓ 提交到数据库成功")
        
        db.refresh(report)
        print(f"✓ 刷新对象成功，日报ID: {report.id}")
        
        # 查询验证
        saved_report = db.query(DailyReport).filter(DailyReport.id == report.id).first()
        if saved_report:
            print(f"✓ 验证成功，日报标题: {saved_report.title}")
        else:
            print("❌ 验证失败，找不到保存的日报")
            
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
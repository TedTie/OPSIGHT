#!/usr/bin/env python3
"""
数据库清理脚本 - 清理AI相关的测试数据
"""

import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from app.db import get_db
from app.models import AIAgent, AIFunction, AICallLog

def clean_ai_data():
    """清理AI相关的测试数据"""
    db = next(get_db())
    
    try:
        # 删除AI调用日志
        deleted_logs = db.query(AICallLog).delete()
        print(f"删除了 {deleted_logs} 条AI调用日志")
        
        # 删除AI功能
        deleted_functions = db.query(AIFunction).delete()
        print(f"删除了 {deleted_functions} 个AI功能")
        
        # 删除AI智能体
        deleted_agents = db.query(AIAgent).delete()
        print(f"删除了 {deleted_agents} 个AI智能体")
        
        db.commit()
        print("✅ 数据库清理完成")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 清理失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean_ai_data()
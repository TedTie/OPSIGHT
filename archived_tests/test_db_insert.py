#!/usr/bin/env python3
"""
测试数据库插入
"""

import sys
import os
from datetime import datetime

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# 切换到backend目录，确保使用正确的数据库文件
os.chdir(backend_path)

from app.db import get_db
from app.models import AICallLog, CallStatus

def test_insert():
    """测试插入AI调用日志"""
    db = next(get_db())
    
    try:
        # 创建测试记录
        call_log = AICallLog(
            function_id=1,
            agent_id=1,
            user_id=1,
            request_data={"input_text": "测试"},
            status=CallStatus.PENDING,
            duration_ms=0,
            started_at=datetime.utcnow()
        )
        
        print("📝 创建AICallLog对象成功")
        
        db.add(call_log)
        print("📝 添加到session成功")
        
        db.commit()
        print("✅ 提交成功")
        
        db.refresh(call_log)
        print(f"✅ 插入成功，ID: {call_log.id}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 插入失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_insert()
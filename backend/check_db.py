#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的任务数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from app.models import Task, User

def main():
    db = next(get_db())
    
    # 检查任务数据
    tasks = db.query(Task).all()
    print('任务数据分析:')
    print(f'总任务数: {len(tasks)}')
    print()
    
    assignment_type_count = {}
    for task in tasks:
        assignment_type = task.assignment_type.value if task.assignment_type else 'None'
        assignment_type_count[assignment_type] = assignment_type_count.get(assignment_type, 0) + 1
        print(f'ID:{task.id} 标题:{task.title} 分配类型:{assignment_type} 分配给:{task.assigned_to}')
    
    print()
    print('分配类型统计:')
    for assignment_type, count in assignment_type_count.items():
        print(f'  {assignment_type}: {count}个')
    
    # 检查用户数据
    print()
    print('用户数据:')
    users = db.query(User).all()
    for user in users:
        print(f'ID:{user.id} 用户名:{user.username} 组ID:{user.group_id} 身份类型:{user.identity_type}')

if __name__ == "__main__":
    main()
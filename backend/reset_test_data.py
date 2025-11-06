#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置测试数据以符合审计报告的预期
根据审计报告，应该有10个任务：
- 4个 assignment_type: "all" 的任务
- 4个 assignment_type: "user" 的任务  
- 2个 assignment_type: "group" 的任务

test_user应该能看到6个任务：
- 4个 "all" 类型的任务
- 2个 "group" 类型且target_group_id=1的任务
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from app.models import Task, TaskAssignmentType, TaskType, TaskStatus
from sqlalchemy.orm import Session

def reset_test_data():
    db = next(get_db())
    
    # 删除所有现有任务
    db.query(Task).delete()
    db.commit()
    
    # 创建符合审计报告预期的10个任务
    test_tasks = [
        # 4个 assignment_type: "all" 的任务 (所有用户都能看到)
        {
            "title": "全员任务1 - 系统维护",
            "description": "系统维护任务，所有用户都需要了解",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.ALL,
            "assigned_to": None,
            "target_group_id": None,
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        },
        {
            "title": "全员任务2 - 安全培训",
            "description": "安全培训任务，所有用户都需要参与",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.ALL,
            "assigned_to": None,
            "target_group_id": None,
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        },
        {
            "title": "全员任务3 - 政策更新",
            "description": "政策更新通知，所有用户都需要查看",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.ALL,
            "assigned_to": None,
            "target_group_id": None,
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        },
        {
            "title": "全员任务4 - 年度总结",
            "description": "年度总结任务，所有用户都需要参与",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.ALL,
            "assigned_to": None,
            "target_group_id": None,
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        },
        
        # 4个 assignment_type: "user" 的任务 (分配给特定用户)
        {
            "title": "个人任务1 - 分配给admin",
            "description": "分配给admin的个人任务",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.USER,
            "assigned_to": 1,  # admin
            "target_group_id": None,
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        },
        {
            "title": "个人任务2 - 分配给jlpss-chenjianxiong",
            "description": "分配给jlpss-chenjianxiong的个人任务",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.USER,
            "assigned_to": 2,  # jlpss-chenjianxiong
            "target_group_id": None,
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        },
        {
            "title": "个人任务3 - 分配给test_user",
            "description": "分配给test_user的个人任务",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.USER,
            "assigned_to": 3,  # test_user
            "target_group_id": None,
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        },
        {
            "title": "个人任务4 - 分配给admin",
            "description": "分配给admin的另一个个人任务",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.USER,
            "assigned_to": 1,  # admin
            "target_group_id": None,
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        },
        
        # 2个 assignment_type: "group" 的任务
        {
            "title": "组任务1 - MYC-SS01Team",
            "description": "分配给MYC-SS01Team组的任务",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.GROUP,
            "assigned_to": None,
            "target_group_id": 1,  # MYC-SS01Team (test_user和jlpss-chenjianxiong都在这个组)
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        },
        {
            "title": "组任务2 - MYC-LP01Team",
            "description": "分配给MYC-LP01Team组的任务",
            "task_type": TaskType.CHECKBOX,
            "assignment_type": TaskAssignmentType.GROUP,
            "assigned_to": None,
            "target_group_id": 2,  # MYC-LP01Team (admin在这个组)
            "target_identity": None,
            "status": TaskStatus.PENDING,
            "created_by": 1  # admin创建
        }
    ]
    
    # 插入任务
    for task_data in test_tasks:
        task = Task(**task_data)
        db.add(task)
    
    db.commit()
    
    # 验证数据
    tasks = db.query(Task).all()
    print(f"✅ 成功创建 {len(tasks)} 个测试任务")
    
    assignment_type_count = {}
    for task in tasks:
        assignment_type = task.assignment_type.value
        assignment_type_count[assignment_type] = assignment_type_count.get(assignment_type, 0) + 1
        print(f"  ID:{task.id} 标题:{task.title} 分配类型:{assignment_type} 分配给:{task.assigned_to} 目标组:{task.target_group_id}")
    
    print()
    print("分配类型统计:")
    for assignment_type, count in assignment_type_count.items():
        print(f"  {assignment_type}: {count}个")
    
    print()
    print("预期结果:")
    print("  admin: 10个任务 (所有任务)")
    print("  jlpss-chenjianxiong: 10个任务 (所有任务)")
    print("  test_user: 6个任务 (4个all + 1个user + 1个group)")

if __name__ == "__main__":
    reset_test_data()
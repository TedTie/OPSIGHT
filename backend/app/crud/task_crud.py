from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from ..models import Task, TaskRecord, JielongRecord
from ..schemas import JielongParticipationCreate


def log_task_progress(db: Session, task_id: int, user_id: int, value: float) -> Optional[Task]:
    """记录任务进度（金额/数量），并返回更新后的任务。"""
    # 检查任务是否存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None

    # 仅处理金额与数量类型（兼容 Enum 或字符串）
    task_type = getattr(task.task_type, 'value', task.task_type)
    if task_type not in ("amount", "quantity"):
        return None

    # 创建进度记录（TaskRecord 只包含 value、task_id、user_id）
    task_record = TaskRecord(
        task_id=task_id,
        user_id=user_id,
        value=float(value),
        created_at=datetime.utcnow()
    )

    db.add(task_record)

    # 累加任务当前进度
    if task_type == "amount":
        task.current_amount = (task.current_amount or 0.0) + float(value)
    elif task_type == "quantity":
        # 对数量类型，按整数累加
        try:
            inc = int(value)
        except (TypeError, ValueError):
            inc = 0
        task.current_quantity = (task.current_quantity or 0) + inc

    # 更新时间戳
    task.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(task)
        return task
    except Exception:
        db.rollback()
        return None


def add_jielong_participation(
    db: Session,
    task_id: int,
    user_id: int,
    data: JielongParticipationCreate,
) -> Optional[JielongRecord]:
    """添加接龙任务参与记录（使用 JielongRecord 模型字段）。"""
    # 检查任务存在且为接龙类型
    task = db.query(Task).filter(Task.id == task_id).first()
    task_type = getattr(task.task_type, 'value', task.task_type) if task else None
    if not task or task_type != "jielong":
        return None

    # 创建接龙记录
    jielong_record = JielongRecord(
        task_id=task_id,
        user_id=user_id,
        student_id=data.student_id,
        notes=data.notes,
        intention=data.intention,
        created_at=datetime.utcnow(),
    )

    db.add(jielong_record)

    # 增加接龙当前计数
    task.jielong_current_count = (task.jielong_current_count or 0) + 1
    task.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(jielong_record)
        return jielong_record
    except Exception:
        db.rollback()
        return None
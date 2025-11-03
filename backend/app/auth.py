from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from .db import get_db
from .models import User

# 简单的会话存储（生产环境应该使用 Redis）
user_sessions = {}

def get_current_user_simple(request: Request, db: Session = Depends(get_db)) -> User:
    """获取当前用户 - 超级简化版"""
    username = request.cookies.get("username")

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录，请先登录"
        )

    user = db.query(User).filter(User.username == username, User.is_active == True).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在或已被禁用"
        )

    return user

def login_user_simple(username: str, db: Session) -> User:
    """简单登录 - 只需要用户名"""
    user = db.query(User).filter(User.username == username, User.is_active == True).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在或已被禁用"
        )

    return user

def logout_user_simple():
    """简单登出"""
    return {"message": "登出成功"}
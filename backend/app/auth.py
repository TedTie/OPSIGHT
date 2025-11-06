from typing import Optional
from fastapi import HTTPException, status, Depends, Request, Response
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
from .crud.user_crud import get_user_by_username

# 简单的会话存储（生产环境应该使用 Redis）
user_sessions = {}

def get_current_active_user(request: Request, db: Session = Depends(get_db)) -> User:
    # 从会话中获取用户数据
    user_data = request.session.get('user')
    
    if not user_data:
        raise HTTPException(status_code=401, detail="未认证")
    # 从数据库中获取最新的用户信息（好习惯，以防用户信息被后台更改）
    user = db.query(User).filter(User.id == user_data.get('id')).first()
    if not user:
        # 如果 session 中的用户在数据库中已不存在
        request.session.clear() # 清理无效 session
        raise HTTPException(status_code=401, detail="用户不存在")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return user

async def login_user_session(username: str, response: Response, request: Request, db: Session) -> User:
    """基于会话的登录函数"""
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或密码错误")
    
    # 将用户信息存储在服务器端的 session 中
    request.session['user'] = {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }
    
    return user

def login_user_simple(username: str, db: Session) -> User:
    """简单登录 - 只需要用户名（保留向后兼容）"""
    user = db.query(User).filter(User.username == username, User.is_active == True).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在或已被禁用"
        )

    return user

async def logout_user_session(request: Request, response: Response):
    # 清空服务器上的会话数据
    request.session.clear()
    
    # (可选) 清除浏览器中的 session cookie，让前端立即感知
    response.delete_cookie("session")
    
    return {"message": "登出成功"}
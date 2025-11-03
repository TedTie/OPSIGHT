#!/usr/bin/env python3
"""
直接测试FastAPI的UserResponse序列化
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.schemas import UserResponse
from app.db import get_db
from app.models import User
import json

app = FastAPI()

@app.get("/test-user-response")
async def test_user_response():
    """测试UserResponse序列化"""
    db = next(get_db())
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    if admin_user:
        user_response = UserResponse(
            id=admin_user.id,
            username=admin_user.username,
            role=admin_user.role,
            identity_type=admin_user.identity_type,
            full_identity=admin_user.get_full_identity(),
            ai_knowledge_branch=admin_user.get_ai_knowledge_branch(),
            organization=admin_user.organization,
            group_id=admin_user.group_id,
            group_name=admin_user.group.name if admin_user.group else None,
            is_active=admin_user.is_active,
            created_at=admin_user.created_at
        )
        return user_response
    else:
        return {"error": "User not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
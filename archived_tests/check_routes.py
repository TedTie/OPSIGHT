#!/usr/bin/env python3
"""
检查FastAPI路由
"""

from app.main import app

def check_routes():
    """检查所有路由"""
    print("=== FastAPI 路由列表 ===")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"{route.methods} {route.path}")
        elif hasattr(route, 'path'):
            print(f"[MOUNT] {route.path}")

if __name__ == "__main__":
    check_routes()
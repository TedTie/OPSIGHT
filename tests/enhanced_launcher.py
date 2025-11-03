#!/usr/bin/env python3
"""
OPSIGHT 增强极简版 - 一键启动脚本
启动后端和前端服务
"""

import subprocess
import time
import os
import sys
import webbrowser
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("🎯 OPSIGHT 增强极简版 - 一键启动")
    print("=" * 60)
    print("✨ 功能特性:")
    print("   📋 任务管理 - 支持4种任务类型")
    print("   📝 日报管理 - AI智能分析")
    print("   👥 用户管理 - 三级权限体系")
    print("   📊 数据分析 - 可视化图表")
    print("   🤖 AI集成 - 情感分析和工作建议")
    print()
    print("🚀 服务地址:")
    print("   📍 后端API: http://localhost:8001")
    print("   📍 前端界面: http://localhost:3001")
    print("   📍 API文档: http://localhost:8001/docs")
    print()
    print("🔑 默认账户:")
    print("   👤 admin - 超级管理员")
    print("   👤 user1 - 普通用户")
    print("=" * 60)

def start_backend():
    """启动后端服务"""
    print("🔧 启动后端服务...")
    backend_path = Path(__file__).parent / "backend" / "minimal_enhanced"

    # 检查Python环境
    try:
        subprocess.run([sys.executable, "-c", "import fastapi"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ 未找到FastAPI，正在安装依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(backend_path / "requirements.txt")], check=True)

    # 启动后端
    backend_process = subprocess.Popen(
        [sys.executable, "start.py"],
        cwd=str(backend_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("⏳ 等待后端服务启动...")
    time.sleep(3)

    # 检查后端是否启动成功
    try:
        import requests
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务启动成功")
            return backend_process
        else:
            print("❌ 后端服务启动失败")
            return None
    except Exception as e:
        print(f"❌ 检查后端服务失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("🌐 启动前端服务...")
    frontend_path = Path(__file__).parent / "frontend" / "minimal_enhanced"

    # 启动前端
    frontend_process = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=str(frontend_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("⏳ 等待前端服务启动...")
    time.sleep(2)

    print("✅ 前端服务启动成功")
    return frontend_process

def check_services():
    """检查服务状态"""
    try:
        import requests

        # 检查后端
        backend_ok = False
        try:
            response = requests.get("http://localhost:8001/health", timeout=3)
            backend_ok = response.status_code == 200
        except:
            pass

        # 检查前端
        frontend_ok = False
        try:
            response = requests.get("http://localhost:3001", timeout=3)
            frontend_ok = response.status_code == 200
        except:
            pass

        return backend_ok, frontend_ok
    except ImportError:
        print("⚠️  未安装requests库，跳过服务检查")
        return True, True

def main():
    print_banner()

    # 启动后端
    backend_process = start_backend()
    if not backend_process:
        print("❌ 后端服务启动失败，程序退出")
        return

    # 启动前端
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ 前端服务启动失败，程序退出")
        backend_process.terminate()
        return

    print("\n🎉 OPSIGHT 增强极简版启动完成！")
    print("🌐 正在打开浏览器...")

    # 打开浏览器
    time.sleep(1)
    webbrowser.open("http://localhost:3001")

    print("\n🛑 按 Ctrl+C 停止服务")

    try:
        while True:
            time.sleep(1)
            # 检查服务状态
            backend_ok, frontend_ok = check_services()
            if not backend_ok:
                print("⚠️  后端服务异常")
            if not frontend_ok:
                print("⚠️  前端服务异常")
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        backend_process.terminate()
        frontend_process.terminate()

        # 等待进程结束
        try:
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
            frontend_process.kill()

        print("✅ 服务已停止")
        print("👋 感谢使用 OPSIGHT 增强极简版！")

if __name__ == "__main__":
    main()
@echo off
chcp 65001 >nul
title OPSIGHT 系统启动器

echo ============================================================
echo 🚀 OPSIGHT - 智能任务与日报管理系统
echo ============================================================
echo.

echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请安装Python 3.8+并添加到系统PATH
    pause
    exit /b 1
)
echo ✅ Python环境正常

echo.
echo 🔍 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装或未添加到PATH
    echo 请安装Node.js并添加到系统PATH
    pause
    exit /b 1
)
echo ✅ Node.js环境正常

echo.
echo 📦 安装后端依赖...
cd /d "%~dp0backend"
python -m pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 后端依赖安装可能有问题，但继续启动...
) else (
    echo ✅ 后端依赖安装成功
)

echo.
echo 📦 安装前端依赖...
cd /d "%~dp0frontend"
npm install >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 前端依赖安装可能有问题，但继续启动...
) else (
    echo ✅ 前端依赖安装成功
)

echo.
echo 🔧 启动后端服务...
cd /d "%~dp0backend"
start "OPSIGHT Backend" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo.
echo ⏳ 等待后端服务启动...
timeout /t 3 /nobreak >nul

echo.
echo 🎨 启动前端服务...
cd /d "%~dp0frontend"
start "OPSIGHT Frontend" cmd /k "npm run dev"

echo.
echo ⏳ 等待前端服务启动...
timeout /t 5 /nobreak >nul

echo.
echo 🌐 打开浏览器...
start http://localhost:3001

echo.
echo ============================================================
echo 🎉 OPSIGHT 系统启动成功！
echo ============================================================
echo 📍 前端地址: http://localhost:3001
echo 📍 后端地址: http://localhost:8000
echo 📚 API文档: http://localhost:8000/docs
echo ============================================================
echo 💡 默认登录信息:
echo    用户名: admin
echo    密码: admin123
echo ============================================================
echo.
echo 💡 提示: 关闭此窗口不会停止服务
echo    要停止服务，请关闭后端和前端的命令行窗口
echo.
pause
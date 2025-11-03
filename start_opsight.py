#!/usr/bin/env python3
"""
OPSIGHT 系统统一启动脚本
一键启动前端和后端服务
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path

class OPSIGHTLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_path = self.project_root / "backend" / "minimal_enhanced"
        self.frontend_path = self.project_root / "frontend"
        self.backend_process = None
        self.frontend_process = None
        
    def print_banner(self):
        """打印启动横幅"""
        print("=" * 60)
        print("🚀 OPSIGHT - 智能任务与日报管理系统")
        print("=" * 60)
        print("📍 项目路径:", self.project_root)
        print("🔧 后端路径:", self.backend_path)
        print("🎨 前端路径:", self.frontend_path)
        print("=" * 60)
        
    def check_dependencies(self):
        """检查依赖"""
        print("🔍 检查系统依赖...")
        
        # 检查Python
        try:
            python_version = sys.version.split()[0]
            print(f"✅ Python版本: {python_version}")
        except Exception as e:
            print(f"❌ Python检查失败: {e}")
            return False
            
        # 检查Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js版本: {result.stdout.strip()}")
            else:
                print("❌ Node.js未安装")
                return False
        except Exception as e:
            print(f"❌ Node.js检查失败: {e}")
            return False
            
        # 检查npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm版本: {result.stdout.strip()}")
            else:
                print("❌ npm未安装")
                return False
        except Exception as e:
            print(f"❌ npm检查失败: {e}")
            return False
            
        return True
        
    def install_backend_dependencies(self):
        """安装后端依赖"""
        print("📦 安装后端依赖...")
        try:
            os.chdir(self.backend_path)
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 后端依赖安装成功")
                return True
            else:
                print(f"❌ 后端依赖安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 后端依赖安装异常: {e}")
            return False
        finally:
            os.chdir(self.project_root)
            
    def install_frontend_dependencies(self):
        """安装前端依赖"""
        print("📦 安装前端依赖...")
        try:
            os.chdir(self.frontend_path)
            result = subprocess.run(["npm", "install"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 前端依赖安装成功")
                return True
            else:
                print(f"❌ 前端依赖安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 前端依赖安装异常: {e}")
            return False
        finally:
            os.chdir(self.project_root)
            
    def start_backend(self):
        """启动后端服务"""
        print("🔧 启动后端服务...")
        try:
            os.chdir(self.backend_path)
            self.backend_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print("✅ 后端服务启动中...")
            print("📍 后端地址: http://localhost:8001")
            print("📚 API文档: http://localhost:8001/docs")
            return True
        except Exception as e:
            print(f"❌ 后端服务启动失败: {e}")
            return False
        finally:
            os.chdir(self.project_root)
            
    def start_frontend(self):
        """启动前端服务"""
        print("🎨 启动前端服务...")
        try:
            os.chdir(self.frontend_path)
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print("✅ 前端服务启动中...")
            print("📍 前端地址: http://localhost:3001")
            return True
        except Exception as e:
            print(f"❌ 前端服务启动失败: {e}")
            return False
        finally:
            os.chdir(self.project_root)
            
    def wait_for_services(self):
        """等待服务启动"""
        print("⏳ 等待服务启动...")
        time.sleep(5)
        
        # 检查后端服务
        try:
            import requests
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                print("✅ 后端服务就绪")
            else:
                print("⚠️ 后端服务可能未完全启动")
        except Exception as e:
            print(f"⚠️ 后端服务检查失败: {e}")
            
        # 检查前端服务
        try:
            import requests
            response = requests.get("http://localhost:3001", timeout=5)
            if response.status_code == 200:
                print("✅ 前端服务就绪")
            else:
                print("⚠️ 前端服务可能未完全启动")
        except Exception as e:
            print(f"⚠️ 前端服务检查失败: {e}")
            
    def open_browser(self):
        """打开浏览器"""
        print("🌐 打开浏览器...")
        try:
            webbrowser.open("http://localhost:3001")
            print("✅ 浏览器已打开")
        except Exception as e:
            print(f"⚠️ 无法自动打开浏览器: {e}")
            print("请手动访问: http://localhost:3001")
            
    def cleanup(self):
        """清理进程"""
        print("\n🛑 正在关闭服务...")
        if self.backend_process:
            self.backend_process.terminate()
            print("✅ 后端服务已关闭")
        if self.frontend_process:
            self.frontend_process.terminate()
            print("✅ 前端服务已关闭")
            
    def run(self):
        """运行启动器"""
        try:
            self.print_banner()
            
            # 检查依赖
            if not self.check_dependencies():
                print("❌ 依赖检查失败，请安装必要的依赖")
                return False
                
            # 安装依赖
            if not self.install_backend_dependencies():
                print("❌ 后端依赖安装失败")
                return False
                
            if not self.install_frontend_dependencies():
                print("❌ 前端依赖安装失败")
                return False
                
            # 启动服务
            if not self.start_backend():
                print("❌ 后端服务启动失败")
                return False
                
            if not self.start_frontend():
                print("❌ 前端服务启动失败")
                return False
                
            # 等待服务启动
            self.wait_for_services()
            
            # 打开浏览器
            self.open_browser()
            
            print("\n" + "=" * 60)
            print("🎉 OPSIGHT 系统启动成功！")
            print("=" * 60)
            print("📍 前端地址: http://localhost:3001")
            print("📍 后端地址: http://localhost:8001")
            print("📚 API文档: http://localhost:8001/docs")
            print("=" * 60)
            print("💡 默认登录信息:")
            print("   用户名: admin")
            print("   密码: admin123")
            print("=" * 60)
            print("按 Ctrl+C 停止服务")
            
            # 保持运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
            
        return True

def main():
    """主函数"""
    launcher = OPSIGHTLauncher()
    success = launcher.run()
    if success:
        print("\n✅ OPSIGHT 系统已安全关闭")
    else:
        print("\n❌ OPSIGHT 系统启动失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
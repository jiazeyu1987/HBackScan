#!/usr/bin/env python3
"""
简单的API服务启动测试
"""
import asyncio
import uvicorn
import multiprocessing
import time
import signal
import sys

def start_server():
    """启动FastAPI服务器"""
    print("🚀 启动FastAPI服务器...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")

def test_server():
    """测试服务器响应"""
    import requests
    time.sleep(3)  # 等待服务器启动
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器启动成功，健康检查通过")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

if __name__ == "__main__":
    # 在后台启动服务器
    print("🔧 启动测试...")
    
    # 启动服务器进程
    server_process = multiprocessing.Process(target=start_server)
    server_process.start()
    
    try:
        # 测试服务器
        if test_server():
            print("\n📚 API文档地址:")
            print("   Swagger UI: http://localhost:8000/docs")
            print("   ReDoc: http://localhost:8000/redoc")
            print("   健康检查: http://localhost:8000/health")
            print("\n按 Ctrl+C 停止服务器")
            
            # 等待用户中断
            server_process.join()
        else:
            print("❌ 服务器测试失败")
            server_process.terminate()
            
    except KeyboardInterrupt:
        print("\n👋 正在停止服务器...")
        server_process.terminate()
        server_process.join()
        print("✅ 服务器已停止")
        sys.exit(0)
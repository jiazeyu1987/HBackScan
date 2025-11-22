#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动前端测试页面
"""

import webbrowser
import os
import time

def main():
    """启动前端页面"""
    # 获取HTML文件路径
    html_file = os.path.join(os.path.dirname(__file__), 'frontend', 'scanner_test.html')
    html_file = os.path.abspath(html_file)

    print("🏥 医院层级扫描系统 - 前端测试界面")
    print("=" * 50)

    # 检查文件是否存在
    if not os.path.exists(html_file):
        print(f"❌ 错误: 找不到HTML文件 {html_file}")
        return

    print(f"📁 前端文件: {html_file}")
    print(f"🌐 后端API: http://localhost:8002")
    print(f"📖 API文档: http://localhost:8002/docs")
    print()

    # 构造file URL
    file_url = f"file:///{html_file.replace('\\', '/')}"

    print("🚀 正在启动前端页面...")
    print(f"📍 页面地址: {file_url}")
    print()

    try:
        # 打开浏览器
        webbrowser.open(file_url)
        print("✅ 前端页面已启动！")
        print()
        print("📋 使用说明:")
        print("1. 确保后端服务运行在 http://localhost:8002")
        print("2. 在页面中输入医院名称进行扫描")
        print("3. 系统会自动监控扫描状态")
        print("4. 完成后会展示详细的扫描结果")
        print()
        print("💡 提示: 如果页面无法访问API，请检查后端服务是否正常启动")

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print(f"请手动打开: {file_url}")

if __name__ == "__main__":
    main()
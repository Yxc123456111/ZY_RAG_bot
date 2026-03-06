#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCM Chatbot - 中医智能助手启动器
固定端口8888
"""

import subprocess
import sys
import time

API_PORT = 8888

def main():
    print("=" * 60)
    print("TCM Chatbot - 中医智能助手")
    print("=" * 60)
    print()
    print(f"API端口: {API_PORT}")
    print()
    
    # 启动API服务（新窗口）
    print("[1/2] 启动API服务...")
    api_proc = subprocess.Popen(
        [sys.executable, "main.py", "--api"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # 等待API启动
    print("等待API服务就绪...")
    time.sleep(5)
    
    # 启动桌面客户端（新窗口）
    print("[2/2] 启动桌面客户端...")
    desktop_proc = subprocess.Popen(
        [sys.executable, "desktop_chat.py"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    print()
    print("=" * 60)
    print("所有服务已启动!")
    print(f"API地址: http://localhost:{API_PORT}")
    print(f"API文档: http://localhost:{API_PORT}/docs")
    print("=" * 60)
    print()
    print("提示: 关闭此窗口不会停止服务")
    print("请手动关闭API和桌面客户端窗口")
    print()
    
    # 等待用户按回车
    input("按 Enter 键退出此启动器...")
    
    print("启动器已退出 (服务仍在运行)")


if __name__ == "__main__":
    main()

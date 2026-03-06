#!/usr/bin/env python3
"""启动API服务"""
import subprocess
import sys
import time
import os

def main():
    print("启动中医智能助手API服务...")
    print("访问地址: http://localhost:8888")
    print("API文档: http://localhost:8888/docs")
    print("按 Ctrl+C 停止服务\n")
    
    try:
        subprocess.run([sys.executable, "main.py", "--api", "--port", "8888"])
    except KeyboardInterrupt:
        print("\n服务已停止")

if __name__ == "__main__":
    main()

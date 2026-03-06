#!/usr/bin/env python3
"""启动桌面客户端"""
import subprocess
import sys
import time

def main():
    print("启动中医智能助手桌面客户端...")
    print("请确保API服务已启动 (python main.py --api)\n")
    
    try:
        subprocess.run([sys.executable, "desktop_chat.py"])
    except KeyboardInterrupt:
        print("\n客户端已关闭")

if __name__ == "__main__":
    main()

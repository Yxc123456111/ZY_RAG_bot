#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 连接诊断测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import socket


def check_port_available(host, port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


def test_api_connection():
    """测试 API 连接"""
    print("=" * 60)
    print("API 连接诊断")
    print("=" * 60)
    
    api_url = "http://localhost:8888"
    
    # 1. 检查端口是否被占用
    print("\n1. 检查端口 8888 状态")
    print("-" * 40)
    if check_port_available("localhost", 8888):
        print("[OK] 端口 8888 已被占用（可能有服务在运行）")
    else:
        print("[WARN] 端口 8888 未被占用（服务可能未启动）")
    
    # 2. 尝试连接健康检查端点
    print("\n2. 测试 /health 端点")
    print("-" * 40)
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        print(f"[OK] 连接成功")
        print(f"     状态码: {response.status_code}")
        print(f"     响应: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("[FAIL] 连接被拒绝 - API 服务可能未启动")
        print("       请运行: python main.py --api")
    except Exception as e:
        print(f"[FAIL] 连接错误: {e}")
    
    # 3. 测试根路径
    print("\n3. 测试根路径 /")
    print("-" * 40)
    try:
        response = requests.get(api_url, timeout=5)
        print(f"[OK] 连接成功")
        print(f"     状态码: {response.status_code}")
        print(f"     响应: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("[FAIL] 连接被拒绝")
    except Exception as e:
        print(f"[FAIL] 错误: {e}")
    
    # 4. 测试 /chat 端点
    print("\n4. 测试 /chat 端点")
    print("-" * 40)
    try:
        response = requests.post(
            f"{api_url}/chat",
            json={"message": "人参的功效"},
            timeout=10
        )
        print(f"[OK] 连接成功")
        print(f"     状态码: {response.status_code}")
        data = response.json()
        print(f"     意图: {data.get('intent')}")
        print(f"     类型: {data.get('data_type')}")
        print(f"     消息预览: {data.get('message', '')[:100]}...")
    except requests.exceptions.ConnectionError:
        print("[FAIL] 连接被拒绝")
    except Exception as e:
        print(f"[FAIL] 错误: {e}")
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    test_api_connection()

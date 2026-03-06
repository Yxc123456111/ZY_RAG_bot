#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟桌面客户端草药查询模式测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desktop_chat import TCMAPIClient


def test_herb_query_mode():
    """测试草药查询模式"""
    print("=" * 60)
    print("模拟桌面客户端草药查询模式")
    print("=" * 60)
    
    # 创建 API 客户端（与桌面客户端相同）
    api_client = TCMAPIClient(api_url="http://localhost:8888")
    
    # 测试 1: 直接查询 Supabase（草药查询模式）
    print("\n1. 测试直接查询 Supabase（草药查询模式）")
    print("-" * 40)
    
    try:
        result = api_client.query_supabase_herb("人参")
        print(f"查询结果: {result.get('success')}")
        print(f"消息: {result.get('message', 'N/A')}")
        if result.get('success'):
            print(f"药物名称: {result.get('drug_name')}")
            print(f"格式化预览: {result.get('formatted', 'N/A')[:100]}...")
        elif result.get('suggestions'):
            print(f"建议: {result.get('suggestions')}")
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 2: 测试丹砂查询
    print("\n2. 测试丹砂查询")
    print("-" * 40)
    
    try:
        result = api_client.query_supabase_herb("丹砂")
        print(f"查询结果: {result.get('success')}")
        print(f"消息: {result.get('message', 'N/A')}")
        if result.get('success'):
            print(f"药物名称: {result.get('drug_name')}")
            print(f"格式化预览: {result.get('formatted', 'N/A')[:100]}...")
        elif result.get('suggestions'):
            print(f"建议: {result.get('suggestions')}")
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 3: 测试 API 模式（普通聊天模式）
    print("\n3. 测试 API 模式（普通聊天模式）")
    print("-" * 40)
    
    try:
        result = api_client.chat("人参的功效")
        print(f"查询结果: {result.get('success')}")
        print(f"消息: {result.get('message', 'N/A')[:100]}...")
        if result.get('error'):
            print(f"错误: {result.get('error')}")
    except Exception as e:
        print(f"[ERROR] API 调用失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_herb_query_mode()

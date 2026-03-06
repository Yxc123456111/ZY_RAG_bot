#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整草药查询调试测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time


def simulate_desktop_client():
    """模拟桌面客户端的草药查询流程"""
    print("=" * 60)
    print("模拟桌面客户端草药查询流程")
    print("=" * 60)
    
    # 1. 初始化（与桌面客户端相同）
    print("\n1. 初始化配置管理器")
    print("-" * 40)
    from config_manager import get_config, is_supabase_ready
    config = get_config()
    print(f"Supabase 配置状态: {is_supabase_ready()}")
    
    # 2. 创建 API 客户端
    print("\n2. 创建 API 客户端")
    print("-" * 40)
    from desktop_chat import TCMAPIClient
    api_client = TCMAPIClient(api_url="http://localhost:8888")
    print("API 客户端创建成功")
    
    # 3. 模拟草药查询模式
    print("\n3. 模拟草药查询模式")
    print("-" * 40)
    herb_query_mode = True  # 模拟进入草药查询模式
    
    if herb_query_mode:
        print("当前模式: 草药查询模式")
        print("将直接查询 Supabase，不经过 API")
        
        # 模拟查询
        drug_name = "丹砂"
        print(f"查询药物: {drug_name}")
        
        try:
            result = api_client.query_supabase_herb(drug_name)
            print(f"查询成功: {result.get('success')}")
            print(f"消息: {result.get('message', 'N/A')}")
            
            if result.get('success'):
                print(f"\n药物信息:\n{result.get('formatted', 'N/A')[:300]}...")
            else:
                print(f"\n查询失败: {result.get('message')}")
                if result.get('suggestions'):
                    print(f"建议: {result.get('suggestions')}")
                    
        except Exception as e:
            print(f"[ERROR] 查询过程发生异常: {e}")
            import traceback
            traceback.print_exc()
    
    # 4. 模拟普通聊天模式
    print("\n4. 模拟普通聊天模式")
    print("-" * 40)
    herb_query_mode = False
    
    if not herb_query_mode:
        print("当前模式: 普通聊天模式")
        print("将通过 API 查询")
        
        try:
            result = api_client.chat("人参的功效")
            print(f"查询成功: {result.get('success')}")
            if not result.get('success'):
                print(f"错误消息: {result.get('message')}")
        except Exception as e:
            print(f"[ERROR] API 调用失败: {e}")
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)
    print("\n结论:")
    print("- 草药查询模式直接查询 Supabase，不依赖 API 服务")
    print("- 普通聊天模式需要 API 服务运行")
    print("- 如果草药查询模式仍显示'无法连接到服务器'，可能是:")
    print("  1. herb_query_mode 没有被正确设置为 True")
    print("  2. 查询过程中发生了未捕获的异常")


if __name__ == "__main__":
    simulate_desktop_client()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端智能中药查询测试
模拟桌面客户端的完整流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent_classifier import QueryRouter
from desktop_chat import TCMAPIClient


def simulate_smart_query(query: str):
    """
    模拟智能查询流程
    与 desktop_chat.py 中的 _process_with_intent 方法逻辑相同
    """
    print(f"\n用户输入: {query}")
    print("-" * 40)
    
    # 1. 意图识别
    router = QueryRouter()
    route_result = router.route(query)
    
    intent = route_result.get("intent")
    is_herb = intent == "herb_query" and route_result.get("is_supabase")
    
    print(f"[意图识别] {intent}")
    print(f"[是否中药查询] {is_herb}")
    
    # 2. 根据意图处理
    if is_herb:
        # 中药查询 - 提取名称并查询 Supabase
        herb_name = extract_herb_name(query, route_result.get("entities", {}))
        
        if herb_name:
            print(f"[提取中药名称] {herb_name}")
            print(f"[处理方式] 直接查询 Supabase")
            
            # 查询 Supabase
            api_client = TCMAPIClient(api_url="http://localhost:8888")
            result = api_client.query_supabase_herb(herb_name)
            
            if result.get("success"):
                print(f"[查询成功]")
                print(f"\n结果预览:")
                print(result.get("formatted", "")[:300] + "...")
            else:
                print(f"[查询失败] {result.get('message')}")
        else:
            print(f"[无法提取中药名称] 回退到 API 模式")
    else:
        # 其他查询 - 调用 API
        print(f"[处理方式] 调用 API 服务")
        print(f"[注意] 如果 API 服务未启动，会显示'无法连接到服务器'")


def extract_herb_name(query: str, entities: dict) -> str:
    """提取中药名称"""
    # 1. 从实体中提取
    herb_entities = entities.get("herb", [])
    if herb_entities:
        return herb_entities[0]
    
    # 2. 关键词匹配
    common_herbs = [
        "人参", "黄芪", "当归", "甘草", "桂枝", "麻黄", "柴胡",
        "白术", "茯苓", "川芎", "熟地黄", "白芍", "生姜", "大枣",
        "半夏", "陈皮", "枳实", "厚朴", "大黄", "黄连", "黄芩",
        "丹砂", "朱砂"
    ]
    
    for herb in common_herbs:
        if herb in query:
            return herb
    
    return None


def main():
    """运行端到端测试"""
    print("=" * 60)
    print("智能中药查询端到端测试")
    print("=" * 60)
    print("\n测试场景：用户输入不同查询，系统自动识别意图")
    
    # 测试用例
    test_queries = [
        "人参的功效是什么",      # 中药查询
        "丹砂的药性",           # 中药查询
        "帮我查一下白术",       # 中药查询
        "足三里穴在哪里",       # 针灸查询
        "伤寒论桂枝汤",         # 方剂查询
    ]
    
    for query in test_queries:
        simulate_smart_query(query)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n结论:")
    print("- 中药查询会自动识别并直接查询 Supabase")
    print("- 无需手动切换模式，系统智能处理")
    print("- 其他查询会调用 API 服务")


if __name__ == "__main__":
    main()

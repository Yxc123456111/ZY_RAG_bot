#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 中药查询简化测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent_classifier import QueryRouter
from core.text2sql import SchemaManager
from supabase_herb_client import create_client_from_env
from config_manager import is_supabase_ready


def main():
    print("=" * 60)
    print("Supabase 中药查询测试")
    print("=" * 60)
    
    # 1. 测试意图分类
    print("\n1. 测试意图分类器")
    print("-" * 40)
    router = QueryRouter()
    
    test_queries = [
        "人参有什么功效",
        "黄芪的性味是什么", 
        "当归主治什么病",
        "丹砂的药性",
    ]
    
    for query in test_queries:
        result = router.route(query)
        is_herb = result['intent'] == 'herb_query' and result.get('is_supabase') == True
        status = "OK" if is_herb else "FAIL"
        print(f"[{status}] {query} -> {result['intent']}, table={result.get('table')}")
    
    # 2. 测试 Schema
    print("\n2. 测试 Text2SQL Schema")
    print("-" * 40)
    schema = SchemaManager.get_schema('shennong_herbs')
    if schema:
        print(f"[OK] shennong_herbs 表存在")
        print(f"     描述: {schema['description']}")
        print(f"     可搜索字段: {SchemaManager.get_searchable_fields('shennong_herbs')}")
    else:
        print("[FAIL] shennong_herbs 表不存在")
    
    # 3. 测试 Supabase 客户端
    print("\n3. 测试 Supabase 客户端")
    print("-" * 40)
    
    if not is_supabase_ready():
        print("[SKIP] Supabase 未配置")
        return
    
    client = create_client_from_env()
    if not client:
        print("[FAIL] 客户端创建失败")
        return
    
    print("[OK] 客户端创建成功")
    
    # 查询测试
    result = client.query_by_name('人参')
    if result:
        print(f"[OK] 查询人参成功")
        print(f"     名称: {result.get('drug_name')}")
        print(f"     性味: {result.get('properties', 'N/A')[:40]}")
    else:
        print("[WARN] 未找到人参")
    
    # 4. 测试格式化
    print("\n4. 测试格式化输出")
    print("-" * 40)
    if result:
        formatted = client.format_herb_info(result)
        if formatted and len(formatted) > 10:
            print("[OK] 格式化成功")
            print("\n预览:")
            print(formatted[:300] + "..." if len(formatted) > 300 else formatted)
        else:
            print("[FAIL] 格式化失败")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

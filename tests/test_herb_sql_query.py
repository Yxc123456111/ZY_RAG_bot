#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中药 SQL 查询功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.herb_sql_generator import generate_herb_sql, extract_herb_names
from supabase_sql_executor import execute_herb_sql


def test_keyword_extraction():
    """测试关键词提取"""
    print("=" * 60)
    print("测试中药关键词提取")
    print("=" * 60)
    
    test_cases = [
        ("人参的功效是什么", ["人参"]),
        ("帮我查一下白术", ["白术"]),
        ("苦菜的性味", ["苦菜"]),
        ("细辛有什么作用", ["细辛"]),
        ("人参和黄芪一起用", ["人参", "黄芪"]),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        result = extract_herb_names(query)
        if result == expected:
            status = "[OK]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
        print(f"{status} {query}")
        print(f"    期望: {expected}, 实际: {result}")
    
    print(f"\n总计: {passed}/{passed+failed} 通过")
    return failed == 0


def test_sql_generation():
    """测试 SQL 生成"""
    print("\n" + "=" * 60)
    print("测试 SQL 生成")
    print("=" * 60)
    
    test_cases = [
        "人参的功效",
        "帮我查一下白术",
        "苦菜",
    ]
    
    for query in test_cases:
        sql_query = generate_herb_sql(query)
        if sql_query:
            print(f"\n查询: {query}")
            print(f"  提取的中药: {sql_query.herb_names}")
            print(f"  SQL: {sql_query.sql}")
            print(f"  参数: {sql_query.params}")
            print(f"  说明: {sql_query.explanation}")
        else:
            print(f"\n[FAIL] {query} - 无法生成 SQL")
    
    return True


def test_sql_execution():
    """测试 SQL 执行"""
    print("\n" + "=" * 60)
    print("测试 SQL 执行")
    print("=" * 60)
    
    test_cases = [
        "人参",
        "白术",
        "苦菜",
        "细辛",
    ]
    
    for query in test_cases:
        print(f"\n查询: {query}")
        result = execute_herb_sql(query)
        
        print(f"  成功: {result.get('success')}")
        print(f"  提取的中药: {result.get('extracted_herbs')}")
        print(f"  SQL: {result.get('sql')}")
        print(f"  说明: {result.get('explanation')}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            if isinstance(data, list):
                data = data[0]
            print(f"  药物名称: {data.get('drug_name')}")
            print(f"  性味: {data.get('properties', 'N/A')[:50]}...")
        else:
            print(f"  错误: {result.get('error', result.get('message', '未知错误'))}")
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("中药 SQL 查询功能测试")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("关键词提取", test_keyword_extraction()))
    except Exception as e:
        print(f"[ERROR] 关键词提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("关键词提取", False))
    
    try:
        results.append(("SQL 生成", test_sql_generation()))
    except Exception as e:
        print(f"[ERROR] SQL 生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("SQL 生成", False))
    
    try:
        results.append(("SQL 执行", test_sql_execution()))
    except Exception as e:
        print(f"[ERROR] SQL 执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("SQL 执行", False))
    
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

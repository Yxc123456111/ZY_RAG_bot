#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中药关键词提取功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.herb_sql_generator import extract_herb_names


def test_extraction():
    """测试关键词提取"""
    print("=" * 60)
    print("测试中药关键词提取")
    print("=" * 60)
    
    test_cases = [
        ("人参", ["人参"]),
        ("人参的功效是什么", ["人参"]),
        ("帮我查一下白术", ["白术"]),
        ("苦菜的性味", ["苦菜"]),
        ("细辛有什么作用", ["细辛"]),
        ("丹砂的药性", ["丹砂"]),
        ("酸枣仁的主治", ["酸枣仁"]),
        ("白胶和干漆", ["白胶", "干漆"]),
        ("人参和黄芪一起用", ["人参", "黄芪"]),
        ("我想了解茯苓", ["茯苓"]),
        ("黄连、黄芩、黄柏的区别", ["黄连", "黄芩", "黄柏"]),
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
        print(f"    期望: {expected}")
        print(f"    实际: {result}")
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{passed+failed} 通过")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = test_extraction()
    sys.exit(0 if success else 1)

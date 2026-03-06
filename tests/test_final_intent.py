#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终意图测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent_classifier import QueryRouter


def test_final():
    """最终测试"""
    print("=" * 60)
    print("最终意图识别测试")
    print("=" * 60)
    
    router = QueryRouter()
    
    # 测试各种查询
    tests = [
        ("帮我查一下白术", "herb_query"),
        ("白术", "herb_query"),
        ("人参的功效", "herb_query"),
        ("苦菜", "herb_query"),
        ("细辛", "herb_query"),
        ("酸枣仁", "herb_query"),
        ("白胶", "herb_query"),
        ("干漆", "herb_query"),
        ("足三里穴在哪里", "acupuncture_query"),
        ("伤寒论桂枝汤", "shanghan_query"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected in tests:
        result = router.route(query)
        actual = result['intent']
        
        if actual == expected:
            status = "[OK]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
        
        print(f"{status} {query} -> {actual}")
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{passed+failed} 通过")
    if failed > 0:
        print(f"失败: {failed}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = test_final()
    sys.exit(0 if success else 1)

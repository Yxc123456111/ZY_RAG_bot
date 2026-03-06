#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试意图路由功能
验证在普通聊天模式下自动识别中药查询意图
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent_classifier import QueryRouter


def test_intent_routing():
    """测试意图路由"""
    print("=" * 60)
    print("测试意图路由功能")
    print("=" * 60)
    
    router = QueryRouter()
    
    # 测试用例
    test_cases = [
        # (查询, 期望意图, 期望是否中药查询)
        ("人参的功效是什么", "herb_query", True),
        ("黄芪的性味", "herb_query", True),
        ("当归主治什么病", "herb_query", True),
        ("丹砂的药性", "herb_query", True),
        ("帮我查一下白术", "herb_query", True),
        ("甘草有什么禁忌", "herb_query", True),
        ("足三里穴在哪里", "acupuncture_query", False),
        ("伤寒论桂枝汤", "shanghan_query", False),
        ("金匮要略", "jinkui_query", False),
        ("我头痛发烧怎么办", "diagnosis", False),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_intent, expected_is_herb in test_cases:
        result = router.route(query)
        actual_intent = result['intent']
        actual_is_herb = actual_intent == 'herb_query' and result.get('is_supabase') == True
        
        intent_match = actual_intent == expected_intent
        herb_match = actual_is_herb == expected_is_herb
        
        if intent_match and herb_match:
            status = "[OK]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
        
        print(f"{status} {query}")
        print(f"    期望: {expected_intent}, 实际: {actual_intent}")
        print(f"    是否中药查询: 期望={expected_is_herb}, 实际={actual_is_herb}")
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{passed+failed} 通过")
    if failed > 0:
        print(f"失败: {failed}")
    print("=" * 60)
    
    return failed == 0


def test_herb_name_extraction():
    """测试中药名称提取"""
    print("\n" + "=" * 60)
    print("测试中药名称提取")
    print("=" * 60)
    
    # 模拟 _extract_herb_name 方法
    common_herbs = [
        "人参", "黄芪", "当归", "甘草", "桂枝", "麻黄", "柴胡",
        "白术", "茯苓", "川芎", "熟地黄", "白芍", "生姜", "大枣",
        "丹砂", "朱砂"
    ]
    
    test_cases = [
        ("人参的功效是什么", "人参"),
        ("丹砂的药性", "丹砂"),
        ("帮我查一下白术", "白术"),
        ("黄芪主治什么", "黄芪"),
        ("甘草有什么作用", "甘草"),
    ]
    
    def extract_herb_name(query):
        for herb in common_herbs:
            if herb in query:
                return herb
        return None
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        actual = extract_herb_name(query)
        if actual == expected:
            status = "[OK]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
        print(f"{status} {query} -> {actual}")
    
    print(f"\n总计: {passed}/{passed+failed} 通过")
    return failed == 0


if __name__ == "__main__":
    result1 = test_intent_routing()
    result2 = test_herb_name_extraction()
    
    if result1 and result2:
        print("\n所有测试通过!")
        sys.exit(0)
    else:
        print("\n部分测试失败")
        sys.exit(1)

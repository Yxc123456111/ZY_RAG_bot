#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试之前失败的药物名称是否被正确识别
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent_classifier import QueryRouter


def test_missing_herbs():
    """测试之前失败的药物"""
    print("=" * 60)
    print("测试之前失败的药物名称识别")
    print("=" * 60)
    
    router = QueryRouter()
    
    # 截图中失败的药物
    test_drugs = [
        ("苦菜", True),
        ("酸枣仁", True),
        ("酸枣", True),
        ("白胶", True),
        ("干漆", True),
        ("细辛", True),
    ]
    
    passed = 0
    failed = 0
    
    for drug, expected in test_drugs:
        result = router.route(drug)
        is_herb = result['intent'] == 'herb_query' and result.get('is_supabase')
        
        if is_herb == expected:
            status = "[OK]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
        
        print(f"{status} {drug}")
        print(f"    intent={result['intent']}, is_supabase={result.get('is_supabase')}")
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{passed+failed} 通过")
    if failed > 0:
        print(f"失败: {failed}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = test_missing_herbs()
    sys.exit(0 if success else 1)

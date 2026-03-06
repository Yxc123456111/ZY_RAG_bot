"""
意图识别模块测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent_classifier import IntentClassifier, IntentType, QueryRouter


def test_intent_classifier():
    """测试意图分类器"""
    classifier = IntentClassifier()
    
    test_cases = [
        ("足三里穴在哪里？", IntentType.ACUPUNCTURE_QUERY),
        ("人参有什么功效？", IntentType.HERB_QUERY),
        ("桂枝汤主治什么？", IntentType.SHANGHAN_QUERY),
        ("金匮要略中治疗胸痹的方剂", IntentType.JINKUI_QUERY),
        ("我最近头痛发热，怎么办？", IntentType.DIAGNOSIS),
        ("你好", IntentType.GREETING),
        ("今天天气怎么样", IntentType.UNKNOWN),
    ]
    
    print("=== 意图识别测试 ===\n")
    
    correct = 0
    for query, expected in test_cases:
        result = classifier.classify(query)
        status = "[OK]" if result.intent == expected else "[FAIL]"
        print(f"{status} 查询: {query}")
        print(f"   预期: {expected.value}, 实际: {result.intent.value}")
        print(f"   置信度: {result.confidence:.3f}")
        print(f"   实体: {result.entities}")
        print()
        
        if result.intent == expected:
            correct += 1
    
    print(f"准确率: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.1f}%)")


def test_query_router():
    """测试查询路由器"""
    router = QueryRouter()
    
    test_queries = [
        "足三里穴的定位和主治",
        "桂枝汤的组成",
        "我最近失眠多梦",
    ]
    
    print("\n=== 查询路由测试 ===\n")
    
    for query in test_queries:
        result = router.route(query)
        print(f"查询: {query}")
        print(f"  意图: {result['intent']}")
        print(f"  需要SQL: {result['requires_sql']}")
        print(f"  需要RAG: {result['requires_rag']}")
        print(f"  表名: {result.get('table', 'N/A')}")
        print()


if __name__ == "__main__":
    test_intent_classifier()
    test_query_router()

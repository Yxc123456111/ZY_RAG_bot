"""
中医聊天机器人演示脚本
展示核心功能：意图识别、Text2SQL转换
"""

import sys
sys.path.insert(0, '.')

from core.intent_classifier import IntentClassifier, QueryRouter
from core.text2sql import Text2SQLConverter, SchemaManager


def demo_intent_classification():
    """演示意图识别"""
    print("=" * 60)
    print("DEMO 1: Intent Classification")
    print("=" * 60)
    
    classifier = IntentClassifier()
    
    test_queries = [
        "足三里穴在哪里？",
        "人参有什么功效？",
        "桂枝汤主治什么？",
        "金匮要略中治疗胸痹的方剂",
        "我最近头痛发热，怎么办？",
        "你好",
    ]
    
    for query in test_queries:
        result = classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"  Intent: {result.intent.value}")
        print(f"  Confidence: {result.confidence:.3f}")
        if result.entities:
            print(f"  Entities: {result.entities}")


def demo_text2sql():
    """演示Text2SQL转换"""
    print("\n" + "=" * 60)
    print("DEMO 2: Text2SQL Conversion")
    print("=" * 60)
    
    converter = Text2SQLConverter(use_llm=False)
    
    test_cases = [
        ("足三里穴的定位和主治是什么？", "acupoints"),
        ("人参有什么功效？", "herbs"),
        ("桂枝汤的组成和功效是什么？", "shanghan_formulas"),
        ("治疗胸痹的方剂", "jinkui_formulas"),
    ]
    
    for query, table in test_cases:
        result = converter.convert(query, table)
        print(f"\nQuery: {query}")
        print(f"Table: {table}")
        print(f"SQL: {result.sql}")
        print(f"Explanation: {result.explanation}")


def demo_query_routing():
    """演示查询路由"""
    print("\n" + "=" * 60)
    print("DEMO 3: Query Routing")
    print("=" * 60)
    
    router = QueryRouter()
    
    test_queries = [
        "足三里穴的定位和主治",
        "桂枝汤的组成",
        "我最近失眠多梦",
    ]
    
    for query in test_queries:
        result = router.route(query)
        print(f"\nQuery: {query}")
        print(f"  Intent: {result['intent']}")
        print(f"  Requires SQL: {result['requires_sql']}")
        print(f"  Requires RAG: {result['requires_rag']}")
        if result.get('table'):
            print(f"  Table: {result['table']}")


def demo_database_schema():
    """演示数据库Schema"""
    print("\n" + "=" * 60)
    print("DEMO 4: Database Schema")
    print("=" * 60)
    
    tables = ["acupoints", "herbs", "shanghan_formulas", "jinkui_formulas"]
    
    for table in tables:
        schema = SchemaManager.get_schema(table)
        searchable = SchemaManager.get_searchable_fields(table)
        print(f"\nTable: {table}")
        print(f"  Description: {schema['description']}")
        print(f"  Searchable Fields: {searchable}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("TCM Chatbot - Demo")
    print("=" * 60)
    
    demo_intent_classification()
    demo_text2sql()
    demo_query_routing()
    demo_database_schema()
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

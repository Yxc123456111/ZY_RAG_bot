"""
Text2SQL模块测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.text2sql import Text2SQLConverter, SchemaManager


def test_schema_manager():
    """测试Schema管理器"""
    print("=== Schema管理器测试 ===\n")
    
    tables = ["acupoints", "herbs", "shanghan_formulas", "jinkui_formulas"]
    
    for table in tables:
        schema = SchemaManager.get_schema(table)
        searchable = SchemaManager.get_searchable_fields(table)
        print(f"表: {table}")
        print(f"  描述: {schema['description']}")
        print(f"  可搜索字段: {searchable}")
        print()


def test_text2sql():
    """测试Text2SQL转换"""
    converter = Text2SQLConverter(use_llm=False)
    
    test_cases = [
        ("足三里穴在哪里？", "acupoints"),
        ("人参有什么功效？", "herbs"),
        ("桂枝汤主治什么？", "shanghan_formulas"),
        ("治疗胸痹的方剂", "jinkui_formulas"),
    ]
    
    print("=== Text2SQL转换测试 ===\n")
    
    for query, table in test_cases:
        result = converter.convert(query, table)
        print(f"查询: {query}")
        print(f"表: {table}")
        print(f"SQL: {result.sql}")
        print(f"说明: {result.explanation}")
        print(f"置信度: {result.confidence}")
        print()


if __name__ == "__main__":
    test_schema_manager()
    test_text2sql()

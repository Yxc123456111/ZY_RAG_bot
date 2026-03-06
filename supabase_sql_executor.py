#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase SQL 执行器
通过 SQL 查询语句查询 Supabase 数据库
"""

import requests
from typing import Dict, List, Optional, Any
from urllib.parse import quote

from config_manager import get_config
from core.herb_sql_generator import HerbSQLQuery, generate_herb_sql, generate_fuzzy_herb_sql


class SupabaseSQLExecutor:
    """
    Supabase SQL 执行器
    使用 PostgREST 协议执行 SQL 查询
    """
    
    def __init__(self, project_url: str, api_key: str):
        """
        初始化 SQL 执行器
        
        Args:
            project_url: Supabase Project URL
            api_key: Supabase API Key (service_role key 或 anon key)
        """
        self.project_url = project_url.rstrip('/')
        self.api_key = api_key
        self.api_url = f"{self.project_url}/rest/v1"
        
        # 请求头
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def execute(self, sql_query: HerbSQLQuery) -> Dict:
        """
        执行 SQL 查询
        
        Args:
            sql_query: SQL 查询对象
            
        Returns:
            查询结果字典
        """
        try:
            # 解析 SQL 并构造 PostgREST 请求
            # PostgREST 不支持直接执行 SQL，需要使用查询参数
            
            # 简化处理：根据 SQL 类型构造请求
            if "drug_name = :herb_name" in sql_query.sql:
                # 精确查询
                herb_name = sql_query.params.get("herb_name")
                return self._query_by_name(herb_name)
            elif "drug_name ILIKE" in sql_query.sql:
                # 模糊查询
                pattern = sql_query.params.get("pattern", "").replace("%", "")
                return self._fuzzy_search(pattern)
            else:
                return {
                    "success": False,
                    "error": "不支持的 SQL 类型",
                    "sql": sql_query.sql
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql_query.sql
            }
    
    def _query_by_name(self, drug_name: str) -> Dict:
        """精确查询药物"""
        try:
            url = f"{self.api_url}/shennong_herbs"
            params = {
                "drug_name": f"eq.{drug_name}",
                "limit": "1"
            }
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        "success": True,
                        "data": data[0],
                        "count": 1,
                        "sql": f"SELECT * FROM shennong_herbs WHERE drug_name = '{drug_name}'"
                    }
                else:
                    return {
                        "success": False,
                        "error": "NOT_FOUND",
                        "message": f"未找到药物 '{drug_name}'",
                        "sql": f"SELECT * FROM shennong_herbs WHERE drug_name = '{drug_name}'"
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP_{response.status_code}",
                    "message": response.text,
                    "sql": f"SELECT * FROM shennong_herbs WHERE drug_name = '{drug_name}'"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": "EXCEPTION",
                "message": str(e)
            }
    
    def _fuzzy_search(self, keyword: str) -> Dict:
        """模糊搜索药物"""
        try:
            url = f"{self.api_url}/shennong_herbs"
            params = {
                "drug_name": f"ilike.*{keyword}*",
                "limit": "10"
            }
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "count": len(data),
                    "sql": f"SELECT * FROM shennong_herbs WHERE drug_name ILIKE '%{keyword}%'"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP_{response.status_code}",
                    "message": response.text
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": "EXCEPTION",
                "message": str(e)
            }
    
    def query_by_sql(self, sql_query: HerbSQLQuery) -> Dict:
        """
        通过 SQL 对象查询
        
        Args:
            sql_query: SQL 查询对象
            
        Returns:
            查询结果字典
        """
        return self.execute(sql_query)


def execute_herb_sql(query_text: str) -> Dict:
    """
    便捷函数：根据用户输入执行中药查询
    
    Args:
        query_text: 用户查询文本
        
    Returns:
        查询结果字典
    """
    # 获取配置
    config = get_config()
    url = config.get('SUPABASE_URL', '')
    key = config.get('SUPABASE_KEY', '')
    
    if not url or not key:
        return {
            "success": False,
            "error": "SUPABASE_URL 和 SUPABASE_KEY 未配置"
        }
    
    # 生成 SQL
    sql_query = generate_herb_sql(query_text)
    
    if not sql_query:
        # 尝试模糊查询
        sql_query = generate_fuzzy_herb_sql(query_text)
        if not sql_query:
            return {
                "success": False,
                "error": "无法从查询中提取中药名称"
            }
    
    # 执行查询
    executor = SupabaseSQLExecutor(url, key)
    result = executor.execute(sql_query)
    
    # 添加 SQL 信息
    result['sql'] = sql_query.sql
    result['explanation'] = sql_query.explanation
    result['extracted_herbs'] = sql_query.herb_names
    
    return result


# 测试代码
if __name__ == "__main__":
    # 测试
    test_queries = [
        "人参的功效",
        "帮我查一下白术",
        "苦菜的性味",
        "细辛有什么作用"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")
        
        result = execute_herb_sql(query)
        
        print(f"提取的中药: {result.get('extracted_herbs')}")
        print(f"SQL: {result.get('sql')}")
        print(f"说明: {result.get('explanation')}")
        print(f"成功: {result.get('success')}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            if isinstance(data, list):
                data = data[0]
            print(f"药物名称: {data.get('drug_name')}")
            print(f"性味: {data.get('properties', 'N/A')[:50]}...")

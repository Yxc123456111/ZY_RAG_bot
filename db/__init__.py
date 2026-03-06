#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块
统一使用 Supabase 进行关系型数据库查询
"""

from .supabase_client import (
    SupabaseClient,
    SupabaseHerbClient,  # 兼容性别名
    QueryResult,
    create_supabase_client,
    create_client_from_env,  # 兼容性别名
)

__all__ = [
    "SupabaseClient",
    "SupabaseHerbClient",
    "QueryResult",
    "create_supabase_client",
    "create_client_from_env",
]

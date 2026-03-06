#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接测试 Supabase REST API 连接"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip('"')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip('"')

print("=" * 50)
print("Supabase 连接测试")
print("=" * 50)
print(f"URL: {SUPABASE_URL}")
print(f"KEY (前20位): {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "KEY: 未设置")
print()

# 测试 API 调用
api_url = f"{SUPABASE_URL}/rest/v1/shennong_herbs"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

# 测试1: 简单查询
print("测试1: 查询所有数据 (limit=1)")
params = {"limit": "1"}
try:
    resp = requests.get(api_url, headers=headers, params=params, timeout=10)
    print(f"  状态码: {resp.status_code}")
    print(f"  响应: {resp.text[:200]}..." if len(resp.text) > 200 else f"  响应: {resp.text}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  返回数据条数: {len(data)}")
except Exception as e:
    print(f"  错误: {e}")

print()

# 测试2: 按药名查询
print("测试2: 查询 '丹砂'")
params = {"drug_name": "eq.丹砂", "limit": "1"}
try:
    resp = requests.get(api_url, headers=headers, params=params, timeout=10)
    print(f"  状态码: {resp.status_code}")
    print(f"  响应: {resp.text[:200]}..." if len(resp.text) > 200 else f"  响应: {resp.text}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  返回数据条数: {len(data)}")
except Exception as e:
    print(f"  错误: {e}")

print()
print("=" * 50)
print("诊断建议:")
print("- 如果状态码是 401/403: 密钥权限不足，需要更换为 anon key")
print("- 如果返回空数组 []: 表存在但无数据或RLS限制")
print("- 如果状态码是 404: 表名错误或表不存在")
print("=" * 50)

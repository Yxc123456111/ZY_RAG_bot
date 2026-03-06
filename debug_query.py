#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试草药查询问题
"""

import requests
import urllib.parse

SUPABASE_URL = "https://urxupwzffnpexsgquqzz.supabase.co"
SUPABASE_KEY = "sb_publishable_MT_RSVcH8wq4lNHcNQwLJw_zDUPCOQL"

def test_query():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    drug_name = "丹砂"
    
    print("=" * 60)
    print(f"测试查询: {drug_name}")
    print("=" * 60)
    
    # 方法1: 使用 ilike 模糊查询（推荐）
    print("\n方法1: 使用 ilike 模糊查询")
    url = f"{SUPABASE_URL}/rest/v1/shennong_herbs"
    params = {
        "drug_name": f"ilike.{drug_name}",
        "limit": "5"
    }
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"找到 {len(data)} 条记录")
            for item in data:
                print(f"  - {item.get('drug_name')}")
        else:
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # 方法2: 使用 eq 精确查询（需要URL编码）
    print("\n方法2: 使用 eq 精确查询（URL编码）")
    encoded_name = urllib.parse.quote(drug_name)
    params2 = {
        "drug_name": f"eq.{encoded_name}",
        "limit": "1"
    }
    
    print(f"Encoded: {encoded_name}")
    print(f"Params: {params2}")
    
    try:
        response = requests.get(url, headers=headers, params=params2, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"找到 {len(data)} 条记录")
            for item in data:
                print(f"  - {item.get('drug_name')}")
        else:
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # 方法3: 获取所有数据（查看实际存储的名称）
    print("\n方法3: 查看数据库中的实际数据")
    params3 = {"limit": "10"}
    
    try:
        response = requests.get(url, headers=headers, params=params3, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"前10条记录:")
            for item in data:
                name = item.get('drug_name', '')
                print(f"  - '{name}' (长度: {len(name)})")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_query()

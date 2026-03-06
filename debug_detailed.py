#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试查询过程
"""

import requests

SUPABASE_URL = "https://urxupwzffnpexsgquqzz.supabase.co"
SUPABASE_KEY = "sb_publishable_MT_RSVcH8wq4lNHcNQwLJw_zDUPCOQL"

def debug_query():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/shennong_herbs"
    
    # 1. 先获取所有数据看看
    print("Step 1: 获取所有数据")
    params = {"limit": "20"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total records: {len(data)}")
            print("\nFirst 5 records:")
            for i, item in enumerate(data[:5], 1):
                name = item.get('drug_name', 'N/A')
                print(f"  {i}. '{name}'")
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. 测试精确查询
    print("\nStep 2: 测试精确查询 (eq)")
    drug = "丹砂"
    params2 = {"drug_name": f"eq.{drug}", "limit": "1"}
    
    try:
        response = requests.get(url, headers=headers, params=params2, timeout=10)
        print(f"Query: {drug}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found: {len(data)} records")
            for item in data:
                print(f"  - {item.get('drug_name')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. 测试模糊查询 (ilike)
    print("\nStep 3: 测试模糊查询 (ilike)")
    params3 = {"drug_name": f"ilike.%丹%", "limit": "5"}
    
    try:
        response = requests.get(url, headers=headers, params=params3, timeout=10)
        print(f"Query: ilike.%丹%")
        print(f"Status: {response.status_code}")
        print(f"URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found: {len(data)} records")
            for item in data:
                print(f"  - {item.get('drug_name')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_query()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将本地 CSV 数据导入到 Supabase
"""

import csv
import requests
import json
import sys

SUPABASE_URL = "https://urxupwzffnpexsgquqzz.supabase.co"
SUPABASE_KEY = "sb_publishable_MT_RSVcH8wq4lNHcNQwLJw_zDUPCOQL"
CSV_FILE = "data/shennong_herbs_clean.csv"

def import_data():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{SUPABASE_URL}/rest/v1/shennong_herbs"
    
    print("Reading CSV file...")
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            records = list(reader)
        
        print(f"Found {len(records)} records in CSV")
        
        if not records:
            print("No data to import!")
            return
        
        # 获取所有可能的字段
        all_fields = set()
        for record in records:
            all_fields.update(record.keys())
        
        # 填充缺失字段为空字符串，确保所有记录结构一致
        for record in records:
            for field in all_fields:
                if field not in record:
                    record[field] = ""
        
        # 单条插入（更可靠）
        total = len(records)
        imported = 0
        failed = 0
        
        for i, record in enumerate(records, 1):
            # 清理数据（移除source_file等不需要的字段）
            cleaned = {k: v for k, v in record.items() if v and v.strip() and k != 'source_file'}
            
            # 如果没有药物名称，跳过
            if not cleaned.get('drug_name'):
                continue
            
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=cleaned,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    imported += 1
                    if i % 20 == 0:
                        print(f"Imported {i}/{total} records...")
                else:
                    failed += 1
                    if failed <= 3:  # 只显示前3个错误
                        print(f"Error on record {i} ({cleaned.get('drug_name')}): HTTP {response.status_code}")
                        print(response.text[:200])
                    elif failed == 4:
                        print("... (more errors hidden)")
                        
            except Exception as e:
                failed += 1
                if failed <= 3:
                    print(f"Error on record {i}: {e}")
        
        print(f"\nImport complete!")
        print(f"  Successfully imported: {imported}")
        print(f"  Failed: {failed}")
        
        # 验证
        print("\nVerifying...")
        response = requests.get(
            url,
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            params={"limit": "5"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Database now has {len(data)} records (sampled)")
            for item in data:
                print(f"  - {item.get('drug_name', 'N/A')}")
                
    except FileNotFoundError:
        print(f"CSV file not found: {CSV_FILE}")
        print("Please run: python scripts/extract_herbs.py first")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import_data()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Supabase 数据库状态并提供导入指导
"""

import requests
import json

SUPABASE_URL = "https://urxupwzffnpexsgquqzz.supabase.co"
SUPABASE_KEY = "sb_publishable_MT_RSVcH8wq4lNHcNQwLJw_zDUPCOQL"

def check_database():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("Supabase 数据库状态检查")
    print("=" * 60)
    
    # 检查表是否存在并获取记录数
    url = f"{SUPABASE_URL}/rest/v1/shennong_herbs"
    
    try:
        # 获取总数（不使用limit）
        response = requests.get(url, headers=headers, params={"select": "count"}, timeout=10)
        print(f"\n表 shennong_herbs 状态:")
        print(f"  HTTP 状态: {response.status_code}")
        
        if response.status_code == 200:
            # 尝试获取所有数据
            response2 = requests.get(url, headers=headers, params={"limit": "100"}, timeout=10)
            data = response2.json()
            print(f"  记录数量: {len(data)}")
            
            if len(data) == 0:
                print("\n  ⚠️  警告: 数据库表为空！")
                print("\n  需要将数据导入到 Supabase 数据库中。")
                show_import_instructions()
            else:
                print(f"\n  ✓ 数据库正常，包含 {len(data)} 条记录")
                print("\n  部分记录预览:")
                for item in data[:5]:
                    print(f"    - {item.get('drug_name', 'N/A')}")
        elif response.status_code == 404:
            print("\n  ✗ 错误: 表不存在")
            show_create_table_instructions()
        else:
            print(f"\n  ✗ 错误: {response.text[:200]}")
            
    except Exception as e:
        print(f"\n  ✗ 连接错误: {e}")

def show_import_instructions():
    print("\n" + "=" * 60)
    print("数据导入步骤")
    print("=" * 60)
    print("""
方法1: 使用 Supabase Dashboard (推荐)
1. 登录 https://app.supabase.io
2. 进入项目: urxupwzffnpexsgquqzz
3. 点击左侧 "Table Editor"
4. 点击 "New Table" -> "Import Data from CSV"
5. 选择文件: data/shennong_herbs_clean.csv
6. 表名设为: shennong_herbs
7. 点击 "Import"

方法2: 使用 SQL 导入
1. 在 Supabase Dashboard 中打开 "SQL Editor"
2. 执行以下 SQL:

   CREATE TABLE IF NOT EXISTS shennong_herbs (
       id SERIAL PRIMARY KEY,
       drug_name VARCHAR(100),
       original_text TEXT,
       origin TEXT,
       indications TEXT,
       properties TEXT,
       dosage TEXT,
       contraindications TEXT,
       other1 TEXT, other1_name VARCHAR(50),
       other2 TEXT, other2_name VARCHAR(50),
       other3 TEXT, other3_name VARCHAR(50),
       other4 TEXT, other4_name VARCHAR(50),
       other5 TEXT, other5_name VARCHAR(50),
       other6 TEXT, other6_name VARCHAR(50),
       other7 TEXT, other7_name VARCHAR(50),
       other8 TEXT, other8_name VARCHAR(50),
       other9 TEXT, other9_name VARCHAR(50),
       other10 TEXT, other10_name VARCHAR(50),
       other11 TEXT, other11_name VARCHAR(50)
   );

3. 然后使用 Supabase 的 Import 功能导入 CSV

方法3: 使用 Python 脚本批量插入
""")
    
    # 检查本地数据文件
    import os
    csv_file = "data/shennong_herbs_clean.csv"
    if os.path.exists(csv_file):
        print(f"✓ 本地数据文件存在: {csv_file}")
        print(f"  文件大小: {os.path.getsize(csv_file)} bytes")
    else:
        print(f"✗ 本地数据文件不存在: {csv_file}")
        print("  请先运行: python scripts/extract_herbs.py")

def show_create_table_instructions():
    print("""
表不存在，请先创建表:

1. 在 Supabase Dashboard 中打开 "SQL Editor"
2. 执行:

   CREATE TABLE shennong_herbs (
       id SERIAL PRIMARY KEY,
       drug_name VARCHAR(100) NOT NULL,
       original_text TEXT,
       origin TEXT,
       indications TEXT,
       properties TEXT,
       dosage TEXT,
       contraindications TEXT,
       other1 TEXT, other1_name VARCHAR(50),
       other2 TEXT, other2_name VARCHAR(50),
       other3 TEXT, other3_name VARCHAR(50),
       other4 TEXT, other4_name VARCHAR(50),
       other5 TEXT, other5_name VARCHAR(50),
       other6 TEXT, other6_name VARCHAR(50),
       other7 TEXT, other7_name VARCHAR(50),
       other8 TEXT, other8_name VARCHAR(50),
       other9 TEXT, other9_name VARCHAR(50),
       other10 TEXT, other10_name VARCHAR(50),
       other11 TEXT, other11_name VARCHAR(50)
   );

3. 导入数据
""")

if __name__ == "__main__":
    check_database()

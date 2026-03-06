#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Supabase 同步中药列表到本地
"""

import requests
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def get_all_drug_names():
    """从 Supabase 获取所有药物名称"""
    # 从环境变量读取配置
    from dotenv import load_dotenv
    load_dotenv()
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("错误: 请设置 SUPABASE_URL 和 SUPABASE_KEY 环境变量")
        return []
    
    # 请求所有药物名称
    resp = requests.get(
        f'{url}/rest/v1/shennong_herbs',
        headers={'apikey': key, 'Authorization': f'Bearer {key}'},
        params={'select': 'drug_name', 'limit': 1000},
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        drug_names = [d.get('drug_name', '') for d in data if d.get('drug_name')]
        return sorted(drug_names)
    else:
        print(f"查询失败: {resp.status_code}")
        return []

def update_herb_sql_generator(drug_names):
    """更新 herb_sql_generator.py 中的 COMMON_HERBS 列表"""
    file_path = Path(__file__).parent.parent / 'core' / 'herb_sql_generator.py'
    
    if not file_path.exists():
        print(f"错误: 文件不存在 {file_path}")
        return False
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 生成新的列表字符串
    new_list = "COMMON_HERBS = [\n"
    for name in drug_names:
        new_list += f"    '{name}',\n"
    new_list += "]"
    
    # 替换旧的列表（使用正则匹配）
    import re
    pattern = r"COMMON_HERBS = \[[\s\S]*?\]"
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_list, content)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"已更新 {file_path}")
        print(f"药物数量: {len(drug_names)}")
        return True
    else:
        print("错误: 无法找到 COMMON_HERBS 列表")
        return False

if __name__ == "__main__":
    print("正在从 Supabase 同步中药列表...")
    drug_names = get_all_drug_names()
    
    if drug_names:
        print(f"获取到 {len(drug_names)} 个药物名称")
        update_herb_sql_generator(drug_names)
    else:
        print("同步失败")

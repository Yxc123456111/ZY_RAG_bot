#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""显示提取结果的示例"""

import json

with open('data/shennong_herbs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 显示前3种药物的摘要
for i, drug in enumerate(data[:3], 1):
    print(f'=== {i}. {drug["drug_name"]} ===')
    print(f'本经原文: {drug["original_text"][:80]}...')
    print(f'产地: {drug["origin"][:60]}...' if drug["origin"] else '产地: (空)')
    print(f'主治: {drug["indications"][:60]}...' if drug["indications"] else '主治: (空)')
    print(f'性味: {drug["properties"][:40]}...' if drug["properties"] else '性味: (空)')
    print(f'用量: {drug["dosage"][:40]}...' if drug["dosage"] else '用量: (空)')
    print(f'禁忌: {drug["contraindications"][:40]}...' if drug["contraindications"] else '禁忌: (空)')
    
    # 显示其他字段
    others = []
    j = 1
    while f'other{j}_name' in drug:
        name = drug.get(f'other{j}_name', '')
        if name:
            others.append(name)
        j += 1
    print(f'其他字段: {others}')
    print()

print(f"共提取 {len(data)} 种药物")

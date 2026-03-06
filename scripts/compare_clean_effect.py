#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比清理前后的效果
展示剔除 > 注释后的内容变化
"""

import json

def show_comparison():
    print("=" * 60)
    print("数据清理效果对比")
    print("=" * 60)
    print("\n清理规则：完全剔除以 '>' 开头的注释段落\n")
    
    # 读取新生成的JSON
    with open('data/shennong_herbs.json', 'r', encoding='utf-8') as f:
        drugs = json.load(f)
    
    # 展示前3种药物的对比
    for i, drug in enumerate(drugs[:3], 1):
        print(f"\n{'─' * 60}")
        print(f"【{i}. {drug['drug_name']}】")
        print(f"{'─' * 60}")
        
        # 本经原文
        print(f"\n[本经原文]（已清理）:")
        text = drug['original_text'][:200] + "..." if len(drug['original_text']) > 200 else drug['original_text']
        print(f"   {text}")
        
        # 产地
        if drug['origin']:
            print(f"\n[产地]:")
            print(f"   {drug['origin'][:100]}..." if len(drug['origin']) > 100 else f"   {drug['origin']}")
        
        # 主治
        if drug['indications']:
            print(f"\n[主治]:")
            print(f"   {drug['indications'][:100]}..." if len(drug['indications']) > 100 else f"   {drug['indications']}")
        
        # 统计其他字段
        others = []
        j = 1
        while f'other{j}_name' in drug:
            name = drug.get(f'other{j}_name', '')
            if name:
                others.append(name)
            j += 1
        
        if others:
            print(f"\n[其他字段]: {', '.join(others)}")
    
    print(f"\n{'=' * 60}")
    print(f"共处理 {len(drugs)} 种药物")
    print(f"{'=' * 60}")
    
    print("\n[OK] 清理后的文件:")
    print("   - data/shennong_herbs.json (新)")
    print("   - data/shennong_herbs_clean.csv (新)")
    print("   - data/shennong_herbs_schema.sql (建表语句)")
    
    print("\n[!] 注意：原 shennong_herbs.csv 文件被占用未更新")
    print("   请手动使用 shennong_herbs_clean.csv 或关闭占用程序后重新运行脚本")

if __name__ == "__main__":
    show_comparison()

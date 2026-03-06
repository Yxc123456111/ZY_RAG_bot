#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
神农本草经药物内容提取脚本
用于将markdown文件中的药物内容提取为JSON/CSV格式，便于导入Supabase数据库
"""

import os
import re
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional


# 字段映射（中文 -> 英文）
FIELD_MAPPING = {
    "药物名称": "drug_name",
    "本经原文": "original_text",
    "产地": "origin",
    "主治": "indications",
    "性味": "properties",
    "用量": "dosage",
    "禁忌": "contraindications",
}

# 需要提取的标准字段（按优先级顺序）
STANDARD_FIELDS = ["本经原文", "产地", "主治", "性味", "用量", "禁忌"]


def extract_drug_name(content: str) -> str:
    """提取药物名称（从标题行）"""
    # 匹配 ## 开头的标题
    match = re.search(r'^##\s*(.+?)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def extract_sections(content: str) -> Dict[str, str]:
    """提取所有 #### 【xxx】 标记的段落"""
    sections = {}
    
    # 匹配 #### 【字段名】 内容 的模式
    # 支持多个 #### 段落，直到下一个 #### 或文件结束
    pattern = r'####\s*【(.+?)】\s*\n(.*?)(?=\n####|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for field_name, field_content in matches:
        field_name = field_name.strip()
        # 清理内容：去除多余空白和引用符号 >
        field_content = clean_content(field_content)
        sections[field_name] = field_content
    
    return sections


def clean_content(content: str) -> str:
    """清理内容，完全剔除以 > 开头的注释段落"""
    lines = content.strip().split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # 完全跳过以 > 开头的注释行
        if line.startswith('>'):
            continue
        # 跳过分隔线
        elif line.startswith('---'):
            continue
        # 保留其他内容
        elif line:
            cleaned_lines.append(line)
    
    # 合并行并去除多余空行
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def parse_drug_file(file_path: Path) -> Dict:
    """解析单个药物文件"""
    content = file_path.read_text(encoding='utf-8')
    
    # 提取药物名称
    drug_name = extract_drug_name(content)
    
    # 提取各段落
    sections = extract_sections(content)
    
    # 构建结果字典
    result = {
        "drug_name": drug_name,
    }
    
    # 映射标准字段
    other_sections = []
    for cn_name, en_name in FIELD_MAPPING.items():
        if cn_name == "药物名称":
            continue
        if cn_name in sections:
            result[en_name] = sections[cn_name]
        else:
            result[en_name] = ""
    
    # 收集其他字段（非标准字段）
    for section_name, section_content in sections.items():
        if section_name not in STANDARD_FIELDS:
            other_sections.append({
                "name": section_name,
                "content": section_content
            })
    
    # 将其他字段按顺序命名为 other1, other2, ...
    for i, other in enumerate(other_sections, 1):
        result[f"other{i}"] = other["content"]
        result[f"other{i}_name"] = other["name"]
    
    return result


def get_all_drug_files(directory: Path) -> List[Path]:
    """获取所有药物文件（排除索引文件）"""
    files = []
    for file_path in sorted(directory.glob("*.md")):
        # 排除索引文件（如 0.上经.md）
        if not re.match(r'^\d+\.', file_path.name):
            continue
        if file_path.name.startswith("0."):
            continue
        files.append(file_path)
    return sorted(files, key=lambda x: int(re.search(r'^(\d+)', x.name).group(1)))


def extract_all_drugs(input_dir: str) -> List[Dict]:
    """提取目录中所有药物"""
    input_path = Path(input_dir)
    files = get_all_drug_files(input_path)
    
    drugs = []
    for file_path in files:
        try:
            drug_data = parse_drug_file(file_path)
            drug_data["source_file"] = file_path.name
            drugs.append(drug_data)
            print(f"[OK] 已提取: {drug_data['drug_name']}")
        except Exception as e:
            print(f"[FAIL] 提取失败 {file_path.name}: {e}")
    
    return drugs


def save_to_json(drugs: List[Dict], output_file: str):
    """保存为JSON文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(drugs, f, ensure_ascii=False, indent=2)
    print(f"\nJSON文件已保存: {output_file}")


def save_to_csv(drugs: List[Dict], output_file: str):
    """保存为CSV文件"""
    if not drugs:
        print("没有数据可保存")
        return
    
    # 获取所有可能的字段
    all_fields = set()
    for drug in drugs:
        all_fields.update(drug.keys())
    
    # 定义字段顺序（标准字段在前，other字段在后）
    standard_order = ["drug_name", "original_text", "origin", "indications", 
                      "properties", "dosage", "contraindications"]
    other_fields = sorted([f for f in all_fields if f.startswith("other") and not f.endswith("_name")])
    other_name_fields = sorted([f for f in all_fields if f.startswith("other") and f.endswith("_name")])
    remaining_fields = sorted([f for f in all_fields if f not in standard_order + other_fields + other_name_fields + ["source_file"]])
    
    fieldnames = standard_order + other_fields + other_name_fields + remaining_fields + ["source_file"]
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for drug in drugs:
            # 确保所有字段都存在
            row = {field: drug.get(field, "") for field in fieldnames}
            writer.writerow(row)
    
    print(f"CSV文件已保存: {output_file}")


def generate_sql_schema(max_others: int = 10) -> str:
    """生成Supabase/PostgreSQL建表语句"""
    sql = """-- 神农本草经药物表
CREATE TABLE shennong_herbs (
    id SERIAL PRIMARY KEY,
    drug_name VARCHAR(100) NOT NULL,           -- 药物名称
    original_text TEXT,                         -- 本经原文
    origin TEXT,                                -- 产地
    indications TEXT,                           -- 主治
    properties TEXT,                            -- 性味
    dosage TEXT,                                -- 用量
    contraindications TEXT,                     -- 禁忌
"""
    
    for i in range(1, max_others + 1):
        sql += f"    other{i} TEXT,                -- 其他{i}内容\n"
        sql += f"    other{i}_name VARCHAR(50),    -- 其他{i}名称\n"
    
    sql += """    source_file VARCHAR(100),                   -- 源文件
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_herbs_name ON shennong_herbs(drug_name);

-- 注释
COMMENT ON TABLE shennong_herbs IS '神农本草经上经药物数据';
"""
    return sql


def main():
    """主函数"""
    # 配置
    INPUT_DIRECTORY = "content/上经"
    OUTPUT_JSON = "data/shennong_herbs.json"
    OUTPUT_CSV = "data/shennong_herbs_clean.csv"
    OUTPUT_SQL = "data/shennong_herbs_schema.sql"
    
    # 确保输出目录存在
    os.makedirs("data", exist_ok=True)
    
    print("=" * 50)
    print("神农本草经药物内容提取")
    print("=" * 50)
    
    # 提取所有药物
    print(f"\n正在从 {INPUT_DIRECTORY} 提取药物数据...\n")
    drugs = extract_all_drugs(INPUT_DIRECTORY)
    
    print(f"\n共提取 {len(drugs)} 种药物")
    
    # 分析其他字段的数量
    max_others = 0
    for drug in drugs:
        others = [k for k in drug.keys() if k.startswith("other") and not k.endswith("_name")]
        max_others = max(max_others, len(others))
    print(f"最大其他字段数: {max_others}")
    
    # 保存为JSON
    save_to_json(drugs, OUTPUT_JSON)
    
    # 保存为CSV
    save_to_csv(drugs, OUTPUT_CSV)
    
    # 生成SQL建表语句
    sql = generate_sql_schema(max_others)
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write(sql)
    print(f"SQL建表语句已保存: {OUTPUT_SQL}")
    
    # 输出统计信息
    print("\n" + "=" * 50)
    print("提取统计")
    print("=" * 50)
    
    # 检查每种字段的填充情况
    field_stats = {}
    for drug in drugs:
        for key in drug.keys():
            if key not in ["source_file"]:
                if key not in field_stats:
                    field_stats[key] = 0
                if drug[key]:
                    field_stats[key] += 1
    
    print(f"\n{'字段名':<25} {'数量':<8} {'比例':<8}")
    print("-" * 50)
    for field, count in sorted(field_stats.items()):
        if not field.startswith("other") or field == "other1":
            percentage = count / len(drugs) * 100 if drugs else 0
            print(f"{field:<25} {count:<8} {percentage:.1f}%")
    
    other_fields_count = len([k for k in field_stats.keys() if k.startswith("other") and not k.endswith("_name")])
    print(f"\n其他字段总数: {other_fields_count}")
    
    print("\n" + "=" * 50)
    print("完成！输出文件:")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_CSV}")
    print(f"  - {OUTPUT_SQL}")
    print("=" * 50)


if __name__ == "__main__":
    main()

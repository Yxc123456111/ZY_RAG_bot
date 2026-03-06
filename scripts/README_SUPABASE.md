# 神农本草经数据提取与Supabase导入指南

## 提取结果概述

已成功从 `content/上经` 目录提取了 **142 种药物**的数据。

### 生成的文件

| 文件 | 说明 |
|------|------|
| `data/shennong_herbs.json` | JSON格式数据，包含完整内容 |
| `data/shennong_herbs.csv` | CSV格式数据，可直接导入Excel/数据库 |
| `data/shennong_herbs_schema.sql` | PostgreSQL/Supabase建表语句 |

### 字段说明

| 字段名 | 中文名 | 数据类型 | 说明 |
|--------|--------|----------|------|
| drug_name | 药物名称 | VARCHAR(100) | 主键，药物的中文名称 |
| original_text | 本经原文 | TEXT | 《神农本草经》原文记载 |
| origin | 产地 | TEXT | 药物产地信息 |
| indications | 主治 | TEXT | 主要治疗功效 |
| properties | 性味 | TEXT | 药物的性味归经 |
| dosage | 用量 | TEXT | 用法用量说明 |
| contraindications | 禁忌 | TEXT | 使用禁忌和注意事项 |
| other1 ~ other11 | 其他内容 | TEXT | 历代医家注解（别录、甄权、大明等）|
| other1_name ~ other11_name | 其他内容名称 | VARCHAR(50) | 对应other字段的标题名称 |
| source_file | 源文件 | VARCHAR(100) | 原始markdown文件名 |

---

## Supabase 导入步骤

### 方法一：使用SQL语句创建表

1. 登录 [Supabase Dashboard](https://app.supabase.io)
2. 进入 SQL Editor
3. 复制 `data/shennong_herbs_schema.sql` 中的内容
4. 粘贴并执行

### 方法二：使用CSV导入（推荐）

1. 打开 `data/shennong_herbs.csv`（使用Excel或文本编辑器）
2. 登录 Supabase Dashboard
3. 进入 **Table Editor** → **New Table**
4. 选择 **Import Data from CSV**
5. 上传CSV文件并映射字段

### 方法三：使用Python脚本导入

```python
import json
from supabase import create_client

# Supabase配置
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"

# 初始化客户端
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 加载数据
with open('data/shennong_herbs.json', 'r', encoding='utf-8') as f:
    drugs = json.load(f)

# 批量插入（每次100条）
batch_size = 100
for i in range(0, len(drugs), batch_size):
    batch = drugs[i:i+batch_size]
    # 删除source_file字段（可选）
    for drug in batch:
        drug.pop('source_file', None)
    
    result = supabase.table('shennong_herbs').insert(batch).execute()
    print(f"已导入 {i+len(batch)}/{len(drugs)}")

print("导入完成！")
```

---

## 数据结构示例

```json
{
  "drug_name": "丹砂",
  "original_text": "性味甘，微寒无毒，主治身体五脏百病...",
  "origin": "在我国四川湖南等山中。以辰州为最佳...",
  "indications": "丹砂为安神要药...",
  "properties": "",
  "dosage": "一般水飞用以拌合他药，单服时可用二，三分...",
  "contraindications": "丹砂只可生研水飞用。火炼则为水银而有毒...",
  "other1": "通血脉，止烦满，消渴...",
  "other1_name": "别录",
  "other2": "镇心，主抽风传尸痨...",
  "other2_name": "甄权",
  "other3": "润心肺，治疮痂息肉...",
  "other3_name": "大明",
  "other4": "入心镇怯，定魂除邪。",
  "other4_name": "灵贻",
  "other5": "取朱砂打碎，选去夹石...",
  "other5_name": "炮制",
  "source_file": "1.丹砂.md"
}
```

---

## 统计信息

| 字段 | 填充数量 | 填充率 |
|------|----------|--------|
| drug_name | 142 | 100.0% |
| original_text | 140 | 98.6% |
| origin | 129 | 90.8% |
| indications | 122 | 85.9% |
| properties | 124 | 87.3% |
| dosage | 119 | 83.8% |
| contraindications | 119 | 83.8% |
| other1 | 127 | 89.4% |

---

## 注意事项

1. **编码问题**：所有文件使用UTF-8编码，如果在Windows下查看有乱码，请使用支持UTF-8的编辑器（如VS Code、Notepad++）

2. **字段长度**：SQL脚本中的VARCHAR长度可以根据实际数据调整

3. **数据清洗**：如需进一步清洗数据（如去除引用说明），可修改 `extract_herbs.py` 中的 `clean_content` 函数

4. **中经、下经**：如需提取其他经卷，修改脚本中的 `INPUT_DIRECTORY` 变量

---

## 重新提取数据

```bash
python scripts/extract_herbs.py
```

脚本将自动：
- 扫描 `content/上经/*.md` 文件
- 提取所有药物信息
- 生成JSON、CSV和SQL文件
- 输出统计报告

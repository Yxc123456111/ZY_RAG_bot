# 神农本草经数据提取 - 清理版本

## 更新说明

本次提取已剔除所有以 `>` 开头的注释段落，仅保留正式的医药内容。

---

## 清理效果对比

### 原始文件内容示例（1.丹砂.md）

```markdown
## 丹砂

> 丹砂就是朱砂，大陆辰州的朱砂品质最好...

> 什么叫水飞？拿到朱砂原石...

#### 【本经原文】
性味甘，微寒无毒，主治身体五脏百病...

> 看本经原文，朱砂的性味是【甘，微寒】...

> 为什么说朱砂可以杀精魅、邪恶鬼？...

#### 【产地】
在我国四川湖南等山中...
```

### 清理后提取的内容

```json
{
  "drug_name": "丹砂",
  "original_text": "性味甘，微寒无毒，主治身体五脏百病，可以养精神安魂魄。益气明目，杀精魅邪恶鬼，久服通神明，不老能化为汞，畏磁石恶盐水，其色真珠光色如云母，可折者良。又名朱砂。",
  "origin": "在我国四川湖南等山中。以辰州为最佳，故又号辰砂，属石类。",
  "indications": "丹砂为安神要药。",
  ...
}
```

---

## 清理规则

| 规则 | 处理 |
|------|------|
| 以 `>` 开头的行 | **完全剔除** |
| 以 `---` 开头的行 | 剔除 |
| `#### 【xxx】` 标记的内容 | 保留正文，剔除内部的 `>` 注释 |
| 正式医药内容 | 保留 |

---

## 生成文件

| 文件 | 说明 |
|------|------|
| `data/shennong_herbs.json` | JSON格式，UTF-8编码 |
| `data/shennong_herbs_clean.csv` | CSV格式，UTF-8-BOM编码（可直接用Excel打开） |
| `data/shennong_herbs_schema.sql` | PostgreSQL/Supabase 建表语句 |

---

## 数据字段

| 字段名 | 中文名 | 说明 |
|--------|--------|------|
| drug_name | 药物名称 | 如：丹砂、人参等 |
| original_text | 本经原文 | 《神农本草经》原文 |
| origin | 产地 | 药物产地信息 |
| indications | 主治 | 主要功效 |
| properties | 性味 | 性味归经 |
| dosage | 用量 | 用法用量 |
| contraindications | 禁忌 | 禁忌事项 |
| other1~other11 | 其他内容 | 历代医家注解（别录、甄权、大明等） |
| other1_name~other11_name | 其他内容名称 | 对应other字段的标题 |

---

## 统计数据

- **药物总数**: 142 种
- **最大其他字段数**: 11 个
- **字段填充率**:
  - 药物名称: 100%
  - 本经原文: 98.6%
  - 产地: 90.8%
  - 主治: 85.9%
  - 性味: 87.3%
  - 用量: 83.8%
  - 禁忌: 83.8%

---

## Supabase 导入

### 方法1: SQL建表

在 Supabase SQL Editor 中执行 `data/shennong_herbs_schema.sql`

### 方法2: CSV导入

1. 打开 Supabase Dashboard
2. 进入 Table Editor → Import Data from CSV
3. 选择 `data/shennong_herbs_clean.csv`

---

## 重新提取

如需重新提取（比如源文件有更新）：

```bash
python scripts/extract_herbs.py
```

脚本会自动：
1. 扫描 `content/上经/*.md` 文件
2. 剔除所有 `>` 注释段落
3. 生成新的 JSON、CSV 和 SQL 文件

# 中药 SQL 查询功能说明

## 功能概述

根据用户输入的句子，语义提取中药名称关键字，通过调用 SQL 查询语句向 Supabase 数据库 `shennong_herbs` 表进行查询。

## 核心组件

### 1. `core/herb_sql_generator.py` - SQL 生成器

#### HerbKeywordExtractor（关键词提取器）
- 使用正则表达式从用户输入中提取中药名称
- 支持 400+ 种常见中药名称
- 按长度降序匹配，优先匹配长词

#### HerbSQLGenerator（SQL 生成器）
- 根据提取的中药名称生成 SQL 查询语句
- 支持精确查询（`=`）和模糊查询（`ILIKE`）
- 生成带参数的 SQL，防止 SQL 注入

**生成的 SQL 示例**：
```sql
-- 单个药物查询
SELECT * FROM shennong_herbs WHERE drug_name = :herb_name

-- 模糊查询
SELECT * FROM shennong_herbs WHERE drug_name ILIKE :pattern
```

### 2. `supabase_sql_executor.py` - SQL 执行器

#### SupabaseSQLExecutor
- 将 SQL 对象转换为 PostgREST 请求
- 执行查询并返回结果
- 支持错误处理和结果格式化

#### 执行流程
```
用户输入
    ↓
提取中药名称
    ↓
生成 SQL 语句
    ↓
转换为 PostgREST 参数
    ↓
调用 Supabase REST API
    ↓
返回查询结果
```

## 使用方式

### 在桌面客户端中使用

在默认聊天窗口下，输入任何包含中药名称的查询：

```
人参的功效是什么
```

系统会自动：
1. 提取关键词：人参
2. 生成 SQL：`SELECT * FROM shennong_herbs WHERE drug_name = '人参'`
3. 执行查询
4. 返回结果

### 直接使用代码

```python
from supabase_sql_executor import execute_herb_sql

# 执行查询
result = execute_herb_sql("帮我查一下白术")

# 查看结果
print(result['sql'])           # 生成的 SQL
print(result['extracted_herbs'])  # 提取的中药名称
print(result['data'])          # 查询数据
```

## 支持的中药

系统支持 400+ 种中药，包括但不限于：

- **补益类**：人参、黄芪、当归、白术、茯苓、甘草
- **清热类**：黄连、黄芩、黄柏、栀子、金银花、连翘
- **解表类**：麻黄、桂枝、柴胡、薄荷、防风、荆芥
- **祛湿类**：苍术、厚朴、藿香、砂仁、茯苓、泽泻
- **安神类**：酸枣仁、柏子仁、远志、合欢皮、龙骨、牡蛎
- **活血类**：川芎、丹参、红花、桃仁、益母草、牛膝
- **化痰类**：半夏、贝母、瓜蒌、竹茹、桔梗、杏仁
- **收涩类**：五味子、山茱萸、乌梅、诃子、肉豆蔻
- **其他**：丹砂、朱砂、细辛、苦菜、白胶、干漆

## 查询示例

### 示例 1：简单查询
```
用户输入：人参
提取关键词：人参
生成 SQL：SELECT * FROM shennong_herbs WHERE drug_name = '人参'
```

### 示例 2：自然语言查询
```
用户输入：帮我查一下白术的功效
提取关键词：白术
生成 SQL：SELECT * FROM shennong_herbs WHERE drug_name = '白术'
```

### 示例 3：模糊查询
```
用户输入：含有"参"字的药物
提取关键词：参
生成 SQL：SELECT * FROM shennong_herbs WHERE drug_name ILIKE '%参%'
```

## 技术特点

### 1. 语义提取
- 使用正则表达式匹配，而非简单字符串查找
- 支持多种表述方式："人参"、"人参的功效"、"帮我查一下人参"
- 自动去重和排序

### 2. SQL 安全
- 使用参数化查询，防止 SQL 注入
- 自动生成参数名，避免冲突

### 3. 错误处理
- 未找到药物时返回友好提示
- API 调用失败时返回详细错误信息
- 支持模糊搜索建议

## 文件结构

```
core/
  herb_sql_generator.py    - SQL 生成器
  intent_classifier.py     - 意图分类器

supabase_sql_executor.py   - SQL 执行器
supabase_herb_client.py    - 原有客户端

tests/
  test_herb_sql_query.py   - SQL 查询测试
  test_keyword_extraction.py - 关键词提取测试
```

## 测试验证

运行测试脚本：

```bash
# 测试 SQL 查询功能
python tests/test_herb_sql_query.py

# 测试关键词提取
python tests/test_keyword_extraction.py
```

## 与旧版本的区别

| 特性 | 旧版本 | 新版本 |
|------|--------|--------|
| 查询方式 | 直接调用 API | 生成 SQL 后执行 |
| 关键词提取 | 基于意图分类器 | 基于正则表达式匹配 |
| 可扩展性 | 固定关键词列表 | 可动态加载中药列表 |
| 查询语句 | 封装在客户端 | 可见的 SQL 语句 |
| 调试 | 较难追踪 | 可查看生成的 SQL |

## 优势

1. **语义理解**：能理解自然语言查询，不只是关键词匹配
2. **透明性**：可查看生成的 SQL 语句，便于调试
3. **安全性**：使用参数化查询，防止 SQL 注入
4. **可扩展性**：支持 400+ 种中药，易于扩展
5. **智能路由**：自动识别中药查询并直接查询数据库

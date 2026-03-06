# Supabase 中药查询功能配置指南

## 功能概述

桌面聊天客户端已集成 **Supabase 神农本草经查询** 功能，点击"中药查询"按钮即可通过 Supabase 数据库查询草药信息。

## 配置步骤

### 1. 准备 Supabase 数据库

#### 1.1 创建表结构

在 Supabase 中执行以下 SQL 创建草药数据表：

```sql
-- 神农本草经药物表
CREATE TABLE shennong_herbs (
    id SERIAL PRIMARY KEY,
    drug_name VARCHAR(100) NOT NULL,           -- 药物名称
    original_text TEXT,                         -- 本经原文
    origin TEXT,                                -- 产地
    indications TEXT,                           -- 主治
    properties TEXT,                            -- 性味
    dosage TEXT,                                -- 用量
    contraindications TEXT,                     -- 禁忌
    other1 TEXT,                                -- 其他1内容
    other1_name VARCHAR(50),                    -- 其他1名称
    other2 TEXT,
    other2_name VARCHAR(50),
    -- ... other3~other11 类似
    source_file VARCHAR(100),                   -- 源文件
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_herbs_name ON shennong_herbs(drug_name);
```

#### 1.2 导入数据

使用 `data/shennong_herbs_clean.csv` 文件导入数据：

1. 登录 Supabase Dashboard
2. 进入 **Table Editor**
3. 点击 **Import Data from CSV**
4. 选择 `shennong_herbs_clean.csv` 文件
5. 映射字段并导入

### 2. 获取 Supabase 连接信息

1. 登录 [Supabase Dashboard](https://app.supabase.io)
2. 进入你的项目
3. 点击左侧 **Project Settings** → **API**
4. 复制以下信息：
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public**: `eyJhbGciOiJIUzI1NiIs...` (Publishable Key)

### 3. 配置客户端

#### 方式一：环境变量（推荐）

创建 `.env` 文件（复制 `.env.example`）：

```bash
# .env 文件
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-publishable-key-here
```

#### 方式二：界面配置

1. 启动桌面客户端
2. 点击 **中药查询** 按钮
3. 点击 **⚙️ 配置** 按钮
4. 输入 Project URL 和 Publishable Key
5. 点击 **保存配置**

## 使用方式

### 启动应用

```bash
python desktop_chat.py
```

### 查询中药

1. 点击左侧 **"▸ 中药查询"** 按钮
2. 在弹出的对话框中输入药物名称，如：
   - 人参
   - 黄芪
   - 丹砂
3. 点击 **查询** 或按 **Enter** 键
4. 查看查询结果

### 查询结果展示

查询成功后会显示：
- 📖 本经原文
- 🌿 性味
- 📍 产地
- 💊 主治
- 📋 用量
- ⚠️ 禁忌
- 📚 历代医家注解（别录、甄权、大明等）

## 技术实现

### 架构说明

```
用户界面 (ttkbootstrap)
    ↓ 点击"中药查询"
查询对话框
    ↓ 输入药物名称
SupabaseHerbClient
    ↓ HTTP API 请求
Supabase (PostgreSQL)
    ↓ 返回药物数据
格式化显示
```

### API 请求格式

```python
# 精确查询
GET https://your-project.supabase.co/rest/v1/shennong_herbs?drug_name=eq.人参&limit=1

# 模糊搜索
GET https://your-project.supabase.co/rest/v1/shennong_herbs?drug_name=ilike.%黄%
```

请求头：
```
apikey: your-publishable-key
Authorization: Bearer your-publishable-key
```

## 故障排查

### 问题一："配置信息缺失"

**原因**：未设置 SUPABASE_URL 和 SUPABASE_KEY

**解决**：
1. 检查 `.env` 文件是否存在并包含配置
2. 或者在查询界面点击"配置"按钮手动输入

### 问题二："未找到相关药物"

**原因**：
1. 药物名称不在数据库中
2. 数据库为空或未导入数据

**解决**：
1. 确认数据已正确导入 Supabase
2. 尝试使用其他名称，如 "黄耆" 代替 "黄芪"
3. 使用模糊搜索查看相似药物

### 问题三：查询超时或失败

**原因**：网络连接问题或 Supabase 服务异常

**解决**：
1. 检查网络连接
2. 确认 Project URL 正确
3. 检查 Supabase 服务状态

## 安全注意事项

⚠️ **重要提示**：

1. **Publishable Key** 是客户端使用的公钥，可以公开
2. 不要将 **Service Role Key** (secret key) 用于客户端
3. 建议在 Supabase 中启用 **RLS (Row Level Security)** 保护数据

```sql
-- 启用 RLS
ALTER TABLE shennong_herbs ENABLE ROW LEVEL SECURITY;

-- 允许匿名用户读取
CREATE POLICY "Allow anonymous read" ON shennong_herbs
    FOR SELECT USING (true);
```

## 扩展功能

### 添加更多草药数据

如需导入中经、下经数据：

1. 提取对应数据为 CSV
2. 在 Supabase 中导入到同一表
3. 或通过 API 批量插入

### 自定义查询条件

修改 `supabase_herb_client.py` 添加更多查询方式：

```python
def search_by_property(self, property_keyword: str) -> List[Dict]:
    """按性味搜索"""
    # 实现搜索逻辑
    pass

def search_by_indication(self, symptom: str) -> List[Dict]:
    """按主治症状搜索"""
    # 实现搜索逻辑
    pass
```

## 相关文件

| 文件 | 说明 |
|------|------|
| `supabase_herb_client.py` | Supabase 查询客户端 |
| `desktop_chat.py` | 桌面客户端（含查询界面） |
| `data/shennong_herbs_clean.csv` | 草药数据文件 |
| `.env.example` | 配置模板 |
| `docs/supabase_herb_query.md` | 本文档 |

## 参考链接

- [Supabase 官方文档](https://supabase.com/docs)
- [PostgREST API 文档](https://postgrest.org/en/stable/)
- [ttkbootstrap 文档](https://ttkbootstrap.readthedocs.io/)

# 中药查询功能快速开始

## 功能介绍

点击桌面客户端的 **"中药查询"** 按钮，可通过 Supabase 数据库查询《神农本草经》上经的 142 种草药信息。

## 快速配置（3分钟）

### 1. 准备 Supabase 数据库

#### 1.1 创建项目
1. 访问 [supabase.com](https://supabase.com) 并注册/登录
2. 点击 **New Project** 创建新项目
3. 等待数据库初始化完成

#### 1.2 导入数据
1. 进入 Supabase Dashboard
2. 点击左侧 **Table Editor**
3. 点击 **New Table** → **Import Data from CSV**
4. 选择 `data/shennong_herbs_clean.csv` 文件
5. 表名设为 `shennong_herbs`
6. 点击 **Import**

### 2. 获取连接信息

1. 在 Supabase Dashboard 中，点击左侧 **Project Settings** → **API**
2. 复制以下信息：
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public**: `eyJhbG...` (Publishable Key)

### 3. 配置客户端

创建 `.env` 文件：

```bash
copy .env.example .env
```

编辑 `.env` 文件，添加 Supabase 配置：

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...your-publishable-key
```

## 使用指南

### 启动应用

```bash
python desktop_chat.py
```

### 查询中药

1. 点击左侧 **"▸ 中药查询"** 按钮
2. 输入药物名称（如：人参、黄芪、丹砂）
3. 点击 **查询** 或按 **Enter**
4. 查看完整药物信息

![使用流程](https://i.imgur.com/example.png)

## 功能截图

### 查询界面
```
┌─────────────────────────────────────┐
│  🌿 神农本草经数据库查询               │
├─────────────────────────────────────┤
│  药物名称： [人参        ] [🔍 查询] │
├─────────────────────────────────────┤
│  【人参】                           │
│                                     │
│  📖 本经原文：                       │
│  味甘微寒，主补五脏，安精神...        │
│                                     │
│  🌿 性味：味甘微苦性微寒无毒          │
│                                     │
│  📍 产地：我国吉林辽宁产者最良...      │
│                                     │
│  💊 主治：人参为大补元气要药...        │
│                                     │
│  📋 用量：普通五分至三钱...           │
│                                     │
│  ⚠️ 禁忌：肺家有热诸症及阴虚...       │
└─────────────────────────────────────┘
```

## 数据结构

查询结果包含以下字段：

| 字段 | 内容 |
|------|------|
| 药物名称 | 中药名称 |
| 本经原文 | 《神农本草经》原文 |
| 性味 | 药物的性味归经 |
| 产地 | 药物产地信息 |
| 主治 | 主要治疗功效 |
| 用量 | 用法用量说明 |
| 禁忌 | 使用禁忌 |
| 其他 | 历代医家注解（别录、甄权、大明等） |

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 提示"配置信息缺失" | 检查 `.env` 文件是否存在，且包含 SUPABASE_URL 和 SUPABASE_KEY |
| 提示"未找到相关药物" | 确认数据已导入 Supabase；尝试使用其他名称如"黄耆" |
| 查询超时 | 检查网络连接；确认 Project URL 正确 |

## 相关文件

| 文件 | 说明 |
|------|------|
| `supabase_herb_client.py` | Supabase 查询客户端类 |
| `desktop_chat.py` | 桌面客户端（已集成查询功能） |
| `data/shennong_herbs_clean.csv` | 草药数据文件 |
| `docs/supabase_herb_query.md` | 详细配置文档 |

## 技术架构

```
┌─────────────────┐
│  desktop_chat.py │  ← 用户界面 (ttkbootstrap)
│  (中药查询按钮)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ supabase_herb_  │  ← 查询客户端 (HTTP API)
│ client.py       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Supabase      │  ← PostgreSQL 数据库
│  (shennong_herbs表)│
└─────────────────┘
```

## 下一步

- 导入更多草药数据（中经、下经）
- 添加按性味、主治搜索功能
- 集成到主聊天流程中

## 帮助

如有问题，请查看详细文档：`docs/supabase_herb_query.md`

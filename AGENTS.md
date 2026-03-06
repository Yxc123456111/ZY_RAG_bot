# TCM Chatbot - Agent Guide

## 项目概述

这是一个基于RAG（检索增强生成）+ Supabase 关系型数据库的中医聊天机器人系统。

## 核心架构

```
api/           - FastAPI接口层
core/          - 核心业务逻辑
  - intent_classifier.py  意图识别
  - text2sql.py           自然语言转SQL
  - diagnosis_engine.py   诊断引擎
  - plugin_manager.py     插件管理
db/            - Supabase 数据库客户端
  - supabase_client.py    统一Supabase客户端
  - __init__.py           模块导出
rag/           - RAG向量数据库
web/           - Web界面
config/        - 配置文件
data/          - 数据目录
  - documents/   文档目录（神农本草经、伤寒论、金匮要略、针灸、医案）
  - vector_db/   本地向量数据库
```

## 数据库架构

### 关系型数据库（Supabase）

所有关系型数据查询均通过 Supabase 进行，支持以下表：

| 表名 | 说明 | 查询类型 |
|------|------|----------|
| `shennong_herbs` | 神农本草经草药数据 | 精确查询、模糊搜索 |
| `acupoints` | 针灸穴位数据 | 精确查询、模糊搜索 |
| `shanghan_formulas` | 伤寒论方剂数据 | 精确查询、模糊搜索 |
| `jinkui_formulas` | 金匮要略方剂数据 | 精确查询、模糊搜索 |

### 向量数据库（本地）

使用本地 ChromaDB/Milvus 存储文档向量，支持 RAG 检索：

| 来源类型 | 说明 |
|----------|------|
| `shennong` | 神农本草经文档 |
| `acupuncture` | 针灸文档 |
| `shanghan` | 伤寒论文档 |
| `jinkui` | 金匮要略文档 |
| `cases` | 医案文档 |

## 开发规范

### 1. 代码风格
- 使用Python类型注解
- 函数和类添加docstring
- 遵循PEP 8规范

### 2. 模块设计
- 保持单一职责原则
- 使用接口/抽象基类定义扩展点
- 新功能通过插件机制添加

### 3. 数据库操作
- **关系型查询**：统一使用 `db.SupabaseClient`
- **向量查询**：使用 `rag.TCMVectorStore`
- 异步操作使用 async/await
- 所有Supabase表变更需在 Supabase Dashboard 中管理

### 4. 配置管理
- 环境变量使用 `.env` 文件
- 配置文件使用 YAML 格式
- 敏感信息不提交到版本控制

## 配置说明

### Supabase 配置

在项目根目录创建 `.env` 文件：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

或使用 `config_manager` 的配置文件。

## 扩展指南

### 添加新模块

1. 在 `core/` 创建新模块文件
2. 在 `config/config.yaml` 添加模块开关
3. 在 `api/main.py` 添加API端点
4. 更新 `AGENTS.md` 文档

### 添加新的Supabase表查询

1. 在 `db/supabase_client.py` 中添加查询方法：
   ```python
   def query_new_table(self, name: str) -> Optional[Dict]:
       # 实现查询逻辑
       pass
   ```

2. 在 `core/text2sql.py` 的 SchemaManager 中添加表定义

3. 在 `api/main.py` 中添加查询处理函数

### 添加新插件

1. 创建 `plugins/my_plugin.py`
2. 继承 `BasePlugin` 或特定类型插件基类
3. 实现必要的方法
4. 重启服务自动加载

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_intent.py

# 带覆盖率
pytest --cov=core tests/
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t tcm-chatbot .

# 运行容器
docker run -p 8000:8000 -p 7860:7860 tcm-chatbot
```

### 生产环境注意事项

1. 修改 `.env` 中的 Supabase 密钥和配置
2. 使用HTTPS
3. 启用日志轮转
4. 设置监控告警

## 常见问题

### 向量数据库加载慢
- 首次加载需要下载嵌入模型
- 可考虑使用本地缓存

### Supabase 连接失败
- 检查 SUPABASE_URL 和 SUPABASE_KEY 配置
- 确认 Supabase 项目已启动
- 检查网络连接和防火墙设置

### 内存不足
- 减小向量检索的top_k值
- 使用更小的嵌入模型
- 启用结果缓存

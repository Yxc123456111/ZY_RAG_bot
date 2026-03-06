# 🏥 中医智能助手 - TCM Chatbot

基于RAG+关系型数据库的中医知识问答系统

## 📋 功能特性

### 核心功能

1. **📍 针灸知识查询**
   - 穴位定位、主治、功效查询
   - 经络循行、穴位配伍查询
   - 支持自然语言语义查询

2. **🌿 中药查询**
   - 中药性味、归经、功效查询
   - 用法用量、禁忌查询
   - 支持别名查询

3. **📖 伤寒论方剂查询**
   - 方剂组成、功效、主治查询
   - 条文原文、病机分析查询
   - 类方比较

4. **📚 金匮要略方剂查询**
   - 方剂查询（按篇章、病证分类）
   - 原文检索

5. **🔍 病情诊断**
   - 基于RAG的中医辨证分析
   - 四诊信息提取
   - 推荐治疗方案
   - 参考来源追溯

### 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户交互层 (Web/API)                  │
├─────────────────────────────────────────────────────────┤
│                   智能路由与意图识别                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  SQL生成    │  │  RAG检索    │  │    诊断引擎      │ │
│  │  (Text2SQL) │  │ (Vector DB) │  │                 │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
│         │                │                   │          │
│         ▼                ▼                   ▼          │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Supabase 关系型数据库                     │   │
│  │   针灸 │ 神农本草经 │ 伤寒论 │ 金匮要略         │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         本地向量数据库 (Chroma/Milvus)           │   │
│  │   针灸 │ 伤寒论 │ 金匮要略 │ 神农本草经 │ 医案  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 4GB+ RAM
- Supabase 账号和项目

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd tcm-chatbot

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 初始化

```bash
# 初始化数据库和目录
python main.py --init
```

### 启动服务

```bash
# 启动API服务器
python main.py --api

# 启动Web界面
python main.py --web

# 启动所有服务
python main.py --all

# 交互式命令行
python main.py --shell
```

### 访问服务

- API文档: http://localhost:8000/docs
- Web界面: http://localhost:7860

## 📁 项目结构

```
tcm-chatbot/
├── api/                    # API接口
│   └── main.py            # FastAPI主应用
├── core/                   # 核心模块
│   ├── intent_classifier.py   # 意图识别
│   ├── text2sql.py           # 自然语言转SQL
│   ├── diagnosis_engine.py   # 诊断引擎
│   └── plugin_manager.py     # 插件管理
├── db/                     # Supabase数据库客户端
│   ├── supabase_client.py   # 统一Supabase客户端
│   └── __init__.py         # 模块导出
├── rag/                    # RAG模块
│   └── vector_store.py    # 向量数据库
├── web/                    # Web界面
│   └── chat_interface.py  # Gradio/Streamlit界面
├── config/                 # 配置文件
│   └── config.yaml        # 主配置
├── data/                   # 数据目录
│   ├── vector_db/         # 本地向量数据库
│   └── documents/         # 文档资料（神农本草经、伤寒论等）
├── plugins/                # 插件目录
├── tests/                  # 测试
├── main.py                # 主入口
├── requirements.txt       # 依赖
└── README.md             # 说明文档
```

## ⚙️ 配置

### Supabase 配置

在项目根目录创建 `.env` 文件：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### 详细配置

编辑 `config/config.yaml` 进行更多配置：

```yaml
# 数据库配置
database:
  relational:
    type: "supabase"  # 统一使用Supabase
    url: "${SUPABASE_URL}"
    key: "${SUPABASE_KEY}"
  
  vector:
    type: "chroma"  # 本地向量数据库
    persist_directory: "./data/vector_db"
    embedding_model: "BAAI/bge-large-zh-v1.5"

# LLM配置
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"
```

## 📚 数据准备

### 1. 关系型数据库（Supabase）

在 Supabase Dashboard 中创建以下表：

| 表名 | 说明 |
|------|------|
| `shennong_herbs` | 神农本草经草药数据 |
| `acupoints` | 针灸穴位数据 |
| `shanghan_formulas` | 伤寒论方剂数据 |
| `jinkui_formulas` | 金匮要略方剂数据 |

表结构参考：`docs/supabase_schema.sql`

导入数据方式：
- 通过 Supabase Dashboard 的 Table Editor 手动导入
- 使用 Supabase CLI 批量导入
- 调用 API 接口插入数据

### 2. 向量数据库数据（本地）

将文档放入 `data/documents/` 相应目录：

```
data/documents/
├── 针灸/           # 针灸相关文档
├── 伤寒论/         # 伤寒论文档
├── 金匮要略/       # 金匮要略文档
├── 神农本草经/     # 神农本草经文档
└── 医案/           # 医案文档
```

支持格式：`.txt`, `.md`, `.pdf`, `.docx`, `.json`

启动服务时会自动加载文档到向量数据库。

## 🔌 扩展开发

### 添加新的查询处理器

```python
from core.plugin_manager import QueryHandlerPlugin, PluginInfo, PluginType

class MyHandler(QueryHandlerPlugin):
    def initialize(self) -> bool:
        return True
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="my_handler",
            version="1.0.0",
            description="我的处理器",
            author="Your Name",
            plugin_type=PluginType.QUERY_HANDLER,
            dependencies=[]
        )
    
    def can_handle(self, intent: str, entities: Dict) -> bool:
        # 判断是否能处理
        return intent == "my_intent"
    
    async def handle(self, query: str, entities: Dict, context: Dict) -> Dict:
        # 处理查询
        return {"result": "处理结果"}
```

将文件保存到 `plugins/my_handler.py` 即可自动加载。

## 🧪 API示例

### 聊天接口

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "足三里穴在哪里？"
  }'
```

### 诊断接口

```bash
curl -X POST "http://localhost:8000/diagnosis" \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "头痛，恶寒发热，无汗，舌苔薄白，脉浮紧"
  }'
```

### 知识搜索

```bash
curl "http://localhost:8000/knowledge/search?query=桂枝汤&source_type=shanghan&k=5"
```

## ⚠️ 免责声明

1. 本系统提供的所有信息仅供参考学习，**不能替代专业医生的诊断和治疗建议**。
2. 如有健康问题，请及时就医，遵医嘱治疗。
3. 使用本系统产生的任何后果，开发者不承担责任。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系

如有问题或建议，请通过以下方式联系：
- 邮箱: your-email@example.com
- GitHub Issues

---

**传承中医智慧，服务现代健康** 🏥

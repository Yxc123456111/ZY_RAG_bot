"""
中医聊天机器人 - FastAPI主应用
"""

import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent_classifier import IntentClassifier, IntentType, QueryRouter
from core.text2sql import Text2SQLConverter, SchemaManager
from core.diagnosis_engine import DiagnosisEngine
from rag.milvus_store import TCMMilvusStore as TCMVectorStore, DocumentLoader
from db import SupabaseClient, create_supabase_client


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="会话ID")
    context: Optional[List[Dict]] = Field(None, description="对话上下文")


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    message: str
    intent: str
    data_type: str  # sql / rag / direct
    sources: Optional[List[Dict]] = None
    confidence: float
    response_time: float


class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="查询内容")
    table: Optional[str] = Field(None, description="指定查询表")


class QueryResponse(BaseModel):
    """查询响应"""
    success: bool
    data: List[Dict]
    count: int
    sql: Optional[str] = None
    explanation: Optional[str] = None


class DiagnosisRequest(BaseModel):
    """诊断请求"""
    symptoms: str = Field(..., description="症状描述", min_length=10)
    include_sources: Optional[List[str]] = Field(
        default=["acupuncture", "shanghan", "jinkui", "shennong", "cases"],
        description="包含的知识来源"
    )


class DiagnosisResponse(BaseModel):
    """诊断响应"""
    syndrome_type: str
    pathogenesis: str
    treatment_principle: str
    recommendations: List[Dict]
    analysis: str
    sources: List[Dict]
    confidence: float
    warnings: List[str]


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str
    components: Dict[str, str]


# ==================== 全局状态 ====================

class AppState:
    """应用状态管理"""
    
    def __init__(self):
        self.intent_classifier: Optional[IntentClassifier] = None
        self.query_router: Optional[QueryRouter] = None
        self.text2sql: Optional[Text2SQLConverter] = None
        self.vector_store: Optional[TCMVectorStore] = None
        self.diagnosis_engine: Optional[DiagnosisEngine] = None
        self.supabase_client: Optional[SupabaseClient] = None
        self.initialized: bool = False
    
    async def initialize(self):
        """初始化应用组件"""
        if self.initialized:
            return
        
        print("[INIT] Initializing TCM Chatbot...")
        
        # 1. 初始化意图分类器
        self.intent_classifier = IntentClassifier()
        self.query_router = QueryRouter()
        
        # 2. 初始化Text2SQL
        self.text2sql = Text2SQLConverter(use_llm=False)
        
        # 3. 初始化向量数据库（使用本地嵌入，无需下载模型）
        try:
            self.vector_store = TCMVectorStore(
                local_mode=True,  # 使用本地模式，无需Milvus服务器
                collection_name="tcm_knowledge",
                dim=128
            )
            stats = self.vector_store.get_collection_stats()
            print(f"[INIT] Vector store loaded: {stats}")
            
            # 如果向量数据库为空，加载文档
            if stats.get("total_documents", 0) == 0:
                print("[INIT] Vector store is empty, loading documents...")
                await self._load_documents_to_vector_store()
        except Exception as e:
            print(f"[INIT] Vector store init skipped: {e}")
            self.vector_store = None
        
        # 4. 初始化诊断引擎
        if self.vector_store:
            self.diagnosis_engine = DiagnosisEngine(
                vector_store=self.vector_store,
                llm_client=None
            )
        
        # 5. 初始化 Supabase 客户端（用于关系型数据库查询）
        try:
            self.supabase_client = create_supabase_client()
            if self.supabase_client:
                print("[INIT] Supabase client initialized")
            else:
                print("[INIT] Supabase client not configured (set SUPABASE_URL and SUPABASE_KEY)")
        except Exception as e:
            print(f"[INIT] Supabase client init failed: {e}")
            self.supabase_client = None
        
        self.initialized = True
        print("[INIT] Initialization completed!")
    
    def get_vector_store_stats(self) -> Dict:
        """获取向量数据库统计"""
        if self.vector_store:
            return self.vector_store.get_collection_stats()
        return {}
    
    async def _load_documents_to_vector_store(self):
        """加载文档到向量数据库"""
        if not self.vector_store:
            print("[WARNING] Vector store not available, skipping document loading")
            return
        
        data_dir = "./data/documents"
        source_mapping = {
            "acupuncture": "针灸",
            "shanghan": "伤寒论",
            "jinkui": "金匮要略",
            "shennong": "神农本草经",
            "cases": "医案"
        }
        
        total_loaded = 0
        for source_type, dir_name in source_mapping.items():
            dir_path = os.path.join(data_dir, dir_name)
            
            if not os.path.exists(dir_path):
                print(f"[INFO] Directory not found: {dir_path}")
                continue
            
            print(f"[INIT] Loading {dir_name} documents from {dir_path}...")
            
            try:
                # 递归加载目录中的所有文档
                documents = []
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in {'.txt', '.md', '.json'}:
                            file_path = os.path.join(root, file)
                            doc = DocumentLoader.load_from_file(file_path)
                            if doc:
                                doc.metadata["source"] = file_path
                                doc.metadata["source_type"] = source_type
                                documents.append(doc)
                
                if documents:
                    ids = self.vector_store.add_documents(documents, source_type=source_type)
                    print(f"[INIT] Loaded {len(documents)} documents ({len(ids)} chunks) from {dir_name}")
                    total_loaded += len(documents)
                else:
                    print(f"[INFO] No documents found in {dir_path}")
                    
            except Exception as e:
                print(f"[ERROR] Failed to load documents from {dir_name}: {e}")
        
        print(f"[INIT] Total documents loaded: {total_loaded}")


# 全局状态实例
app_state = AppState()


# ==================== 生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await app_state.initialize()
    yield
    # 关闭时清理
    print("应用关闭，执行清理...")


# ==================== FastAPI应用 ====================

app = FastAPI(
    title="中医智能助手 API",
    description="基于RAG+关系型数据库的中医聊天机器人",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API端点 ====================

@app.get("/", response_model=Dict)
async def root():
    """根路径"""
    return {
        "name": "中医智能助手 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    components = {
        "intent_classifier": "ok" if app_state.intent_classifier else "not_initialized",
        "vector_store": "ok" if app_state.vector_store else "not_initialized",
        "diagnosis_engine": "ok" if app_state.diagnosis_engine else "not_initialized",
        "supabase": "ok" if app_state.supabase_client else "not_configured"
    }
    
    # 添加向量数据库统计
    if app_state.vector_store:
        stats = app_state.get_vector_store_stats()
        components["vector_documents"] = str(stats.get("total_documents", 0))
    
    return HealthResponse(
        status="healthy" if app_state.initialized else "initializing",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        components=components
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    主聊天接口
    
    根据用户消息自动识别意图并返回相应回答
    """
    import time
    start_time = time.time()
    
    # 生成或复用会话ID
    session_id = request.session_id or str(uuid.uuid4())
    
    # 1. 意图识别和路由
    route_result = app_state.query_router.route(request.message)
    
    response_message = ""
    data_type = "direct"
    sources = None
    
    try:
        # 2. 根据路由结果处理
        if route_result["requires_sql"]:
            # 数据库查询
            data_type = "sql"
            
            # 检查是否为 Supabase 查询（神农本草经/针灸/伤寒论/金匮要略）
            if route_result.get("table") in ["shennong_herbs", "acupoints", "shanghan_formulas", "jinkui_formulas"]:
                response_message = await _handle_supabase_query(
                    route_result["table"],
                    request.message,
                    route_result["entities"]
                )
            else:
                response_message = "暂不支持该类型的本地数据库查询。请使用神农本草经、针灸、伤寒论或金匮要略相关查询。"
        
        elif route_result["requires_rag"]:
            # RAG查询
            data_type = "rag"
            response_message = await _handle_rag_query(
                request.message,
                route_result.get("rag_sources", [])
            )
        
        else:
            # 直接回复
            response_message = _handle_direct_response(request.message, route_result["intent"])
    
    except Exception as e:
        response_message = f"抱歉，处理您的请求时出现了错误：{str(e)}"
        data_type = "error"
    
    response_time = time.time() - start_time
    
    return ChatResponse(
        session_id=session_id,
        message=response_message,
        intent=route_result["intent"],
        data_type=data_type,
        sources=sources,
        confidence=route_result["confidence"],
        response_time=round(response_time, 3)
    )


@app.post("/query/sql", response_model=QueryResponse)
async def sql_query(request: QueryRequest):
    """
    SQL查询接口
    
    将自然语言转换为SQL并执行查询
    """
    # 如果没有指定表，先识别意图
    table = request.table
    if not table:
        route_result = app_state.query_router.route(request.query)
        table = route_result.get("table", "")
    
    if not table:
        return QueryResponse(
            success=False,
            data=[],
            count=0,
            explanation="无法确定查询目标，请明确指定查询类型（针灸/中药/伤寒论/金匮要略）"
        )
    
    # 生成SQL
    sql_result = app_state.text2sql.convert(request.query, table)
    
    # 这里需要实际的数据库连接来执行SQL
    # 暂时返回SQL和说明
    return QueryResponse(
        success=True,
        data=[],
        count=0,
        sql=sql_result.sql,
        explanation=sql_result.explanation
    )


@app.post("/diagnosis", response_model=DiagnosisResponse)
async def diagnosis(request: DiagnosisRequest):
    """
    病情诊断接口
    
    基于RAG进行中医辨证分析
    """
    try:
        result = await app_state.diagnosis_engine.diagnose(
            patient_description=request.symptoms,
            include_sources=request.include_sources
        )
        
        return DiagnosisResponse(
            syndrome_type=result.syndrome_type,
            pathogenesis=result.pathogenesis,
            treatment_principle=result.treatment_principle,
            recommendations=result.recommendations,
            analysis=result.analysis,
            sources=result.sources,
            confidence=result.confidence,
            warnings=result.warnings
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"诊断失败：{str(e)}")


@app.get("/knowledge/search")
async def knowledge_search(
    query: str,
    source_type: Optional[str] = None,
    k: int = 5
):
    """
    知识库搜索接口
    
    在向量数据库中搜索相关知识
    """
    if not app_state.vector_store:
        raise HTTPException(status_code=503, detail="向量数据库未初始化")
    
    try:
        if source_type:
            results = app_state.vector_store.search_by_source_type(
                query=query,
                source_type=source_type,
                k=k
            )
        else:
            results = app_state.vector_store.similarity_search(
                query=query,
                k=k
            )
        
        return {
            "query": query,
            "source_type": source_type,
            "results": [
                {
                    "content": r.content[:500],
                    "source": r.source,
                    "score": round(r.score, 4)
                }
                for r in results
            ],
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败：{str(e)}")


@app.get("/schema/{table_name}")
async def get_table_schema(table_name: str):
    """获取表结构信息"""
    schema = SchemaManager.get_schema(table_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
    
    return {
        "table_name": table_name,
        "schema": schema
    }


@app.get("/schema")
async def list_tables():
    """列出所有可用的表"""
    return {
        "tables": list(SchemaManager.SCHEMAS.keys()),
        "descriptions": {
            name: info["description"]
            for name, info in SchemaManager.SCHEMAS.items()
        }
    }


# ==================== 辅助函数 ====================

async def _handle_sql_query(query: str, table: str, entities: Dict) -> str:
    """处理SQL查询"""
    # 生成SQL
    sql_result = app_state.text2sql.convert(query, table, entities)
    
    # 格式化回复
    response = f"根据您的问题，我为您查询了**{table}**相关信息。\n\n"
    response += f"📝 **查询说明**：{sql_result.explanation}\n\n"
    response += f"```sql\n{sql_result.sql}\n```\n\n"
    
    # 注意：实际执行需要数据库连接
    response += "（注：实际数据查询需要配置数据库连接）"
    
    return response


async def _handle_supabase_query(table: str, query: str, entities: Dict) -> str:
    """
    处理Supabase数据库查询
    
    支持表：
    - shennong_herbs: 神农本草经
    - acupoints: 针灸穴位
    - shanghan_formulas: 伤寒论方剂
    - jinkui_formulas: 金匮要略方剂
    """
    if not app_state.supabase_client:
        return "抱歉，数据库查询服务未配置。请设置 SUPABASE_URL 和 SUPABASE_KEY 环境变量。"
    
    # 根据表类型处理查询
    if table == "shennong_herbs":
        return await _handle_shennong_query(query, entities)
    elif table == "acupoints":
        return await _handle_acupoint_query(query, entities)
    elif table == "shanghan_formulas":
        return await _handle_shanghan_query(query, entities)
    elif table == "jinkui_formulas":
        return await _handle_jinkui_query(query, entities)
    else:
        return f"暂不支持的表查询: {table}"


async def _handle_shennong_query(query: str, entities: Dict) -> str:
    """处理神农本草经查询"""
    # 从实体中提取中药名称
    herb_names = []
    
    if entities:
        herb_entities = entities.get("herb", [])
        if herb_entities:
            herb_names.extend(herb_entities)
    
    # 如果没有提取到实体，尝试使用 HerbKeywordExtractor
    if not herb_names:
        try:
            from core.herb_sql_generator import HerbKeywordExtractor
            extractor = HerbKeywordExtractor()
            herb_names = extractor.extract(query)
            print(f"[API] 使用 HerbKeywordExtractor 提取: {herb_names}")
        except Exception as e:
            print(f"[API] HerbKeywordExtractor 提取失败: {e}")
    
    # 如果仍然没有提取到，尝试从查询中直接匹配常见中药
    if not herb_names:
        common_herbs = ["人参", "黄芪", "当归", "甘草", "桂枝", "麻黄", "柴胡", "白术", "茯苓", "川芎", "熟地黄", "白芍", "生姜", "大枣", "半夏", "陈皮", "枳实", "厚朴", "大黄", "黄连", "黄芩", "黄柏", "栀子", "连翘", "金银花", "薄荷", "防风", "荆芥", "羌活", "独活", "苍术", "知母", "石膏", "麦冬", "天冬", "枸杞子", "菊花", "决明子", "牛膝", "杜仲", "续断", "补骨脂", "菟丝子", "五味子", "山茱萸", "牡丹皮", "泽泻", "山药", "附子", "干姜", "肉桂", "吴茱萸", "细辛", "葛根", "升麻", "白芷", "蔓荆子", "桑叶", "菊花", "柴胡", "银柴胡", "地骨皮", "青蒿", "鳖甲", "龟板", "龙骨", "牡蛎", "酸枣仁", "柏子仁", "远志", "合欢皮", "夜交藤", "石菖蒲", "麝香", "冰片", "苏合香", "石决明", "羚羊角", "牛黄", "钩藤", "天麻", "地龙", "全蝎", "蜈蚣", "僵蚕", "半夏", "天南星", "白附子", "白芥子", "皂荚", "旋覆花", "白前", "川贝母", "浙贝母", "瓜蒌", "竹茹", "竹沥", "天竺黄", "前胡", "桔梗", "胖大海", "海藻", "昆布", "黄药子", "海蛤壳", "海浮石", "瓦楞子", "杏仁", "紫苏子", "百部", "紫菀", "款冬花", "马兜铃", "枇杷叶", "桑白皮", "葶苈子", "白果", "朱砂", "磁石", "龙骨", "琥珀", "酸枣仁", "柏子仁", "远志", "合欢皮", "首乌藤", "灵芝", "缬草", "麝香", "冰片", "苏合香", "石菖蒲", "人参", "西洋参", "党参", "太子参", "黄芪", "白术", "山药", "甘草", "大枣", "刺五加", "绞股蓝", "红景天", "沙棘", "饴糖", "蜂蜜", "鹿茸", "紫河车", "淫羊藿", "巴戟天", "仙茅", "杜仲", "续断", "肉苁蓉", "锁阳", "补骨脂", "益智仁", "菟丝子", "沙苑子", "韭菜子", "核桃仁", "蛤蚧", "冬虫夏草", "胡桃仁", "龙眼肉", "当归", "熟地黄", "白芍", "阿胶", "何首乌", "龙眼肉", "楮实子", "北沙参", "南沙参", "百合", "麦冬", "天冬", "石斛", "玉竹", "黄精", "枸杞子", "墨旱莲", "女贞子", "桑葚", "黑芝麻", "龟甲", "鳖甲", "五味子", "乌梅", "五倍子", "罂粟壳", "诃子", "肉豆蔻", "赤石脂", "山茱萸", "覆盆子", "桑螵蛸", "海螵蛸", "金樱子", "莲子", "芡实", "刺猬皮", "椿皮", "石榴皮", "明党参", "麻黄根", "浮小麦", "糯稻根须", "龙胆", "龙胆草"]
        
        for herb in common_herbs:
            if herb in query:
                herb_names.append(herb)
                break
    
    if not herb_names:
        return "抱歉，未能从您的问题中识别出中药名称。请尝试输入具体的中药名称，如'人参'、'黄芪'等。"
    
    herb_name = herb_names[0]
    result = app_state.supabase_client.query_shennong_herb(herb_name)
    
    if result:
        formatted = app_state.supabase_client.format_shennong_herb(result)
        return f"为您查询到神农本草经 **{herb_name}** 的信息：\n\n{formatted}"
    else:
        suggestions = app_state.supabase_client.search_shennong_herbs(herb_name, limit=5)
        if suggestions:
            suggestion_names = [s.get("drug_name", "") for s in suggestions]
            return f"未找到'{herb_name}'，您是否想查询：{', '.join(suggestion_names)}？"
        else:
            return f"抱歉，神农本草经中未找到'{herb_name}'的相关信息。"


async def _handle_acupoint_query(query: str, entities: Dict) -> str:
    """处理针灸穴位查询"""
    # 提取穴位名称
    acupoint_names = []
    
    if entities:
        acupoint_entities = entities.get("acupoint", [])
        if acupoint_entities:
            acupoint_names.extend(acupoint_entities)
    
    # 常见穴位列表
    if not acupoint_names:
        common_points = ["足三里", "合谷", "太冲", "内关", "百会", "风池", "大椎", "关元", "气海", "三阴交", "涌泉", "太溪", "曲池", "列缺", "膻中", "中脘", "下脘", "神阙", "命门", "肾俞", "脾俞", "胃俞", "肝俞", "心俞", "肺俞", "胆俞", "膀胱俞", "大肠俞", "小肠俞", "三焦俞", "委中", "承山", "昆仑", "申脉", "照海", "公孙", "足临泣", "外关", "支沟", "翳风", "角孙", "耳门", "听宫", "睛明", "攒竹", "天柱", "哑门", "风府", "脑户", "强间", "后顶", "哑门", "大杼", "风门", "厥阴俞", "附分", "魄户", "膏肓", "神堂", "譩譆", "膈关", "魂门", "阳纲", "意舍", "胃仓", "肓门", "志室", "胞肓", "秩边", "承扶", "殷门", "浮郄", "委阳", "合阳", "承筋", "飞扬", "跗阳", "昆仑", "仆参", "申脉", "金门", "京骨", "束骨", "足通谷", "至阴"]
        
        for point in common_points:
            if point in query:
                acupoint_names.append(point)
                break
    
    if not acupoint_names:
        return "抱歉，未能从您的问题中识别出穴位名称。请尝试输入具体的穴位名称，如'足三里'、'合谷'等。"
    
    point_name = acupoint_names[0]
    result = app_state.supabase_client.query_acupoint(point_name)
    
    if result:
        formatted = app_state.supabase_client.format_acupoint(result)
        return f"为您查询到穴位 **{point_name}** 的信息：\n\n{formatted}"
    else:
        suggestions = app_state.supabase_client.search_acupoints(point_name, limit=5)
        if suggestions:
            suggestion_names = [s.get("name", "") for s in suggestions]
            return f"未找到'{point_name}'，您是否想查询：{', '.join(suggestion_names)}？"
        else:
            return f"抱歉，数据库中未找到'{point_name}'的相关信息。"


async def _handle_shanghan_query(query: str, entities: Dict) -> str:
    """处理伤寒论查询"""
    # 提取方剂名称
    formula_names = []
    
    if entities:
        formula_entities = entities.get("formula", [])
        if formula_entities:
            formula_names.extend(formula_entities)
    
    # 常见方剂列表
    if not formula_names:
        common_formulas = ["桂枝汤", "麻黄汤", "小柴胡汤", "大柴胡汤", "白虎汤", "承气汤", "四逆汤", "理中汤", "真武汤", "五苓散", "小青龙汤", "大青龙汤", "葛根汤", "小建中汤", "炙甘草汤", "乌梅丸", "白头翁汤", "麻子仁丸", "茵陈蒿汤", "栀子豉汤", "泻心汤", "黄连汤", "黄芩汤", "桂枝加葛根汤", "桂枝加附子汤", "桂枝去芍药汤", "桂枝麻黄各半汤", "桂枝二麻黄一汤", "桂枝二越婢一汤", "桂枝加芍药生姜各一两人参三两新加汤", "桂枝甘草汤", "桂枝甘草龙骨牡蛎汤", "桂枝去芍药加蜀漆牡蛎龙骨救逆汤", "桂枝加桂汤", "桂枝附子汤", "甘草附子汤", "桂枝去桂加茯苓白术汤", "麻黄杏仁甘草石膏汤", "麻黄附子细辛汤", "麻黄附子甘草汤", "麻黄升麻汤", "麻黄连翘赤小豆汤", "柴胡加龙骨牡蛎汤", "柴胡桂枝汤", "柴胡桂枝干姜汤", "四逆散", "半夏泻心汤", "生姜泻心汤", "甘草泻心汤", "附子泻心汤", "大黄黄连泻心汤", "旋覆代赭汤", "厚朴生姜半夏甘草人参汤", "小陷胸汤", "大陷胸汤", "大陷胸丸", "三物白散", "大黄附子汤", "十枣汤", "瓜蒂散", "赤石脂禹余粮汤", "桃花汤", "吴茱萸汤", "四逆汤", "通脉四逆汤", "通脉四逆加猪胆汁汤", "四逆加人参汤", "茯苓四逆汤", "白通汤", "白通加猪胆汁汤", "附子汤", "真武汤", "当归四逆汤", "当归四逆加吴茱萸生姜汤", "炙甘草汤", "甘草干姜汤", "芍药甘草汤", "芍药甘草附子汤", "甘草汤", "桔梗汤", "苦酒汤", "半夏散及汤", "猪肤汤", "猪苓汤", "黄连阿胶汤", "四逆汤", "四逆加人参汤", "茯苓四逆汤", "通脉四逆汤", "通脉四逆加猪胆汁汤", "白通汤", "白通加猪胆汁汤", "附子汤", "真武汤", "桃花汤", "猪肤汤", "甘草汤", "桔梗汤", "苦酒汤", "半夏散及汤", "乌梅丸", "白头翁汤", "麻黄升麻汤", "干姜黄芩黄连人参汤"]
        
        for formula in common_formulas:
            if formula in query:
                formula_names.append(formula)
                break
    
    if not formula_names:
        # 尝试搜索关键词
        result = app_state.supabase_client.search_shanghan_formulas(query, limit=3)
        if result:
            formatted = app_state.supabase_client.format_results(result, "shanghan_formulas")
            return f"为您找到以下伤寒论相关方剂：\n\n{formatted}"
        return "抱歉，未能从您的问题中识别出方剂名称或症状。请尝试输入具体的方剂名称，如'桂枝汤'、'麻黄汤'等，或描述相关症状。"
    
    formula_name = formula_names[0]
    result = app_state.supabase_client.query_shanghan_formula(formula_name)
    
    if result:
        formatted = app_state.supabase_client.format_formula(result, "伤寒论")
        return f"为您查询到伤寒论方剂 **{formula_name}** 的信息：\n\n{formatted}"
    else:
        suggestions = app_state.supabase_client.search_shanghan_formulas(formula_name, limit=5)
        if suggestions:
            suggestion_names = [s.get("name", "") for s in suggestions]
            return f"未找到'{formula_name}'，您是否想查询：{', '.join(suggestion_names)}？"
        else:
            return f"抱歉，伤寒论中未找到'{formula_name}'的相关信息。"


async def _handle_jinkui_query(query: str, entities: Dict) -> str:
    """处理金匮要略查询"""
    # 提取方剂名称
    formula_names = []
    
    if entities:
        formula_entities = entities.get("formula", [])
        if formula_entities:
            formula_names.extend(formula_entities)
    
    # 常见方剂列表
    if not formula_names:
        common_formulas = ["栝楼桂枝汤", "葛根汤", "大承气汤", "麻黄加术汤", "麻黄杏仁薏苡甘草汤", "防己黄芪汤", "桂枝附子汤", "白术附子汤", "甘草附子汤", "百合知母汤", "滑石代赭汤", "百合鸡子汤", "百合地黄汤", "百合洗方", "栝楼牡蛎散", "百合滑石散", "甘草泻心汤", "苦参汤", "雄黄熏方", "赤豆当归散", "升麻鳖甲汤", "鳖甲煎丸", "薯蓣丸", "酸枣仁汤", "大黄䗪虫丸", "炙甘草汤", "肾气丸", "胶艾汤", "当归芍药散", "干姜人参半夏丸", "当归贝母苦参丸", "葵子茯苓散", "当归散", "白术散", "枳实芍药散", "下瘀血汤", "竹叶汤", "竹皮大丸", "白头翁加甘草阿胶汤", "黄土汤", "赤小豆当归散", "蜘蛛散", "甘草粉蜜汤", "鸡屎白散", "师aredip汤", "通脉四逆汤", "诃黎勒散", "附子粳米汤", "厚朴七物汤", "厚朴三物汤", "大柴胡汤", "大黄附子汤", "赤丸", "大乌头煎", "当归生姜羊肉汤", "乌头桂枝汤", "附子汤", "甘草干姜汤", "芍药甘草汤", "调胃承气汤", "大承气汤", "白虎加人参汤", "猪苓汤", "文蛤散", "瓜蒌瞿麦丸", "蒲灰散", "滑石白鱼散", "茯苓戎盐汤", "越婢汤", "防己茯苓汤", "甘草麻黄汤", "麻黄附子汤", "杏子汤", "黄芪芍药桂枝苦酒汤", "桂枝加黄芪汤", "桂枝去芍药加麻黄细辛附子汤", "枳术汤", "茵陈蒿汤", "硝石矾石散", "栀子大黄汤", "猪膏发煎", "茵陈五苓散", "大黄硝石汤", "半夏麻黄丸", "柏叶汤", "黄土汤", "泻心汤", "茱萸汤", "半夏干姜散", "生姜半夏汤", "橘皮汤", "橘皮竹茹汤", "薏苡附子散", "桂枝生姜枳实汤", "赤石脂丸", "乌头赤石脂丸", "九痛丸", "柴胡桂枝汤", "厚朴七物汤", "附子粳米汤", "厚朴三物汤", "大柴胡汤", "大承气汤", "大建中汤", "大黄附子汤", "赤丸", "大乌头煎", "当归生姜羊肉汤", "乌头桂枝汤", "温经汤", "胶艾汤", "大黄甘遂汤", "矾石丸", "红蓝花酒", "小建中汤", "黄芪建中汤", "肾气丸", "薯蓣丸", "酸枣仁汤", "大黄䗪虫丸", "鳖甲煎丸", "白虎加桂枝汤", "蜀漆散", "牡蛎汤", "柴胡去半夏加栝楼根汤", "柴胡桂姜汤", "侯氏黑散", "风引汤", "防己地黄汤", "头风摩散", "桂枝芍药知母汤", "乌头汤", "矾石汤", "黄芪桂枝五物汤", "桂枝加龙骨牡蛎汤", "天雄散", "小建中汤", "黄芪建中汤", "薯蓣丸", "酸枣仁汤", "大黄䗪虫丸", "炙甘草汤", "甘草干姜汤", "大建中汤", "附子粳米汤", "厚朴七物汤", "厚朴三物汤", "大柴胡汤", "大黄附子汤", "赤丸", "大乌头煎", "当归生姜羊肉汤", "乌头桂枝汤"]
        
        for formula in common_formulas:
            if formula in query:
                formula_names.append(formula)
                break
    
    if not formula_names:
        # 尝试搜索关键词
        result = app_state.supabase_client.search_jinkui_formulas(query, limit=3)
        if result:
            formatted = app_state.supabase_client.format_results(result, "jinkui_formulas")
            return f"为您找到以下金匮要略相关方剂：\n\n{formatted}"
        return "抱歉，未能从您的问题中识别出方剂名称或症状。请尝试输入具体的方剂名称，或描述相关症状。"
    
    formula_name = formula_names[0]
    result = app_state.supabase_client.query_jinkui_formula(formula_name)
    
    if result:
        formatted = app_state.supabase_client.format_formula(result, "金匮要略")
        return f"为您查询到金匮要略方剂 **{formula_name}** 的信息：\n\n{formatted}"
    else:
        suggestions = app_state.supabase_client.search_jinkui_formulas(formula_name, limit=5)
        if suggestions:
            suggestion_names = [s.get("name", "") for s in suggestions]
            return f"未找到'{formula_name}'，您是否想查询：{', '.join(suggestion_names)}？"
        else:
            return f"抱歉，金匮要略中未找到'{formula_name}'的相关信息。"


async def _handle_rag_query(query: str, sources: List[str]) -> str:
    """处理RAG查询"""
    # 检索相关知识
    results = app_state.vector_store.multi_source_search(query, sources, k_per_source=2)
    
    response = "根据您的问题，我检索到以下相关知识：\n\n"
    
    for source_type, source_results in results.items():
        if source_results:
            source_names = {
                "acupuncture": "📍 针灸",
                "shanghan": "📖 伤寒论",
                "jinkui": "📚 金匮要略",
                "shennong": "🌿 神农本草经",
                "cases": "🏥 医案"
            }
            response += f"\n**{source_names.get(source_type, source_type)}**\n"
            for i, result in enumerate(source_results[:2], 1):
                response += f"{i}. {result.content[:150]}...\n"
    
    return response


def _handle_direct_response(query: str, intent: str) -> str:
    """处理直接回复"""
    if intent == "greeting":
        return "您好！我是中医智能助手，可以帮您查询针灸、中药、伤寒论、金匮要略等中医知识，也可以协助您进行病情分析。请问有什么可以帮助您的？"
    
    elif intent == "unknown":
        return "抱歉，我不太理解您的问题。您可以尝试询问：\n- 针灸穴位信息\n- 中药知识\n- 伤寒论/金匮要略方剂\n- 或者描述您的症状进行分析"
    
    return "请问您想查询哪方面的中医知识？"


# ==================== 启动入口 ====================

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        log_level="info"
    )

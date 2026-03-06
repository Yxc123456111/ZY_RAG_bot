"""
意图识别模块
识别用户查询意图，路由到相应的处理模块
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import re


class IntentType(Enum):
    """意图类型枚举"""
    # 数据库查询类意图
    ACUPUNCTURE_QUERY = "acupuncture_query"      # 针灸查询
    HERB_QUERY = "herb_query"                    # 中药查询
    SHANGHAN_QUERY = "shanghan_query"            # 伤寒论查询
    JINKUI_QUERY = "jinkui_query"                # 金匮要略查询
    
    # RAG类意图
    DIAGNOSIS = "diagnosis"                      # 病情诊断
    GENERAL_KNOWLEDGE = "general_knowledge"      # 一般知识问答
    
    # 其他
    GREETING = "greeting"                        # 问候
    UNKNOWN = "unknown"                          # 未知意图


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: IntentType
    confidence: float
    entities: Dict[str, any]
    original_query: str


class IntentClassifier:
    """
    意图分类器
    使用规则+关键词匹配进行意图识别
    """
    
    # 意图关键词映射
    INTENT_KEYWORDS = {
        IntentType.ACUPUNCTURE_QUERY: [
            "针灸", "穴位", "经络", "针刺", "艾灸", "取穴", "针刺法",
            "足三里", "合谷", "太冲", "内关", "百会", "关元", "气海",
            "针", "灸", "穴", "经", "脉"
        ],
        IntentType.HERB_QUERY: [
            "中药", "草药", "药材", "药性", "药味", "归经", "功效", "本草", "药",
            # 常用中药（按拼音排序，方便维护）
            "人参", "黄芪", "当归", "甘草", "桂枝", "麻黄", "柴胡",
            "白术", "茯苓", "川芎", "熟地黄", "白芍", "生姜", "大枣",
            "半夏", "陈皮", "枳实", "厚朴", "大黄", "黄连", "黄芩",
            "黄柏", "栀子", "连翘", "金银花", "薄荷", "防风", "荆芥",
            "丹砂", "朱砂", "石膏", "知母", "麦冬", "天冬", "枸杞子",
            "菊花", "决明子", "牛膝", "杜仲", "续断", "补骨脂", "菟丝子",
            "五味子", "山茱萸", "牡丹皮", "泽泻", "山药", "附子", "干姜",
            "肉桂", "吴茱萸", "细辛", "葛根", "升麻", "白芷", "蔓荆子",
            "桑叶", "菊花", "银柴胡", "地骨皮", "青蒿", "鳖甲", "龟板",
            "龙骨", "牡蛎", "酸枣仁", "柏子仁", "远志", "合欢皮", "夜交藤",
            "石菖蒲", "麝香", "冰片", "苏合香", "石决明", "羚羊角", "牛黄",
            "钩藤", "天麻", "地龙", "全蝎", "蜈蚣", "僵蚕",
            "天南星", "白附子", "白芥子", "皂荚", "旋覆花", "白前",
            "川贝母", "浙贝母", "瓜蒌", "竹茹", "竹沥", "天竺黄", "前胡",
            "桔梗", "胖大海", "海藻", "昆布", "黄药子", "海蛤壳", "海浮石",
            "瓦楞子", "杏仁", "紫苏子", "百部", "紫菀", "款冬花", "马兜铃",
            "枇杷叶", "桑白皮", "葶苈子", "白果", "磁石", "琥珀",
            "灵芝", "缬草", "西洋参", "党参", "太子参",
            "鹿茸", "紫河车", "淫羊藿", "巴戟天", "仙茅", "肉苁蓉", "锁阳",
            "益智仁", "沙苑子", "韭菜子", "核桃仁", "蛤蚧", "冬虫夏草",
            "胡桃仁", "龙眼肉", "楮实子", "北沙参", "南沙参", "百合",
            "石斛", "玉竹", "黄精", "墨旱莲", "女贞子", "桑葚", "黑芝麻",
            "龟甲", "鳖甲", "乌梅", "五倍子", "罂粟壳", "诃子",
            "肉豆蔻", "赤石脂", "覆盆子", "桑螵蛸", "海螵蛸", "金樱子",
            "莲子", "芡实", "刺猬皮", "椿皮", "石榴皮", "明党参",
            "麻黄根", "浮小麦", "糯稻根须",
            # 截图中提到的中药
            "苦菜", "酸枣仁", "酸枣", "白胶", "干漆", "细辛",
            "龙胆", "龙胆草",
            # 中经药品（112个）
            "猬皮", "梅实", "大豆黄卷", "扈蜂", "蚱蝉", "蛴螬", "蛞蝓", "白僵蚕",
            "樗鸡", "鳖甲", "柞蝉", "露蜂房", "䗪虫", "水蛭", "木虻", "蜚虻",
            "蜚蠊", "䗪虫", "甲香", "蟹", "蛇蜕", "白颈", "蚯蚓", "蟾蜍",
            "蚺蛇胆", "斑猫", "蝼蛄", "蜈蚣", "水蛙", "地胆", "萤火", "衣鱼",
            "鼠妇", "蟅虫", "贝子", "石蚕", "雀瓮", "蜣螂", "蝟皮", "石龙子",
            "王不留行", "细辛", "狗肉", "苦菜", "白兔藿", "蚤休", "石长生",
            "陆英", "蓝实", "藜实", "翘根", "赤芝", "黑芝", "青芝", "白芝",
            "黄芝", "紫芝", "大豆黄卷", "腐婢", "败酱", "恒山", "蜀漆",
            "青木香", "狼牙", "羊踯躅", "茵芋", "射干", "鸢尾", "牙子",
            "商陆", "羊蹄", "萹蓄", "狼毒", "鬼臼", "白头翁", "羊桃",
            "女青", "连翘", "闾茹", "乌韭", "鹿藿", "蚤休", "石长生",
            "陆英", "蓝实", "翘根", "王不留行", "淫羊藿", "射干", "藜实",
            # 其他常见中药
            "参", "芪", "术", "苓", "草", "根", "皮", "花", "叶", "子", "仁", "实"
        ],
        IntentType.SHANGHAN_QUERY: [
            "伤寒论", "伤寒", "张仲景", "六经", "太阳", "阳明", "少阳",
            "太阴", "少阴", "厥阴", "桂枝汤", "麻黄汤", "柴胡汤",
            "经方", "条文"
        ],
        IntentType.JINKUI_QUERY: [
            "金匮要略", "金匮", "杂病", "脏腑", "百合病", "中风",
            "历节", "血痹", "虚劳", "肺痿", "肺痈", "胸痹"
        ],
        IntentType.DIAGNOSIS: [
            "诊断", "辨证", "症状", "证", "脉", "舌", "舌苔",
            "寒热", "虚实", "阴阳", "表里", "气血", "津液",
            "头痛", "发热", "咳嗽", "胸闷", "腹痛", "失眠", "乏力",
            "不舒服", "难受", "疼痛", "怎么办", "怎么治"
            # 注意：移除了单个"病"字，避免与中药查询冲突
        ],
        IntentType.GREETING: [
            "你好", "您好", "嗨", "hello", "hi", "在吗",
            "早上好", "下午好", "晚上好", "谢谢", "再见"
        ]
    }
    
    # 实体提取模式
    ENTITY_PATTERNS = {
        "acupoint": r"([\u4e00-\u9fa5]{2,4}穴)",
        "meridian": r"([\u4e00-\u9fa5]{2,4}经)",
        "herb": r"([\u4e00-\u9fa5]{2,5})(?:药|草|根|皮|花|叶|子|仁|实)",
        "formula": r"([\u4e00-\u9fa5]{2,6}汤|[\u4e00-\u9fa5]{2,6}散|[\u4e00-\u9fa5]{2,6}丸)",
        "symptom": r"(头痛|发热|咳嗽|胸闷|腹痛|失眠|乏力|恶心|呕吐|腹泻|便秘|眩晕|心悸|气短|汗出|畏寒|口渴|口苦|口干|咽痛|腰痛|腿痛|关节痛|麻木|肿胀|皮疹|瘙痒)"
    }
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.compiled_patterns = {
            key: re.compile(pattern) 
            for key, pattern in self.ENTITY_PATTERNS.items()
        }
    
    def classify(self, query: str) -> IntentResult:
        """
        识别用户意图
        
        Args:
            query: 用户查询文本
        
        Returns:
            IntentResult: 意图识别结果
        """
        query = query.strip()
        
        # 首先检查是否是中药查询（使用HerbKeywordExtractor）
        try:
            from core.herb_sql_generator import HerbKeywordExtractor
            extractor = HerbKeywordExtractor()
            herbs = extractor.extract(query)
            if herbs:
                # 如果提取到中药名称，直接判定为中药查询
                entities = self._extract_entities(query)
                entities["herb"] = herbs
                entities["intent_scores"] = {"herb_query": 1.0}
                return IntentResult(
                    intent=IntentType.HERB_QUERY,
                    confidence=1.0,
                    entities=entities,
                    original_query=query
                )
        except Exception:
            pass
        
        # 计算各意图的匹配分数
        scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = self._calculate_score(query, keywords)
            scores[intent] = score
        
        # 找出最高分的意图
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        
        # 如果最高分太低，判定为未知意图
        if best_score < 0.1:
            best_intent = IntentType.UNKNOWN
            best_score = 1.0
        
        # 提取实体
        entities = self._extract_entities(query)
        entities["intent_scores"] = {k.value: round(v, 3) for k, v in scores.items()}
        
        return IntentResult(
            intent=best_intent,
            confidence=best_score,
            entities=entities,
            original_query=query
        )
    
    def _calculate_score(self, query: str, keywords: List[str]) -> float:
        """计算查询与关键词的匹配分数"""
        query_lower = query.lower()
        score = 0.0
        matched_keywords = []
        
        for keyword in keywords:
            if keyword in query:
                # 根据关键词长度给予不同权重
                weight = len(keyword) / 10.0 + 0.5
                score += weight
                matched_keywords.append(keyword)
        
        # 归一化分数
        # 如果查询很短（1-4个字符），或者匹配到了较长的关键词（>=2个字符），
        # 直接返回分数，不进行归一化，避免单个药物名称被稀释
        if matched_keywords:
            # 检查是否有较长的关键词匹配（2个字符以上）
            has_long_match = any(len(kw) >= 2 for kw in matched_keywords)
            if len(query) <= 4 or has_long_match:
                return min(score, 1.0)
        
        # 正常归一化
        if matched_keywords:
            score = min(score / len(keywords) * 10, 1.0)
        
        return score
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """从查询中提取实体"""
        entities = {}
        
        for entity_type, pattern in self.compiled_patterns.items():
            matches = pattern.findall(query)
            if matches:
                # 去重并保持顺序
                seen = set()
                unique_matches = []
                for match in matches:
                    if match not in seen:
                        seen.add(match)
                        unique_matches.append(match)
                entities[entity_type] = unique_matches
        
        return entities
    
    def batch_classify(self, queries: List[str]) -> List[IntentResult]:
        """批量识别意图"""
        return [self.classify(q) for q in queries]


class QueryRouter:
    """
    查询路由器
    根据意图将查询路由到相应的处理模块
    """
    
    def __init__(self):
        self.classifier = IntentClassifier()
        self.handlers = {}
    
    def register_handler(self, intent: IntentType, handler_func):
        """注册意图处理器"""
        self.handlers[intent] = handler_func
    
    def route(self, query: str) -> Dict:
        """
        路由查询到相应处理器
        
        Args:
            query: 用户查询
        
        Returns:
            包含意图、实体和处理建议的字典
        """
        # 识别意图
        intent_result = self.classifier.classify(query)
        
        # 构建路由结果
        route_result = {
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "entities": intent_result.entities,
            "query": query,
            "handler": None,
            "requires_sql": False,
            "requires_rag": False
        }
        
        # 判断需要哪种处理方式
        if intent_result.intent in [
            IntentType.ACUPUNCTURE_QUERY,
            IntentType.HERB_QUERY,
            IntentType.SHANGHAN_QUERY,
            IntentType.JINKUI_QUERY
        ]:
            table_name = self._get_table_name(intent_result.intent)
            route_result["requires_sql"] = True
            route_result["table"] = table_name
            route_result["is_supabase"] = self.is_supabase_table(table_name)  # 标记是否为 Supabase 表
        
        elif intent_result.intent == IntentType.DIAGNOSIS:
            route_result["requires_rag"] = True
            route_result["rag_sources"] = ["acupuncture", "shanghan", "jinkui", "shennong", "cases"]
        
        elif intent_result.intent == IntentType.GENERAL_KNOWLEDGE:
            route_result["requires_rag"] = True
            route_result["rag_sources"] = ["acupuncture", "shanghan", "jinkui", "shennong"]
        
        return route_result
    
    def _get_table_name(self, intent: IntentType) -> str:
        """获取意图对应的数据库表名"""
        table_mapping = {
            IntentType.ACUPUNCTURE_QUERY: "acupoints",
            IntentType.HERB_QUERY: "shennong_herbs",  # 指向 Supabase 的 shennong_herbs 表
            IntentType.SHANGHAN_QUERY: "shanghan_formulas",
            IntentType.JINKUI_QUERY: "jinkui_formulas"
        }
        return table_mapping.get(intent, "")
    
    def is_supabase_table(self, table_name: str) -> bool:
        """判断表是否在 Supabase 中"""
        return table_name == "shennong_herbs"


# 便捷函数
def classify_intent(query: str) -> IntentResult:
    """快速意图分类"""
    classifier = IntentClassifier()
    return classifier.classify(query)


def route_query(query: str) -> Dict:
    """快速路由查询"""
    router = QueryRouter()
    return router.route(query)

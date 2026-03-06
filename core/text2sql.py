"""
Text2SQL模块
将自然语言查询转换为SQL语句
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class SQLType(Enum):
    """SQL查询类型"""
    SELECT = "SELECT"
    AGGREGATE = "AGGREGATE"  # COUNT, SUM, AVG等


@dataclass
class SQLResult:
    """SQL生成结果"""
    sql: str
    params: Dict[str, Any]
    table: str
    explanation: str
    confidence: float


class SchemaManager:
    """
    数据库Schema管理器
    管理各表的字段信息和描述
    """
    
    # 表Schema定义
    SCHEMAS = {
        "acupoints": {
            "description": "穴位信息表",
            "fields": {
                "id": {"type": "INT", "description": "穴位ID"},
                "name": {"type": "VARCHAR", "description": "穴位名称", "searchable": True},
                "pinyin": {"type": "VARCHAR", "description": "拼音", "searchable": True},
                "meridian_id": {"type": "INT", "description": "所属经络ID"},
                "location_description": {"type": "TEXT", "description": "定位描述", "searchable": True},
                "main_indications": {"type": "TEXT", "description": "主治病症", "searchable": True},
                "functions": {"type": "TEXT", "description": "功效", "searchable": True},
                "acupuncture_method": {"type": "TEXT", "description": "针刺方法"},
                "moxibustion": {"type": "TEXT", "description": "艾灸方法"},
                "contraindications": {"type": "TEXT", "description": "禁忌"},
                "source": {"type": "VARCHAR", "description": "出处"}
            }
        },
        "meridians": {
            "description": "经络表",
            "fields": {
                "id": {"type": "INT", "description": "经络ID"},
                "name": {"type": "VARCHAR", "description": "经络名称", "searchable": True},
                "nature": {"type": "VARCHAR", "description": "阴阳属性"},
                "hand_foot": {"type": "VARCHAR", "description": "手足"},
                "zang_fu": {"type": "VARCHAR", "description": "脏腑", "searchable": True},
                "circulation_route": {"type": "TEXT", "description": "循行路线", "searchable": True},
                "main_symptoms": {"type": "TEXT", "description": "主要病症", "searchable": True}
            }
        },
        "herbs": {
            "description": "中药表",
            "fields": {
                "id": {"type": "INT", "description": "中药ID"},
                "name": {"type": "VARCHAR", "description": "中药名称", "searchable": True},
                "alias": {"type": "JSON", "description": "别名", "searchable": True},
                "category_id": {"type": "INT", "description": "分类ID"},
                "nature": {"type": "VARCHAR", "description": "药性", "searchable": True},
                "flavor": {"type": "VARCHAR", "description": "药味", "searchable": True},
                "meridian_tropism": {"type": "VARCHAR", "description": "归经", "searchable": True},
                "functions": {"type": "TEXT", "description": "功效", "searchable": True},
                "main_indications": {"type": "TEXT", "description": "主治病症", "searchable": True},
                "usage_dosage": {"type": "TEXT", "description": "用法用量"},
                "precautions": {"type": "TEXT", "description": "使用注意"},
                "contraindications": {"type": "TEXT", "description": "禁忌"},
                "classic_source": {"type": "VARCHAR", "description": "经典出处"}
            }
        },
        "shennong_herbs": {
            "description": "神农本草经草药表 (Supabase)",
            "fields": {
                "id": {"type": "INT", "description": "草药ID"},
                "drug_name": {"type": "VARCHAR", "description": "药物名称", "searchable": True},
                "original_text": {"type": "TEXT", "description": "本经原文", "searchable": True},
                "origin": {"type": "TEXT", "description": "产地", "searchable": True},
                "indications": {"type": "TEXT", "description": "主治", "searchable": True},
                "properties": {"type": "TEXT", "description": "性味", "searchable": True},
                "dosage": {"type": "TEXT", "description": "用量"},
                "contraindications": {"type": "TEXT", "description": "禁忌"},
                "other1": {"type": "TEXT", "description": "其他信息1"},
                "other1_name": {"type": "VARCHAR", "description": "其他信息1名称"},
                "other2": {"type": "TEXT", "description": "其他信息2"},
                "other2_name": {"type": "VARCHAR", "description": "其他信息2名称"}
            }
        },
        "shanghan_formulas": {
            "description": "伤寒论方剂表",
            "fields": {
                "id": {"type": "INT", "description": "方剂ID"},
                "name": {"type": "VARCHAR", "description": "方剂名称", "searchable": True},
                "number": {"type": "VARCHAR", "description": "条文编号", "searchable": True},
                "composition": {"type": "TEXT", "description": "组成药物", "searchable": True},
                "functions": {"type": "TEXT", "description": "功效", "searchable": True},
                "main_indications": {"type": "TEXT", "description": "主治症状", "searchable": True},
                "symptoms_detail": {"type": "TEXT", "description": "症状详情", "searchable": True},
                "pathogenesis": {"type": "TEXT", "description": "病机分析", "searchable": True},
                "formula_analysis": {"type": "TEXT", "description": "方解", "searchable": True},
                "original_text": {"type": "TEXT", "description": "原文", "searchable": True},
                "source_chapter": {"type": "VARCHAR", "description": "所属篇章", "searchable": True}
            }
        },
        "jinkui_formulas": {
            "description": "金匮要略方剂表",
            "fields": {
                "id": {"type": "INT", "description": "方剂ID"},
                "name": {"type": "VARCHAR", "description": "方剂名称", "searchable": True},
                "number": {"type": "VARCHAR", "description": "条文编号", "searchable": True},
                "chapter": {"type": "VARCHAR", "description": "所属篇章", "searchable": True},
                "disease_category": {"type": "VARCHAR", "description": "病证分类", "searchable": True},
                "composition": {"type": "TEXT", "description": "组成药物", "searchable": True},
                "functions": {"type": "TEXT", "description": "功效", "searchable": True},
                "main_indications": {"type": "TEXT", "description": "主治症状", "searchable": True},
                "symptoms_detail": {"type": "TEXT", "description": "症状详情", "searchable": True},
                "original_text": {"type": "TEXT", "description": "原文", "searchable": True}
            }
        }
    }
    
    @classmethod
    def get_schema(cls, table_name: str) -> Optional[Dict]:
        """获取表Schema"""
        return cls.SCHEMAS.get(table_name)
    
    @classmethod
    def get_searchable_fields(cls, table_name: str) -> List[str]:
        """获取可搜索字段"""
        schema = cls.get_schema(table_name)
        if not schema:
            return []
        
        return [
            field_name for field_name, field_info in schema["fields"].items()
            if field_info.get("searchable", False)
        ]
    
    @classmethod
    def get_schema_description(cls, table_name: str) -> str:
        """获取表的Schema描述（用于Prompt）"""
        schema = cls.get_schema(table_name)
        if not schema:
            return ""
        
        lines = [f"表名: {table_name} ({schema['description']})"]
        lines.append("字段:")
        
        for field_name, field_info in schema["fields"].items():
            searchable = " [可搜索]" if field_info.get("searchable") else ""
            lines.append(f"  - {field_name} ({field_info['type']}): {field_info['description']}{searchable}")
        
        return "\n".join(lines)


class Text2SQLConverter:
    """
    自然语言转SQL转换器
    支持基于规则和LLM两种方式
    """
    
    # 查询模式定义
    QUERY_PATTERNS = {
        "acupoints": {
            "穴位定位": ["哪里", "在哪", "位置", "定位", "取穴"],
            "穴位主治": ["治什么", "主治", "治疗", "功效", "作用"],
            "经络穴位": ["经络", "属于", "归经"],
            "针刺方法": ["怎么针", "针刺", "刺法", "针多深"],
            "特定穴位": ["足三里", "合谷", "太冲", "内关", "百会", "关元", "气海", "三阴交"]
        },
        "herbs": {
            "药性查询": ["性味", "寒热", "温凉", "辛甘酸苦咸"],
            "功效查询": ["功效", "作用", "治什么"],
            "归经查询": ["归经", "入哪经"],
            "用法用量": ["怎么用", "用量", "剂量", "煎服"],
            "禁忌查询": ["禁忌", "注意", "副作用", "不能用"]
        },
        "shennong_herbs": {
            "本经查询": ["本经", "原文", "神农本草经"],
            "性味查询": ["性味", "寒热", "温凉", "辛甘酸苦咸"],
            "主治查询": ["主治", "治什么", "功效"],
            "产地查询": ["产地", "哪里产", "出自"],
            "用量查询": ["用量", "怎么用", "剂量"],
            "禁忌查询": ["禁忌", "注意", "不能用"]
        },
        "shanghan_formulas": {
            "方剂组成": ["组成", "有什么药", "药物"],
            "方剂功效": ["功效", "治什么", "主治"],
            "条文查询": ["第几条", "条文", "原文"],
            "症状对应": ["症状", "表现", "证候"],
            "方剂比较": ["区别", "比较", "不同", "类方"]
        },
        "jinkui_formulas": {
            "方剂组成": ["组成", "有什么药", "药物"],
            "方剂功效": ["功效", "治什么", "主治"],
            "篇章查询": ["哪一篇", "篇章", "章节"],
            "病证分类": ["病证", "分类", "属于什么病"]
        }
    }
    
    def __init__(self, use_llm: bool = False, llm_client=None):
        self.use_llm = use_llm
        self.llm_client = llm_client
        self.schema_manager = SchemaManager()
    
    def convert(
        self,
        query: str,
        table_name: str,
        intent_entities: Optional[Dict] = None
    ) -> SQLResult:
        """
        将自然语言查询转换为SQL
        
        Args:
            query: 自然语言查询
            table_name: 目标表名
            intent_entities: 意图识别提取的实体
        
        Returns:
            SQLResult对象
        """
        if self.use_llm and self.llm_client:
            return self._convert_with_llm(query, table_name)
        else:
            return self._convert_with_rules(query, table_name, intent_entities)
    
    def _convert_with_rules(
        self,
        query: str,
        table_name: str,
        intent_entities: Optional[Dict] = None
    ) -> SQLResult:
        """基于规则转换"""
        
        # 获取可搜索字段
        searchable_fields = self.schema_manager.get_searchable_fields(table_name)
        
        # 提取查询关键词
        keywords = self._extract_keywords(query)
        
        # 构建WHERE条件
        conditions = []
        params = {}
        
        # 1. 实体匹配
        if intent_entities:
            for entity_type, entities in intent_entities.items():
                if entities and isinstance(entities, list):
                    for entity in entities:
                        # 根据实体类型映射到字段
                        field_mapping = {
                            "acupoint": "name",
                            "meridian": "meridian_tropism",
                            "herb": "name",
                            "formula": "name",
                            "symptom": "main_indications"
                        }
                        if entity_type in field_mapping:
                            field = field_mapping[entity_type]
                            if field in searchable_fields:
                                param_key = f"param_{len(params)}"
                                conditions.append(f"{field} LIKE %({param_key})s")
                                params[param_key] = f"%{entity}%"
        
        # 2. 关键词匹配
        for keyword in keywords:
            param_key = f"param_{len(params)}"
            # 在多个可搜索字段中匹配
            field_conditions = []
            for field in searchable_fields[:3]:  # 限制字段数量
                field_conditions.append(f"{field} LIKE %({param_key})s")
            
            if field_conditions:
                conditions.append(f"({' OR '.join(field_conditions)})")
                params[param_key] = f"%{keyword}%"
        
        # 构建SQL
        if conditions:
            where_clause = " OR ".join(conditions)
            sql = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 10"
        else:
            # 如果没有条件，返回空结果
            sql = f"SELECT * FROM {table_name} WHERE 1=0"
        
        explanation = f"查询表 {table_name}，关键词: {', '.join(keywords)}"
        
        return SQLResult(
            sql=sql,
            params=params,
            table=table_name,
            explanation=explanation,
            confidence=0.7 if conditions else 0.3
        )
    
    def _convert_with_llm(self, query: str, table_name: str) -> SQLResult:
        """使用LLM转换"""
        # 这里需要实现LLM调用
        # 暂时返回基于规则的结果
        return self._convert_with_rules(query, table_name, None)
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取查询关键词"""
        # 停用词
        stop_words = {
            "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那"
        }
        
        # 去除标点，分词
        import re
        words = re.findall(r'[\u4e00-\u9fa5]+', query)
        
        # 过滤停用词和短词
        keywords = []
        for word in words:
            if len(word) >= 2 and word not in stop_words:
                keywords.append(word)
        
        return keywords
    
    def generate_explanation(self, sql: str, results: List[Dict]) -> str:
        """生成查询结果的自然语言解释"""
        if not results:
            return "未找到相关信息。"
        
        count = len(results)
        explanation = f"找到 {count} 条相关记录。"
        
        return explanation


class SQLExecutor:
    """
    SQL执行器
    通过Supabase执行查询并格式化结果
    """
    
    def __init__(self, supabase_client=None):
        self.supabase_client = supabase_client
    
    async def execute(self, sql_result: SQLResult) -> Dict:
        """
        执行SQL查询（通过Supabase）
        
        Args:
            sql_result: SQL生成结果
        
        Returns:
            查询结果字典
        """
        if not self.supabase_client:
            return {
                "success": False,
                "error": "Supabase client not configured",
                "sql": sql_result.sql
            }
        
        try:
            # 获取表名
            table = sql_result.table
            
            # 提取关键词
            keywords = self._extract_keywords_from_sql(sql_result.sql)
            keyword = keywords[0] if keywords else ""
            
            # 根据表类型调用不同的查询方法
            if table == "shennong_herbs":
                results = self.supabase_client.search_shennong_herbs(keyword, limit=10) if keyword else []
            elif table == "acupoints":
                results = self.supabase_client.search_acupoints(keyword, limit=10) if keyword else []
            elif table == "shanghan_formulas":
                results = self.supabase_client.search_shanghan_formulas(keyword, limit=10) if keyword else []
            elif table == "jinkui_formulas":
                results = self.supabase_client.search_jinkui_formulas(keyword, limit=10) if keyword else []
            else:
                return {
                    "success": False,
                    "error": f"Unsupported table: {table}",
                    "sql": sql_result.sql
                }
            
            return {
                "success": True,
                "data": results,
                "count": len(results),
                "sql": sql_result.sql,
                "explanation": sql_result.explanation
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql_result.sql
            }
    
    def _extract_keywords_from_sql(self, sql: str) -> List[str]:
        """从SQL中提取关键词（简化版）"""
        import re
        # 提取LIKE子句中的关键词
        matches = re.findall(r"LIKE\s+['\"]?%(\w+)%['\"]?", sql, re.IGNORECASE)
        return matches if matches else []
    
    def format_results(self, results: List[Dict], table_name: str) -> str:
        """
        格式化查询结果为自然语言
        
        Args:
            results: 查询结果列表
            table_name: 表名
        
        Returns:
            格式化后的文本
        """
        if not results:
            return "抱歉，没有找到相关信息。"
        
        formatters = {
            "acupoints": self._format_acupoint,
            "herbs": self._format_herb,
            "shennong_herbs": self._format_shennong_herb,
            "shanghan_formulas": self._format_shanghan_formula,
            "jinkui_formulas": self._format_jinkui_formula
        }
        
        formatter = formatters.get(table_name, self._format_generic)
        
        formatted_results = []
        for i, result in enumerate(results[:5], 1):  # 最多显示5条
            formatted_results.append(f"【{i}】{formatter(result)}")
        
        return "\n\n".join(formatted_results)
    
    def _format_acupoint(self, data: Dict) -> str:
        """格式化穴位信息"""
        lines = [f"**{data.get('name', '未知')}**"]
        if data.get('location_description'):
            lines.append(f"📍 定位：{data['location_description']}")
        if data.get('main_indications'):
            lines.append(f"🏥 主治：{data['main_indications'][:100]}...")
        if data.get('functions'):
            lines.append(f"✨ 功效：{data['functions'][:100]}...")
        return "\n".join(lines)
    
    def _format_herb(self, data: Dict) -> str:
        """格式化中药信息"""
        lines = [f"**{data.get('name', '未知')}**"]
        if data.get('nature') or data.get('flavor'):
            nature_flavor = f"{data.get('nature', '')}{data.get('flavor', '')}"
            lines.append(f"🌿 性味：{nature_flavor}")
        if data.get('meridian_tropism'):
            lines.append(f"📍 归经：{data['meridian_tropism']}")
        if data.get('functions'):
            lines.append(f"✨ 功效：{data['functions'][:100]}...")
        return "\n".join(lines)
    
    def _format_shennong_herb(self, data: Dict) -> str:
        """格式化神农本草经草药信息"""
        lines = [f"**{data.get('drug_name', '未知药物')}**"]
        
        if data.get('original_text'):
            lines.append(f"📖 本经原文：{data['original_text'][:200]}...")
        
        if data.get('properties'):
            lines.append(f"🌿 性味：{data['properties']}")
        
        if data.get('origin'):
            lines.append(f"📍 产地：{data['origin']}")
        
        if data.get('indications'):
            lines.append(f"💊 主治：{data['indications'][:150]}...")
        
        if data.get('dosage'):
            lines.append(f"📋 用量：{data['dosage']}")
        
        if data.get('contraindications'):
            lines.append(f"⚠️ 禁忌：{data['contraindications']}")
        
        return "\n".join(lines)
    
    def _format_shanghan_formula(self, data: Dict) -> str:
        """格式化伤寒论方剂"""
        lines = [f"**{data.get('name', '未知')}**"]
        if data.get('number'):
            lines.append(f"📖 条文：第{data['number']}条")
        if data.get('composition'):
            lines.append(f"💊 组成：{data['composition'][:100]}...")
        if data.get('main_indications'):
            lines.append(f"🏥 主治：{data['main_indications'][:100]}...")
        return "\n".join(lines)
    
    def _format_jinkui_formula(self, data: Dict) -> str:
        """格式化金匮要略方剂"""
        lines = [f"**{data.get('name', '未知')}**"]
        if data.get('chapter'):
            lines.append(f"📖 篇章：{data['chapter']}")
        if data.get('composition'):
            lines.append(f"💊 组成：{data['composition'][:100]}...")
        if data.get('main_indications'):
            lines.append(f"🏥 主治：{data['main_indications'][:100]}...")
        return "\n".join(lines)
    
    def _format_generic(self, data: Dict) -> str:
        """通用格式化"""
        return "\n".join([f"{k}: {v}" for k, v in list(data.items())[:5]])


# 便捷函数
def create_text2sql_converter(use_llm: bool = False, llm_client=None) -> Text2SQLConverter:
    """创建Text2SQL转换器"""
    return Text2SQLConverter(use_llm=use_llm, llm_client=llm_client)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 数据库客户端
统一访问：神农本草经、针灸、伤寒论、金匮要略等数据
"""

import os
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class QueryResult:
    """查询结果"""
    success: bool
    data: List[Dict]
    count: int
    error: Optional[str] = None
    sql: Optional[str] = None


class SupabaseClient:
    """
    Supabase 统一数据库客户端
    
    支持表：
    - shennong_herbs: 神农本草经
    - acupoints: 针灸穴位
    - shanghan_formulas: 伤寒论方剂
    - jinkui_formulas: 金匮要略方剂
    """
    
    # 表名映射
    TABLE_MAP = {
        "shennong_herbs": "神农本草经",
        "acupoints": "针灸穴位",
        "meridians": "经络",
        "shanghan_formulas": "伤寒论方剂",
        "jinkui_formulas": "金匮要略方剂",
        "herbs": "中药"
    }
    
    def __init__(self, project_url: str, api_key: str):
        """
        初始化客户端
        
        Args:
            project_url: Supabase Project URL
            api_key: Supabase API Key (anon key 或 service role key)
        """
        self.project_url = project_url.rstrip('/')
        self.api_key = api_key
        self.rest_url = f"{self.project_url}/rest/v1"
        
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                      data: Optional[Dict] = None) -> tuple:
        """发送HTTP请求"""
        url = f"{self.rest_url}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=15)
            else:
                return None, f"不支持的HTTP方法: {method}"
            
            if response.status_code in [200, 201]:
                return response.json(), None
            else:
                return None, f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return None, "请求超时"
        except requests.exceptions.ConnectionError:
            return None, "连接失败，请检查网络或Supabase配置"
        except Exception as e:
            return None, f"请求异常: {str(e)}"
    
    # ==================== 神农本草经 ====================
    
    def query_shennong_herb(self, drug_name: str) -> Optional[Dict]:
        """根据药物名称查询神农本草经"""
        params = {
            "drug_name": f"eq.{drug_name}",
            "limit": "1"
        }
        
        data, error = self._make_request("GET", "shennong_herbs", params=params)
        
        if error:
            print(f"[Error] 查询神农本草经失败: {error}")
            return None
        
        if data and len(data) > 0:
            return self._format_shennong_herb(data[0])
        return None
    
    def search_shennong_herbs(self, keyword: str, limit: int = 10) -> List[Dict]:
        """搜索神农本草经药物"""
        params = {
            "or": f"(drug_name.ilike.*{keyword}*,indications.ilike.*{keyword}*)",
            "limit": str(limit)
        }
        
        data, error = self._make_request("GET", "shennong_herbs", params=params)
        
        if error:
            print(f"[Error] 搜索神农本草经失败: {error}")
            return []
        
        return [self._format_shennong_herb(item) for item in data] if data else []
    
    def _format_shennong_herb(self, data: Dict) -> Dict:
        """格式化神农本草经结果"""
        result = {
            "id": data.get("id"),
            "drug_name": data.get("drug_name", ""),
            "original_text": data.get("original_text", ""),
            "origin": data.get("origin", ""),
            "indications": data.get("indications", ""),
            "properties": data.get("properties", ""),
            "dosage": data.get("dosage", ""),
            "contraindications": data.get("contraindications", ""),
        }
        
        # 添加其他字段
        for i in range(1, 12):
            other_key = f"other{i}"
            other_name_key = f"other{i}_name"
            if data.get(other_key):
                result[other_key] = data[other_key]
                result[other_name_key] = data.get(other_name_key, "")
        
        return result
    
    # ==================== 针灸 ====================
    
    def query_acupoint(self, name: str) -> Optional[Dict]:
        """根据穴位名称查询"""
        params = {
            "name": f"eq.{name}",
            "limit": "1"
        }
        
        data, error = self._make_request("GET", "acupoints", params=params)
        
        if error:
            print(f"[Error] 查询穴位失败: {error}")
            return None
        
        if data and len(data) > 0:
            return self._format_acupoint(data[0])
        return None
    
    def search_acupoints(self, keyword: str, limit: int = 10) -> List[Dict]:
        """搜索穴位"""
        params = {
            "or": f"(name.ilike.*{keyword}*,main_indications.ilike.*{keyword}*,functions.ilike.*{keyword}*)",
            "limit": str(limit)
        }
        
        data, error = self._make_request("GET", "acupoints", params=params)
        
        if error:
            print(f"[Error] 搜索穴位失败: {error}")
            return []
        
        return [self._format_acupoint(item) for item in data] if data else []
    
    def _format_acupoint(self, data: Dict) -> Dict:
        """格式化穴位结果"""
        return {
            "id": data.get("id"),
            "name": data.get("name", ""),
            "code": data.get("code", ""),
            "meridian": data.get("meridian", ""),
            "location": data.get("location", ""),
            "location_method": data.get("location_method", ""),
            "main_indications": data.get("main_indications", ""),
            "functions": data.get("functions", ""),
            "acupuncture_method": data.get("acupuncture_method", ""),
            "moxibustion": data.get("moxibustion", ""),
            "contraindications": data.get("contraindications", "")
        }
    
    # ==================== 伤寒论 ====================
    
    def query_shanghan_formula(self, name: str) -> Optional[Dict]:
        """根据方剂名称查询伤寒论"""
        params = {
            "name": f"eq.{name}",
            "limit": "1"
        }
        
        data, error = self._make_request("GET", "shanghan_formulas", params=params)
        
        if error:
            print(f"[Error] 查询伤寒论方剂失败: {error}")
            return None
        
        if data and len(data) > 0:
            return self._format_shanghan_formula(data[0])
        return None
    
    def search_shanghan_formulas(self, keyword: str, limit: int = 10) -> List[Dict]:
        """搜索伤寒论方剂"""
        params = {
            "or": f"(name.ilike.*{keyword}*,composition.ilike.*{keyword}*,main_indications.ilike.*{keyword}*)",
            "limit": str(limit)
        }
        
        data, error = self._make_request("GET", "shanghan_formulas", params=params)
        
        if error:
            print(f"[Error] 搜索伤寒论方剂失败: {error}")
            return []
        
        return [self._format_shanghan_formula(item) for item in data] if data else []
    
    def _format_shanghan_formula(self, data: Dict) -> Dict:
        """格式化伤寒论方剂结果"""
        return {
            "id": data.get("id"),
            "name": data.get("name", ""),
            "number": data.get("number", ""),
            "composition": data.get("composition", ""),
            "functions": data.get("functions", ""),
            "main_indications": data.get("main_indications", ""),
            "symptoms_detail": data.get("symptoms_detail", ""),
            "pathogenesis": data.get("pathogenesis", ""),
            "formula_analysis": data.get("formula_analysis", ""),
            "preparation": data.get("preparation", ""),
            "original_text": data.get("original_text", "")
        }
    
    # ==================== 金匮要略 ====================
    
    def query_jinkui_formula(self, name: str) -> Optional[Dict]:
        """根据方剂名称查询金匮要略"""
        params = {
            "name": f"eq.{name}",
            "limit": "1"
        }
        
        data, error = self._make_request("GET", "jinkui_formulas", params=params)
        
        if error:
            print(f"[Error] 查询金匮要略方剂失败: {error}")
            return None
        
        if data and len(data) > 0:
            return self._format_jinkui_formula(data[0])
        return None
    
    def search_jinkui_formulas(self, keyword: str, limit: int = 10) -> List[Dict]:
        """搜索金匮要略方剂"""
        params = {
            "or": f"(name.ilike.*{keyword}*,composition.ilike.*{keyword}*,main_indications.ilike.*{keyword}*,chapter.ilike.*{keyword}*)",
            "limit": str(limit)
        }
        
        data, error = self._make_request("GET", "jinkui_formulas", params=params)
        
        if error:
            print(f"[Error] 搜索金匮要略方剂失败: {error}")
            return []
        
        return [self._format_jinkui_formula(item) for item in data] if data else []
    
    def _format_jinkui_formula(self, data: Dict) -> Dict:
        """格式化金匮要略方剂结果"""
        return {
            "id": data.get("id"),
            "name": data.get("name", ""),
            "number": data.get("number", ""),
            "chapter": data.get("chapter", ""),
            "disease_category": data.get("disease_category", ""),
            "composition": data.get("composition", ""),
            "functions": data.get("functions", ""),
            "main_indications": data.get("main_indications", ""),
            "symptoms_detail": data.get("symptoms_detail", ""),
            "pathogenesis": data.get("pathogenesis", ""),
            "formula_analysis": data.get("formula_analysis", ""),
            "original_text": data.get("original_text", "")
        }
    
    # ==================== 通用查询 ====================
    
    def query_by_table(self, table: str, column: str, value: str) -> QueryResult:
        """
        根据表和列查询
        
        Args:
            table: 表名
            column: 列名
            value: 值
        
        Returns:
            QueryResult
        """
        params = {
            column: f"eq.{value}",
            "limit": "10"
        }
        
        data, error = self._make_request("GET", table, params=params)
        
        if error:
            return QueryResult(success=False, data=[], count=0, error=error)
        
        return QueryResult(success=True, data=data or [], count=len(data) if data else 0)
    
    def search_table(self, table: str, keyword: str, search_columns: List[str], 
                     limit: int = 10) -> QueryResult:
        """
        在指定表中搜索
        
        Args:
            table: 表名
            keyword: 关键词
            search_columns: 搜索列列表
            limit: 限制数量
        
        Returns:
            QueryResult
        """
        # 构建OR条件
        or_conditions = ",".join([f"{col}.ilike.*{keyword}*" for col in search_columns])
        params = {
            "or": f"({or_conditions})",
            "limit": str(limit)
        }
        
        data, error = self._make_request("GET", table, params=params)
        
        if error:
            return QueryResult(success=False, data=[], count=0, error=error)
        
        return QueryResult(success=True, data=data or [], count=len(data) if data else 0)
    
    # ==================== 格式化输出 ====================
    
    def _clean_text(self, text: str) -> str:
        """清理文本，移除以 > 开头的额外解释段落"""
        if not text:
            return ""
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # 跳过以 > 开头的行（额外解释）
            if stripped.startswith('>'):
                continue
            # 跳过空行
            if stripped:
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
    def format_shennong_herb(self, herb: Dict) -> str:
        """格式化神农本草经药物信息为可读文本"""
        lines = []
        lines.append(f"【{herb.get('drug_name', '未知药物')}】")
        lines.append("")
        
        if herb.get('original_text'):
            lines.append("[本经原文]")
            lines.append(self._clean_text(herb['original_text']))
            lines.append("")
        
        if herb.get('properties'):
            lines.append("[性味]")
            lines.append(self._clean_text(herb['properties']))
            lines.append("")
        
        if herb.get('origin'):
            lines.append("[产地]")
            lines.append(self._clean_text(herb['origin']))
            lines.append("")
        
        if herb.get('indications'):
            lines.append("[主治]")
            lines.append(self._clean_text(herb['indications']))
            lines.append("")
        
        if herb.get('dosage'):
            lines.append("[用量]")
            lines.append(self._clean_text(herb['dosage']))
            lines.append("")
        
        if herb.get('contraindications'):
            lines.append("[禁忌]")
            lines.append(self._clean_text(herb['contraindications']))
            lines.append("")
        
        # 添加其他字段（历代医家论述）
        for i in range(1, 12):
            other_name = herb.get(f"other{i}_name")
            other_content = herb.get(f"other{i}")
            if other_name and other_content:
                cleaned_content = self._clean_text(other_content)
                if cleaned_content:
                    lines.append(f"[{other_name}]")
                    lines.append(cleaned_content)
                    lines.append("")
        
        # 添加查询出处
        lines.append("─" * 40)
        lines.append("📚 查询出处：神农本草经")
        lines.append("数据来源：Supabase 数据库")
        
        return "\n".join(lines)
    
    def format_acupoint(self, point: Dict) -> str:
        """格式化穴位信息"""
        lines = []
        lines.append(f"【{point.get('name', '未知穴位')}】")
        
        if point.get('meridian'):
            lines.append(f"📍 经络：{point['meridian']}")
        
        if point.get('location'):
            lines.append(f"📍 定位：{point['location']}")
        
        if point.get('main_indications'):
            lines.append(f"🏥 主治：{point['main_indications']}")
        
        if point.get('functions'):
            lines.append(f"✨ 功效：{point['functions']}")
        
        if point.get('acupuncture_method'):
            lines.append(f"💉 针刺：{point['acupuncture_method']}")
        
        return "\n".join(lines)
    
    def format_formula(self, formula: Dict, source: str = "") -> str:
        """格式化方剂信息"""
        lines = []
        lines.append(f"【{formula.get('name', '未知方剂')}】")
        
        if source:
            lines.append(f"📚 来源：{source}")
        
        if formula.get('number'):
            lines.append(f"📖 编号：第{formula['number']}条")
        
        if formula.get('chapter'):
            lines.append(f"📖 篇章：{formula['chapter']}")
        
        if formula.get('composition'):
            lines.append(f"💊 组成：{formula['composition']}")
        
        if formula.get('functions'):
            lines.append(f"✨ 功效：{formula['functions']}")
        
        if formula.get('main_indications'):
            lines.append(f"🏥 主治：{formula['main_indications']}")
        
        if formula.get('original_text'):
            lines.append(f"📜 原文：{formula['original_text']}")
        
        return "\n".join(lines)
    
    def format_results(self, results: List[Dict], table: str) -> str:
        """通用格式化结果"""
        if not results:
            return "未找到相关信息。"
        
        formatters = {
            "shennong_herbs": self.format_shennong_herb,
            "acupoints": self.format_acupoint,
            "shanghan_formulas": lambda x: self.format_formula(x, "伤寒论"),
            "jinkui_formulas": lambda x: self.format_formula(x, "金匮要略")
        }
        
        formatter = formatters.get(table, lambda x: str(x))
        
        formatted = []
        for i, result in enumerate(results[:5], 1):
            formatted.append(f"【{i}】\n{formatter(result)}")
        
        return "\n\n".join(formatted)


# ==================== 便捷函数 ====================

def create_supabase_client() -> Optional[SupabaseClient]:
    """
    从环境变量或配置文件创建客户端
    
    需要的配置：
    - SUPABASE_URL: Project URL
    - SUPABASE_KEY: API Key
    """
    # 首先尝试从 config_manager 读取
    try:
        from config_manager import get_config
        config = get_config()
        project_url = config.get('SUPABASE_URL', '')
        api_key = config.get('SUPABASE_KEY', '')
        
        if project_url and api_key:
            return SupabaseClient(project_url, api_key)
    except Exception:
        pass
    
    # 回退到环境变量
    project_url = os.getenv("SUPABASE_URL")
    api_key = os.getenv("SUPABASE_KEY")
    
    if not project_url or not api_key:
        return None
    
    return SupabaseClient(project_url, api_key)


# 兼容性：保持旧的客户端可用
SupabaseHerbClient = SupabaseClient
create_client_from_env = create_supabase_client

"""
病情诊断引擎
基于RAG的中医诊断分析模块
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class DiagnosisResult:
    """诊断结果"""
    syndrome_type: str                    # 证型
    pathogenesis: str                     # 病机分析
    treatment_principle: str              # 治则
    recommendations: List[Dict]           # 推荐方案
    analysis: str                         # 详细分析
    sources: List[Dict]                   # 参考来源
    confidence: float                     # 置信度
    warnings: List[str]                   # 警告提示


@dataclass
class Recommendation:
    """推荐方案"""
    type: str                             # 类型：acupuncture/herb/formula
    name: str                             # 名称
    content: str                          # 具体内容
    source: str                           # 出处
    rationale: str                        # 选用理由


class DiagnosisEngine:
    """
    中医诊断引擎
    结合RAG检索和LLM分析进行病情诊断
    """
    
    # 四诊信息提取模式
    INQUIRY_PATTERNS = {
        "主诉": ["主诉", "主要是", "主要是", "主要是"],
        "现病史": ["最近", "这几天", "这段时间", "一直"],
        "症状": ["症状", "表现", "感觉", "不舒服"],
        "舌象": ["舌", "舌苔", "舌质", "舌色"],
        "脉象": ["脉", "脉搏", "脉象"],
        "寒热": ["怕冷", "怕热", "发热", "畏寒", "寒热"],
        "汗出": ["出汗", "汗出", "盗汗", "自汗"],
        "饮食": ["食欲", "吃饭", "胃口", "饮食"],
        "睡眠": ["睡眠", "睡觉", "失眠", "多梦"],
        "二便": ["大便", "小便", "便秘", "腹泻", "尿频"]
    }
    
    def __init__(self, vector_store, llm_client=None):
        self.vector_store = vector_store
        self.llm_client = llm_client
    
    async def diagnose(
        self,
        patient_description: str,
        include_sources: List[str] = None
    ) -> DiagnosisResult:
        """
        进行病情诊断
        
        Args:
            patient_description: 患者病情描述
            include_sources: 包含的知识来源类型
        
        Returns:
            DiagnosisResult: 诊断结果
        """
        if include_sources is None:
            include_sources = ["acupuncture", "shanghan", "jinkui", "shennong", "cases"]
        
        # 1. 提取四诊信息
        inquiry_info = self._extract_inquiry_info(patient_description)
        
        # 2. RAG检索相关知识
        retrieved_knowledge = self._retrieve_knowledge(
            patient_description,
            include_sources
        )
        
        # 3. 分析病情
        analysis = await self._analyze_condition(
            inquiry_info,
            retrieved_knowledge
        )
        
        # 4. 生成推荐方案
        recommendations = self._generate_recommendations(
            analysis,
            retrieved_knowledge
        )
        
        # 5. 组装结果
        result = DiagnosisResult(
            syndrome_type=analysis.get("syndrome_type", "待进一步辨证"),
            pathogenesis=analysis.get("pathogenesis", ""),
            treatment_principle=analysis.get("treatment_principle", ""),
            recommendations=recommendations,
            analysis=analysis.get("detailed_analysis", ""),
            sources=retrieved_knowledge.get("sources", []),
            confidence=analysis.get("confidence", 0.5),
            warnings=self._generate_warnings(analysis)
        )
        
        return result
    
    def _extract_inquiry_info(self, description: str) -> Dict[str, Any]:
        """
        提取四诊信息
        
        Args:
            description: 患者描述
        
        Returns:
            结构化的四诊信息
        """
        inquiry_info = {
            "raw_description": description,
            "extracted_time": datetime.now().isoformat()
        }
        
        # 使用正则表达式提取各类信息
        import re
        
        # 提取症状（常见症状关键词）
        symptom_keywords = [
            "头痛", "头晕", "发热", "恶寒", "怕冷", "出汗", "咳嗽", "咳痰",
            "胸闷", "胸痛", "心悸", "气短", "乏力", "倦怠", "食欲不振",
            "恶心", "呕吐", "腹胀", "腹痛", "腹泻", "便秘", "失眠", "多梦",
            "口干", "口苦", "口渴", "咽痛", "腰痛", "关节痛", "麻木", "浮肿"
        ]
        
        found_symptoms = []
        for symptom in symptom_keywords:
            if symptom in description:
                found_symptoms.append(symptom)
        inquiry_info["symptoms"] = found_symptoms
        
        # 提取舌象
        tongue_patterns = [
            r"舌[苔质]*([淡红绛紫青])",
            r"舌[苔质]*([胖大瘦薄])",
            r"舌苔([白黄灰黑])",
            r"舌苔([薄厚腻])",
            r"舌[有]*([裂纹齿痕])"
        ]
        
        tongue_findings = []
        for pattern in tongue_patterns:
            matches = re.findall(pattern, description)
            tongue_findings.extend(matches)
        inquiry_info["tongue"] = tongue_findings if tongue_findings else None
        
        # 提取脉象
        pulse_patterns = [
            r"脉([浮沉迟数虚实滑涩])",
            r"([浮沉迟数虚实滑涩])脉"
        ]
        
        pulse_findings = []
        for pattern in pulse_patterns:
            matches = re.findall(pattern, description)
            pulse_findings.extend(matches)
        inquiry_info["pulse"] = pulse_findings if pulse_findings else None
        
        # 提取寒热信息
        if any(word in description for word in ["怕冷", "畏寒", "寒", "冷"]):
            inquiry_info["cold_heat"] = "寒"
        elif any(word in description for word in ["发热", "怕热", "热", "烧"]):
            inquiry_info["cold_heat"] = "热"
        else:
            inquiry_info["cold_heat"] = None
        
        # 提取汗出信息
        if any(word in description for word in ["出汗", "汗出", "盗汗", "自汗"]):
            inquiry_info["sweating"] = True
        else:
            inquiry_info["sweating"] = None
        
        return inquiry_info
    
    def _retrieve_knowledge(
        self,
        description: str,
        source_types: List[str]
    ) -> Dict:
        """
        检索相关知识
        
        Args:
            description: 患者描述
            source_types: 知识来源类型列表
        
        Returns:
            检索结果
        """
        all_results = []
        sources = []
        
        # 构建检索查询（提取关键症状）
        search_query = self._build_search_query(description)
        
        # 从各来源检索
        for source_type in source_types:
            results = self.vector_store.search_by_source_type(
                query=search_query,
                source_type=source_type,
                k=3
            )
            
            for result in results:
                all_results.append({
                    "content": result.content,
                    "source": result.source,
                    "source_type": source_type,
                    "score": result.score
                })
        
        # 按相似度排序
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "results": all_results[:10],  # 取前10条
            "sources": [
                {"type": r["source_type"], "source": r["source"]}
                for r in all_results[:5]
            ]
        }
    
    def _build_search_query(self, description: str) -> str:
        """构建检索查询"""
        # 提取症状关键词作为查询
        import re
        
        # 常见症状词
        symptom_pattern = r"(头痛|头晕|发热|恶寒|咳嗽|胸闷|心悸|乏力|恶心|呕吐|腹胀|腹痛|腹泻|便秘|失眠|口干|口苦|腰痛)"
        symptoms = re.findall(symptom_pattern, description)
        
        if symptoms:
            return " ".join(symptoms)
        
        # 如果没有匹配到症状，返回原文的前50字
        return description[:50]
    
    async def _analyze_condition(
        self,
        inquiry_info: Dict,
        retrieved_knowledge: Dict
    ) -> Dict:
        """
        分析病情
        
        Args:
            inquiry_info: 四诊信息
            retrieved_knowledge: 检索到的知识
        
        Returns:
            分析结果
        """
        # 如果有LLM，使用LLM分析
        if self.llm_client:
            return await self._analyze_with_llm(inquiry_info, retrieved_knowledge)
        
        # 否则使用规则分析
        return self._analyze_with_rules(inquiry_info, retrieved_knowledge)
    
    async def _analyze_with_llm(
        self,
        inquiry_info: Dict,
        retrieved_knowledge: Dict
    ) -> Dict:
        """使用LLM分析病情"""
        
        # 构建Prompt
        prompt = self._build_diagnosis_prompt(inquiry_info, retrieved_knowledge)
        
        # 调用LLM
        try:
            response = await self.llm_client.complete(prompt)
            # 解析LLM返回的JSON
            analysis = json.loads(response)
            return analysis
        except Exception as e:
            # 如果LLM调用失败，回退到规则分析
            return self._analyze_with_rules(inquiry_info, retrieved_knowledge)
    
    def _analyze_with_rules(
        self,
        inquiry_info: Dict,
        retrieved_knowledge: Dict
    ) -> Dict:
        """基于规则分析病情"""
        
        symptoms = inquiry_info.get("symptoms", [])
        tongue = inquiry_info.get("tongue", [])
        pulse = inquiry_info.get("pulse", [])
        cold_heat = inquiry_info.get("cold_heat")
        
        analysis = {
            "syndrome_type": "待进一步辨证",
            "pathogenesis": "",
            "treatment_principle": "",
            "detailed_analysis": "",
            "confidence": 0.5
        }
        
        # 简单的辨证规则示例
        if "头痛" in symptoms and "恶寒" in symptoms:
            analysis["syndrome_type"] = "外感风寒表证"
            analysis["pathogenesis"] = "风寒外束，卫阳被郁，腠理闭塞"
            analysis["treatment_principle"] = "辛温解表，宣肺散寒"
        
        elif "发热" in symptoms and "口渴" in symptoms:
            analysis["syndrome_type"] = "外感风热表证"
            analysis["pathogenesis"] = "风热犯表，热郁肌腠，卫表失和"
            analysis["treatment_principle"] = "辛凉解表，疏风清热"
        
        elif "胸闷" in symptoms and "心悸" in symptoms:
            analysis["syndrome_type"] = "胸痹"
            analysis["pathogenesis"] = "胸阳不振，痰浊内阻，心脉痹阻"
            analysis["treatment_principle"] = "通阳散结，祛痰宽胸"
        
        elif "失眠" in symptoms and "多梦" in symptoms:
            analysis["syndrome_type"] = "不寐"
            analysis["pathogenesis"] = "心脾两虚，血不养心，神不守舍"
            analysis["treatment_principle"] = "补益心脾，养血安神"
        
        # 构建详细分析
        analysis["detailed_analysis"] = f"""
根据您提供的症状信息：{', '.join(symptoms) if symptoms else '未明确描述'}

【四诊摘要】
- 症状：{', '.join(symptoms) if symptoms else '待补充'}
- 舌象：{', '.join(tongue) if tongue else '待补充'}
- 脉象：{', '.join(pulse) if pulse else '待补充'}
- 寒热：{cold_heat if cold_heat else '待补充'}

【辨证分析】
{analysis['pathogenesis']}

【治则治法】
{analysis['treatment_principle']}

注：以上分析仅供参考，建议咨询专业中医师进行面诊。
"""
        
        return analysis
    
    def _build_diagnosis_prompt(
        self,
        inquiry_info: Dict,
        retrieved_knowledge: Dict
    ) -> str:
        """构建诊断Prompt"""
        
        knowledge_text = "\n\n".join([
            f"【{i+1}】{k['content'][:200]}..."
            for i, k in enumerate(retrieved_knowledge.get("results", [])[:5])
        ])
        
        prompt = f"""你是一位经验丰富的中医专家。请根据以下患者信息和相关中医知识，进行辨证分析。

【患者四诊信息】
- 症状：{', '.join(inquiry_info.get('symptoms', []))}
- 舌象：{', '.join(inquiry_info.get('tongue', [])) if inquiry_info.get('tongue') else '未描述'}
- 脉象：{', '.join(inquiry_info.get('pulse', [])) if inquiry_info.get('pulse') else '未描述'}
- 寒热：{inquiry_info.get('cold_heat', '未描述')}
- 汗出：{inquiry_info.get('sweating', '未描述')}

【原始描述】
{inquiry_info['raw_description']}

【参考知识】
{knowledge_text}

请输出JSON格式的分析结果：
{{
    "syndrome_type": "证型名称",
    "pathogenesis": "病机分析",
    "treatment_principle": "治则治法",
    "detailed_analysis": "详细分析说明",
    "confidence": 0.8
}}
"""
        return prompt
    
    def _generate_recommendations(
        self,
        analysis: Dict,
        retrieved_knowledge: Dict
    ) -> List[Dict]:
        """生成推荐方案"""
        
        recommendations = []
        
        # 从检索结果中提取方剂推荐
        for result in retrieved_knowledge.get("results", []):
            source_type = result.get("source_type", "")
            
            if source_type in ["shanghan", "jinkui"]:
                recommendations.append({
                    "type": "formula",
                    "name": self._extract_formula_name(result["content"]),
                    "content": result["content"][:200] + "...",
                    "source": result["source"],
                    "rationale": f"根据{analysis.get('syndrome_type', '辨证')}推荐"
                })
            
            elif source_type == "acupuncture":
                recommendations.append({
                    "type": "acupuncture",
                    "name": "针灸穴位",
                    "content": result["content"][:200] + "...",
                    "source": result["source"],
                    "rationale": "根据症状推荐穴位"
                })
        
        # 去重
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            key = rec["name"]
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:5]
    
    def _extract_formula_name(self, content: str) -> str:
        """从内容中提取方剂名称"""
        import re
        # 尝试匹配常见的方剂名称格式
        patterns = [
            r"([\u4e00-\u9fa5]{2,6}汤)",
            r"([\u4e00-\u9fa5]{2,6}散)",
            r"([\u4e00-\u9fa5]{2,6}丸)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return "方剂"
    
    def _generate_warnings(self, analysis: Dict) -> List[str]:
        """生成警告提示"""
        warnings = []
        
        # 添加免责声明
        warnings.append("本诊断结果仅供参考，不能替代专业医生的诊断和治疗建议。")
        warnings.append("如有严重不适，请及时就医。")
        
        # 根据分析结果添加特定警告
        confidence = analysis.get("confidence", 0.5)
        if confidence < 0.6:
            warnings.append("由于提供的信息有限，诊断置信度较低，建议提供更多症状细节或咨询专业医师。")
        
        return warnings
    
    def format_diagnosis_result(self, result: DiagnosisResult) -> str:
        """格式化诊断结果为自然语言"""
        
        sections = []
        
        # 证型
        sections.append(f"## 🏥 辨证结果：{result.syndrome_type}")
        
        # 病机
        if result.pathogenesis:
            sections.append(f"\n### 📋 病机分析\n{result.pathogenesis}")
        
        # 治则
        if result.treatment_principle:
            sections.append(f"\n### 💊 治则治法\n{result.treatment_principle}")
        
        # 推荐方案
        if result.recommendations:
            sections.append("\n### 📖 参考方案")
            for i, rec in enumerate(result.recommendations[:3], 1):
                sections.append(f"\n**{i}. {rec['name']}** ({rec['type']})")
                sections.append(f"- 出处：{rec['source']}")
                sections.append(f"- 内容：{rec['content'][:150]}...")
        
        # 详细分析
        if result.analysis:
            sections.append(f"\n### 🔍 详细分析\n{result.analysis}")
        
        # 参考来源
        if result.sources:
            sections.append("\n### 📚 参考来源")
            for src in result.sources[:3]:
                sections.append(f"- {src['type']}: {src['source']}")
        
        # 警告
        if result.warnings:
            sections.append("\n---")
            sections.append("⚠️ **重要提示**：")
            for warning in result.warnings:
                sections.append(f"- {warning}")
        
        return "\n".join(sections)

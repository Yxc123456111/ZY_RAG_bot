#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中药 SQL 查询生成器
根据用户输入提取中药名称并生成 SQL 查询
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class HerbSQLQuery:
    """中药 SQL 查询对象"""
    sql: str
    params: Dict[str, Any]
    herb_names: List[str]
    explanation: str


class HerbKeywordExtractor:
    """中药关键词提取器"""
    
    # 从上经目录提取的中药名称（共142个）+ 其他常见中药
    COMMON_HERBS = [
    '.密陀僧',
    '.炙鳖甲',
    '丹参',
    '丹皮',
    '丹砂',
    '丹雄鸡',
    '乌头',
    '乌梅',
    '乌药',
    '乌韭',
    '云实',
    '云母',
    '五倍子',
    '五加皮',
    '五味子',
    '人参',
    '代赭石',
    '伏翼',
    '假苏',
    '充蔚子',
    '党参',
    '六畜毛蹄甲',
    '兰草',
    '冬灰',
    '冬瓜仁',
    '冬葵子',
    '决明子',
    '凝水石',
    '别羁',
    '刺猬',
    '北柴胡',
    '升麻',
    '半夏',
    '卫矛',
    '卷柏',
    '厚朴',
    '古南',
    '合欢',
    '吴茱萸',
    '商陆',
    '土茯苓',
    '地榆',
    '地肤子',
    '地胆',
    '地黄',
    '夏枯草',
    '夜交藤',
    '大便',
    '大戟',
    '大腹皮',
    '大黄',
    '天南星',
    '天名精',
    '天门冬',
    '天雄',
    '天鼠屎',
    '太一余粮',
    '太子参',
    '头发',
    '奄闾子',
    '女菀',
    '女萎',
    '女贞实',
    '女青',
    '姑活',
    '威灵仙',
    '孔公孽',
    '射干',
    '屈草',
    '山茱萸',
    '山药',
    '川芎',
    '巴戟天',
    '巴豆',
    '常山',
    '干姜',
    '干漆',
    '当归',
    '彼子',
    '徐长卿',
    '恒山',
    '慈石',
    '扁青',
    '文蛤',
    '斑蟊',
    '旋华',
    '旋覆花',
    '昌蒲',
    '景天',
    '曾青',
    '木兰',
    '木虻',
    '木通',
    '木香',
    '朴消',
    '杏仁',
    '杜仲',
    '杜若',
    '松脂',
    '松萝',
    '析蓂子',
    '枣',
    '枲耳实',
    '枳壳',
    '枳实',
    '枸杞',
    '柏实',
    '柳花',
    '柴胡',
    '栀子',
    '栾花',
    '桂枝',
    '桃仁',
    '桐叶',
    '桑上寄生',
    '桑根白皮',
    '桑蜱蛸',
    '桔梗',
    '梓白皮',
    '榆皮',
    '槀本',
    '槐实',
    '樗鸡',
    '款冬花',
    '殷孽',
    '水斳',
    '水苏',
    '水萍',
    '水蛭',
    '水银',
    '沙参',
    '河蟹',
    '泽兰',
    '泽泻',
    '泽漆',
    '海藻',
    '海蛤',
    '海螵蛸',
    '海金沙',
    '涅石',
    '消石',
    '淫羊藿',
    '淮木',
    '溲疏',
    '滑石',
    '漏芦',
    '灯芯草',
    '灵芝',
    '炙鳖甲',
    '熊脂',
    '燕屎',
    '爵床',
    '牛扁',
    '牛膝',
    '牛虻',
    '牛角鳃',
    '牛黄',
    '牡狗阴茎',
    '牡蛎',
    '犀角',
    '狗脊',
    '独活',
    '狼毒',
    '狼牙草',
    '猪苓',
    '玄参',
    '玉泉',
    '王不留行',
    '王孙',
    '王瓜',
    '理石',
    '瓜蒂',
    '瓜蒌根',
    '瓦楞子',
    '甘草',
    '甘遂',
    '甜杏仁',
    '白僵蚕',
    '白兔藿',
    '白垩',
    '白头翁',
    '白敛',
    '白术',
    '白棘',
    '白石英',
    '白胶',
    '白芍',
    '白芥子',
    '白芨',
    '白芷',
    '白英',
    '白茅根',
    '白蒿',
    '白薇',
    '白附子',
    '白青',
    '白马茎',
    '白鲜皮',
    '百合',
    '百草霜',
    '皂荚',
    '盖草',
    '瞿麦',
    '知母',
    '石决明',
    '石斛',
    '石灰',
    '石硫磺',
    '石膏',
    '石苇',
    '石蚕',
    '石蜜',
    '石钟乳',
    '石长生',
    '石龙刍',
    '石龙子',
    '石龙芮',
    '砂仁',
    '礜石',
    '禹余粮',
    '秦椒',
    '秦皮',
    '秦艽',
    '积雪草',
    '空青',
    '竹叶',
    '竹茹',
    '粉钖',
    '粟米',
    '紫参',
    '紫石英',
    '紫苑',
    '紫草',
    '紫菀',
    '紫葳',
    '细辛',
    '络石',
    '续断',
    '羊桃',
    '羊踯躅',
    '羊蹄',
    '羖羊角',
    '羚羊角',
    '翘根',
    '翳螉',
    '肉苁蓉',
    '肤青',
    '胆矾',
    '胡麻',
    '腐婢',
    '芜荑',
    '芡实',
    '芫花',
    '苇茎',
    '苋实',
    '苍术',
    '苦参',
    '苦瓠',
    '苦菜',
    '茜草',
    '茯苓',
    '茵芋',
    '茵陈',
    '草蒿',
    '荛花',
    '药实根',
    '莨菪子',
    '莱菔子',
    '莽草',
    '菊花',
    '菌桂',
    '菟丝子',
    '萆薢',
    '萤火',
    '营实',
    '萹蓄',
    '葛根',
    '葡萄',
    '葶苈',
    '蒲黄',
    '蒺藜子',
    '蓍实',
    '蓝实',
    '蓼实',
    '蔓椒',
    '蔓荆实',
    '蔺茹',
    '蕤核',
    '薄荷',
    '薇衔',
    '薏苡仁',
    '薤白',
    '藕实茎',
    '藜芦',
    '藿香',
    '蘼芜',
    '虾蟆',
    '蚤休',
    '蚯蚓',
    '蛇含',
    '蛇床子',
    '蛇蜕',
    '蛞蝓',
    '蛴螬',
    '蜀椒',
    '蜀羊泉',
    '蜂蜜',
    '蜈蚣',
    '蜚蠊',
    '蜜蜡',
    '蜣螂',
    '蝉蜕',
    '蝎子',
    '蝼蛄',
    '蟅虫',
    '蠡实',
    '衣鱼',
    '补骨脂',
    '覆盆子',
    '豆卷',
    '豚卵',
    '贝子',
    '贝母',
    '败酱草',
    '贯众',
    '赤石脂',
    '赤箭',
    '车前子',
    '辛夷花',
    '远志',
    '连翘',
    '郁李仁',
    '酸枣仁',
    '酸浆',
    '金铃子',
    '钩吻',
    '钩藤',
    '铁落',
    '铅丹',
    '银花',
    '长石',
    '防己',
    '防葵',
    '防风',
    '阳起石',
    '阿胶',
    '附子',
    '陆英',
    '陈皮',
    '雀瓮',
    '雁肪',
    '雄黄',
    '雌黄',
    '雚菌',
    '雷丸',
    '露蜂房',
    '青琅玕',
    '青盐',
    '青葙子',
    '青蘘',
    '飞廉',
    '香蒲',
    '马先蒿',
    '马刀',
    '马陆',
    '鬼臼',
    '鮀鱼甲',
    '鲤鱼',
    '鲤鱼胆',
    '鸢尾',
    '鹿茸',
    '鹿藿',
    '麋脂',
    '麝香',
    '麦门冬',
    '麻子仁',
    '麻黄',
    '黄明胶',
    '黄柏',
    '黄环',
    '黄精',
    '黄芩',
    '黄芪',
    '黄连',
    '黍米',
    '鼠妇',
    '鼠李',
    '龙眼',
    '龙胆',
    '龙骨',
    '龟甲',
    '（鼯）鼠',
]
    
    def __init__(self):
        # 创建正则表达式模式，按长度降序匹配，避免短词优先
        self.herb_pattern = self._create_herb_pattern()
    
    def _create_herb_pattern(self) -> re.Pattern:
        """创建中药名称匹配正则表达式"""
        # 按长度降序排序，优先匹配长词
        sorted_herbs = sorted(set(self.COMMON_HERBS), key=len, reverse=True)
        # 转义特殊字符
        escaped_herbs = [re.escape(herb) for herb in sorted_herbs]
        # 创建正则表达式
        pattern = '|'.join(escaped_herbs)
        return re.compile(pattern)
    
    def extract(self, query: str) -> List[str]:
        """
        从查询中提取中药名称
        
        Args:
            query: 用户查询文本
            
        Returns:
            提取到的中药名称列表
        """
        # 使用正则表达式匹配
        matches = self.herb_pattern.findall(query)
        
        # 去重并保持顺序
        seen = set()
        unique_matches = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                unique_matches.append(match)
        
        return unique_matches


class HerbSQLGenerator:
    """中药 SQL 查询生成器"""
    
    def __init__(self, table_name: str = "shennong_herbs"):
        self.table_name = table_name
        self.keyword_extractor = HerbKeywordExtractor()
    
    def generate(self, query: str) -> Optional[HerbSQLQuery]:
        """
        根据用户查询生成 SQL
        
        Args:
            query: 用户查询文本
            
        Returns:
            HerbSQLQuery 对象，如果没有提取到中药名称则返回 None
        """
        # 提取中药名称
        herb_names = self.keyword_extractor.extract(query)
        
        if not herb_names:
            return None
        
        # 构造 SQL
        if len(herb_names) == 1:
            # 单个药物查询
            sql = f"SELECT * FROM {self.table_name} WHERE drug_name = :herb_name"
            params = {"herb_name": herb_names[0]}
            explanation = f"查询表 {self.table_name} 中 drug_name 为 '{herb_names[0]}' 的记录"
        else:
            # 多个药物查询
            placeholders = ', '.join([f':herb_{i}' for i in range(len(herb_names))])
            sql = f"SELECT * FROM {self.table_name} WHERE drug_name IN ({placeholders})"
            params = {f"herb_{i}": name for i, name in enumerate(herb_names)}
            explanation = f"查询表 {self.table_name} 中 drug_name 在 {herb_names} 中的记录"
        
        return HerbSQLQuery(
            sql=sql,
            params=params,
            herb_names=herb_names,
            explanation=explanation
        )
    
    def generate_fuzzy_sql(self, query: str) -> Optional[HerbSQLQuery]:
        """
        生成模糊查询 SQL
        
        Args:
            query: 用户查询文本
            
        Returns:
            HerbSQLQuery 对象
        """
        # 提取中药名称
        herb_names = self.keyword_extractor.extract(query)
        
        if not herb_names:
            # 如果没有提取到，尝试使用整个查询作为关键词
            sql = f"SELECT * FROM {self.table_name} WHERE drug_name ILIKE :pattern"
            params = {"pattern": f"%{query}%"}
            explanation = f"模糊查询表 {self.table_name} 中 drug_name 包含 '{query}' 的记录"
            return HerbSQLQuery(
                sql=sql,
                params=params,
                herb_names=[query],
                explanation=explanation
            )
        
        # 使用第一个提取到的名称进行模糊查询
        sql = f"SELECT * FROM {self.table_name} WHERE drug_name ILIKE :pattern"
        params = {"pattern": f"%{herb_names[0]}%"}
        explanation = f"模糊查询表 {self.table_name} 中 drug_name 包含 '{herb_names[0]}' 的记录"
        
        return HerbSQLQuery(
            sql=sql,
            params=params,
            herb_names=herb_names,
            explanation=explanation
        )


# 便捷函数
def extract_herb_names(query: str) -> List[str]:
    """从查询中提取中药名称"""
    extractor = HerbKeywordExtractor()
    return extractor.extract(query)


def generate_herb_sql(query: str, table_name: str = "shennong_herbs") -> Optional[HerbSQLQuery]:
    """生成中药查询 SQL"""
    generator = HerbSQLGenerator(table_name)
    return generator.generate(query)


def generate_fuzzy_herb_sql(query: str, table_name: str = "shennong_herbs") -> Optional[HerbSQLQuery]:
    """生成中药模糊查询 SQL"""
    generator = HerbSQLGenerator(table_name)
    return generator.generate_fuzzy_sql(query)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单意图测试
"""

import sys
import os

# 清除缓存
for mod in list(sys.modules.keys()):
    if 'intent' in mod or 'core' in mod:
        del sys.modules[mod]

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 重新导入
from core.intent_classifier import IntentClassifier, IntentType

# 检查关键词
keywords = IntentClassifier.INTENT_KEYWORDS[IntentType.HERB_QUERY]

test_words = ['细辛', '苦菜', '酸枣', '白胶', '干漆', '酸枣仁']

print("检查关键词列表:")
for word in test_words:
    if word in keywords:
        print(f"  [OK] {word} 在关键词列表中")
    else:
        print(f"  [FAIL] {word} 不在关键词列表中")

# 测试分类器
print("\n测试意图分类:")
classifier = IntentClassifier()

for word in test_words:
    result = classifier.classify(word)
    is_herb = result.intent == IntentType.HERB_QUERY
    status = "OK" if is_herb else "FAIL"
    print(f"  [{status}] {word} -> {result.intent.value}")

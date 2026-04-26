#!/usr/bin/env python3
"""
测试情感分析增强效果
测试不同类型文本的情感分析结果，包括正面、负面、中性以及复杂情感表达
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.sentiment_service import SentimentService

def test_sentiment_analysis():
    """测试情感分析功能"""
    test_cases = [
        # 正面情感
        ("今天天气真好，心情非常愉快！", "positive"),
        ("收到了期待已久的礼物，开心极了！", "positive"),
        ("终于通过了考试，感觉所有努力都值得了", "positive"),
        
        # 负面情感
        ("今天遇到了很多麻烦，心情糟透了", "negative"),
        ("工作压力太大，简直要崩溃了", "negative"),
        ("被人误解的感觉真的很难受", "negative"),
        
        # 中性情感
        ("今天是周一，又要开始工作了", "neutral"),
        ("明天要下雨，记得带伞", "neutral"),
        ("这个问题需要仔细思考一下", "neutral"),
        
        # 复杂情感（讽刺、反语）
        ("呵呵，你可真是个好人", "negative"),  # 讽刺
        ("没关系，我一点都不生气", "negative"),  # 反语
        ("太棒了，又要加班到深夜", "negative"),  # 反语
        
        # 细粒度情感
        ("听到这个消息，我感到非常感动", "positive"),
        ("想到明天的面试，我就很焦虑", "negative"),
        ("对未来充满了期待", "positive"),
    ]
    
    print("=== 情感分析测试 ===")
    print(f"{'文本':<50} {'预期标签':<10} {'实际标签':<10} {'情感':<10} {'得分':<6}")
    print("-" * 90)
    
    for text, expected_label in test_cases:
        result = SentimentService.analyze(text, mode="smart")
        actual_label = result.get("label", "unknown")
        emotion = result.get("emotion", "unknown")
        score = result.get("score", 0.5)
        reasoning = result.get("reasoning", "")
        keywords = result.get("keywords", [])
        
        status = "✓" if actual_label == expected_label else "✗"
        print(f"{text:<50} {expected_label:<10} {actual_label:<10} {emotion:<10} {score:<6.2f} {status}")
        print(f"  理由: {reasoning}")
        print(f"  关键词: {', '.join(keywords)}")
        print()

def test_batch_analysis():
    """测试批量情感分析功能"""
    print("=== 批量情感分析测试 ===")
    texts = [
        "今天天气真好",
        "工作压力太大",
        "明天要下雨",
        "收到了礼物，很开心",
        "被人误解，很难受"
    ]
    
    results = SentimentService.analyze_batch(texts, mode="smart")
    for i, (text, result) in enumerate(zip(texts, results)):
        print(f"{i+1}. {text:<30} -> 标签: {result.get('label')}, 情感: {result.get('emotion')}, 得分: {result.get('score', 0.5):.2f}")
    print()

def test_distribution_analysis():
    """测试情感分布分析功能"""
    print("=== 情感分布分析测试 ===")
    texts = [
        "今天天气真好",
        "工作压力太大",
        "明天要下雨",
        "收到了礼物，很开心",
        "被人误解，很难受",
        "对未来充满期待",
        "今天遇到了很多麻烦",
        "终于通过了考试",
        "这个问题需要思考",
        "听到消息很感动"
    ]
    
    distribution = SentimentService.analyze_distribution(texts, mode="smart")
    print(f"情感分布: {distribution}")
    print()

if __name__ == "__main__":
    test_sentiment_analysis()
    test_batch_analysis()
    test_distribution_analysis()
    print("测试完成！")

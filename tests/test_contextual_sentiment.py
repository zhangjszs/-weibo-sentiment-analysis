#!/usr/bin/env python3
"""
上下文感知情感分析测试脚本
"""

import time
import json
from services.sentiment_service import SentimentService
from services.contextual_sentiment import contextual_analyzer


def test_basic_sentiment():
    """测试基础情感分析功能"""
    print("=== 测试基础情感分析 ===")
    
    test_texts = [
        "这部电影真的很棒，演员表演出色，剧情紧凑",
        "今天天气很差，心情也不好",
        "这个产品一般般，没有特别的亮点",
        "yyds！这个游戏太好玩了",
        "破防了，这个结局太让人难过了"
    ]
    
    for text in test_texts:
        result = SentimentService.analyze(text, mode="contextual")
        print(f"文本: {text}")
        print(f"得分: {result['score']:.4f}")
        print(f"标签: {result['label']}")
        print(f"情感: {result['emotion']}")
        print(f"关键词: {result['keywords']}")
        print(f"推理: {result['reasoning']}")
        print(f"来源: {result['source']}")
        print("---")


def test_contextual_analysis():
    """测试上下文关联分析"""
    print("\n=== 测试上下文关联分析 ===")
    
    context_id = "test_context_1"
    conversation = [
        "今天是个好日子",
        "天气晴朗，心情不错",
        "但是突然下起了雨",
        "心情瞬间变差了"
    ]
    
    for i, text in enumerate(conversation):
        print(f"对话 {i+1}: {text}")
        # 清除之前的上下文，重新开始测试
        if i == 0:
            contextual_analyzer.clear_context(context_id)
        
        # 使用上下文ID进行分析
        result = contextual_analyzer.analyze(text, context_id)
        print(f"得分: {result.score:.4f}")
        print(f"标签: {result.label}")
        print(f"情感: {result.emotion}")
        print(f"推理: {result.reasoning}")
        print(f"上下文大小: {contextual_analyzer.context_manager.get_context_size(context_id)}")
        print("---")


def test_internet_slang():
    """测试网络用语处理"""
    print("\n=== 测试网络用语处理 ===")
    
    slang_texts = [
        "这部电影yyds，强烈推荐",
        "今天的工作真是绝绝子",
        "666，这个操作太厉害了",
        "破防了，考试没通过",
        "无语了，又堵车了",
        "今天天气真好😄",
        "难过😢，宠物生病了"
    ]
    
    for text in slang_texts:
        result = SentimentService.analyze(text, mode="contextual")
        print(f"文本: {text}")
        print(f"得分: {result['score']:.4f}")
        print(f"标签: {result['label']}")
        print(f"情感: {result['emotion']}")
        print(f"关键词: {result['keywords']}")
        print(f"推理: {result['reasoning']}")
        print("---")


def test_performance():
    """测试性能"""
    print("\n=== 测试性能 ===")
    
    test_texts = [
        "这是一个测试文本" * 10,
        "yyds！这个产品太棒了",
        "今天天气不错，心情很好",
        "破防了，工作压力好大"
    ]
    
    start_time = time.time()
    results = SentimentService.analyze_batch(test_texts, mode="contextual")
    end_time = time.time()
    
    print(f"批量分析 {len(test_texts)} 条文本，耗时: {end_time - start_time:.4f} 秒")
    print(f"平均每条耗时: {(end_time - start_time) / len(test_texts):.4f} 秒")
    
    for i, result in enumerate(results):
        print(f"文本 {i+1} 得分: {result['score']:.4f}, 标签: {result['label']}")


def test_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    edge_cases = [
        "",  # 空文本
        "   ",  # 空白文本
        "测试" * 100,  # 长文本
        "😊😢👍👎",  # 只有emoji
        "yyds666nb",  # 只有网络用语
        "不不好好",  # 否定嵌套
        "呵呵，你真厉害",  # 讽刺
    ]
    
    for text in edge_cases:
        result = SentimentService.analyze(text, mode="contextual")
        print(f"文本: '{text}'")
        print(f"得分: {result['score']:.4f}")
        print(f"标签: {result['label']}")
        print(f"情感: {result['emotion']}")
        print("---")


if __name__ == "__main__":
    print("开始测试上下文感知情感分析...\n")
    
    test_basic_sentiment()
    test_contextual_analysis()
    test_internet_slang()
    test_performance()
    test_edge_cases()
    
    print("\n测试完成！")

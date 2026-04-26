#!/usr/bin/env python3
"""
测试优化后的情感分析系统
功能：测试情感分析的性能和准确性
"""

import time
import json
from services.sentiment_service import SentimentService
from services.sentiment_dictionaries import sentiment_dict


def test_basic_sentiment():
    """测试基本情感分析"""
    print("\n=== 测试基本情感分析 ===")
    test_cases = [
        ("这家餐厅的服务态度真是太好了！", "positive"),
        ("产品质量很差，客服也不回复。", "negative"),
        ("今天天气一般。", "neutral"),
    ]
    
    for text, expected_label in test_cases:
        start_time = time.time()
        result = SentimentService.analyze(text, mode="simple")
        end_time = time.time()
        
        print(f"文本: {text}")
        print(f"预测: {result['label']}, 得分: {result['score']:.2f}, 情感: {result['emotion']}")
        print(f"预期: {expected_label}")
        print(f"耗时: {end_time - start_time:.4f}s")
        print(f"推理: {result['reasoning']}")
        print()


def test_internet_slang():
    """测试网络用语处理"""
    print("\n=== 测试网络用语处理 ===")
    test_cases = [
        "yyds！这家店的东西太好吃了",
        "绝绝子！这个产品真的很棒",
        "666，主播太厉害了",
        "破防了，今天遇到了很多烦心事",
        "无语，这个服务态度太差了",
    ]
    
    for text in test_cases:
        start_time = time.time()
        result = SentimentService.analyze(text, mode="simple")
        end_time = time.time()
        
        print(f"文本: {text}")
        print(f"预测: {result['label']}, 得分: {result['score']:.2f}, 情感: {result['emotion']}")
        print(f"耗时: {end_time - start_time:.4f}s")
        print(f"关键词: {result['keywords']}")
        print()


def test_emoji():
    """测试emoji表情处理"""
    print("\n=== 测试emoji表情处理 ===")
    test_cases = [
        "今天天气真好！😄",
        "这个电影太感人了😭",
        "遇到了麻烦事😔",
        "收到了礼物🎁，好开心！",
        "工作压力好大😫",
    ]
    
    for text in test_cases:
        start_time = time.time()
        result = SentimentService.analyze(text, mode="simple")
        end_time = time.time()
        
        print(f"文本: {text}")
        print(f"预测: {result['label']}, 得分: {result['score']:.2f}, 情感: {result['emotion']}")
        print(f"耗时: {end_time - start_time:.4f}s")
        print()


def test_negation():
    """测试否定句式处理"""
    print("\n=== 测试否定句式处理 ===")
    test_cases = [
        "这个产品不是很好",
        "我不喜欢这个服务",
        "这不是一个好主意",
        "我没有失望",
        "他不是不开心",
    ]
    
    for text in test_cases:
        start_time = time.time()
        result = SentimentService.analyze(text, mode="simple")
        end_time = time.time()
        
        print(f"文本: {text}")
        print(f"预测: {result['label']}, 得分: {result['score']:.2f}, 情感: {result['emotion']}")
        print(f"耗时: {end_time - start_time:.4f}s")
        print(f"推理: {result['reasoning']}")
        print()


def test_sarcasm():
    """测试反语和讽刺处理"""
    print("\n=== 测试反语和讽刺处理 ===")
    test_cases = [
        "呵呵，你可真是太厉害了",
        "太棒了，又迟到了",
        "真的，我太开心了",
        "一点都不麻烦",
        "可真是个好主意",
    ]
    
    for text in test_cases:
        start_time = time.time()
        result = SentimentService.analyze(text, mode="simple")
        end_time = time.time()
        
        print(f"文本: {text}")
        print(f"预测: {result['label']}, 得分: {result['score']:.2f}, 情感: {result['emotion']}")
        print(f"耗时: {end_time - start_time:.4f}s")
        print(f"推理: {result['reasoning']}")
        print()


def test_sequence_analysis():
    """测试文本序列情感分析"""
    print("\n=== 测试文本序列情感分析 ===")
    test_sequence = [
        "今天早上天气很好，心情不错",
        "但是上班路上遇到了堵车，有点烦躁",
        "到了公司发现项目出了问题，很焦虑",
        "不过同事们都很帮忙，很感动",
        "最后问题解决了，很开心",
    ]
    
    start_time = time.time()
    result = SentimentService.analyze_sequence(test_sequence, mode="custom")
    end_time = time.time()
    
    print(f"序列分析耗时: {end_time - start_time:.4f}s")
    print(f"整体情感: {result['overall_sentiment']['label']}, 得分: {result['overall_sentiment']['score']:.2f}")
    print(f"情感突变次数: {len(result['sentiment_changes'])}")
    print(f"情感类型变化次数: {len(result['emotion_transitions'])}")
    
    print("\n序列分析结果:")
    for i, item in enumerate(result['sequence_analysis']):
        print(f"{i+1}. {item['text']}")
        print(f"   情感: {item['sentiment']['label']}, 得分: {item['sentiment']['score']:.2f}, 情绪: {item['sentiment']['emotion']}")
    
    if result['sentiment_changes']:
        print("\n情感突变:")
        for change in result['sentiment_changes']:
            print(f"从第{change['from_index']+1}句到第{change['to_index']+1}句，情感从{change['from_label']}变为{change['to_label']}，变化幅度: {change['change_score']:.2f}")


def test_dictionary_stats():
    """测试词典统计信息"""
    print("\n=== 测试词典统计信息 ===")
    stats = sentiment_dict.get_dictionary_stats()
    print(f"正向词数量: {stats['positive_words_count']}")
    print(f"负向词数量: {stats['negative_words_count']}")
    print(f"词典初始化状态: {stats['initialized']}")
    print(f"最后更新时间: {stats['last_updated']}")


def test_dictionary_update():
    """测试词典动态更新"""
    print("\n=== 测试词典动态更新 ===")
    # 测试更新前的状态
    stats_before = sentiment_dict.get_dictionary_stats()
    print(f"更新前 - 正向词: {stats_before['positive_words_count']}, 负向词: {stats_before['negative_words_count']}")
    
    # 添加新词汇
    new_positive = ["新词汇1", "新词汇2"]
    new_negative = ["新词汇3", "新词汇4"]
    sentiment_dict.update_from_external_source(new_positive, new_negative)
    
    # 测试更新后的状态
    stats_after = sentiment_dict.get_dictionary_stats()
    print(f"更新后 - 正向词: {stats_after['positive_words_count']}, 负向词: {stats_after['negative_words_count']}")
    print(f"更新是否成功: {stats_after['positive_words_count'] > stats_before['positive_words_count'] and stats_after['negative_words_count'] > stats_before['negative_words_count']}")


def test_performance():
    """测试性能"""
    print("\n=== 测试性能 ===")
    test_texts = [
        "这个产品很好",
        "服务态度很差",
        "yyds，太棒了",
        "今天心情不错",
        "遇到了麻烦事",
    ] * 20  # 100条测试文本
    
    start_time = time.time()
    results = SentimentService.analyze_batch(test_texts, mode="custom")
    end_time = time.time()
    
    total_time = end_time - start_time
    average_time = total_time / len(test_texts)
    
    print(f"批量分析 {len(test_texts)} 条文本")
    print(f"总耗时: {total_time:.4f}s")
    print(f"平均耗时: {average_time:.4f}s/条")
    print(f"分析成功率: {sum(1 for r in results if not r.get('error', False)) / len(results) * 100:.2f}%")


if __name__ == "__main__":
    print("开始测试优化后的情感分析系统...")
    
    test_basic_sentiment()
    test_internet_slang()
    test_emoji()
    test_negation()
    test_sarcasm()
    test_sequence_analysis()
    test_dictionary_stats()
    test_dictionary_update()
    test_performance()
    
    print("\n测试完成！")

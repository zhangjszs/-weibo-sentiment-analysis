#!/usr/bin/env python3
"""
测试智能策略选择系统
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.sentiment_strategy_selector import AdaptiveStrategyManager
from services.sentiment_service import SentimentService

def test_smart_strategy_selector():
    """测试智能策略选择器"""
    print("测试智能策略选择系统...")
    
    # 创建自适应策略管理器
    manager = AdaptiveStrategyManager()
    
    # 测试文本
    test_texts = [
        "这部电影真的太棒了，演员表演很出色！",  # 简单正面文本
        "这个产品质量很差，我非常失望。",    # 简单负面文本
        "今天天气一般，不过还可以接受。",    # 中性文本
        "呵呵，你可真是个天才！",            # 讽刺文本
        "这部电影的特效非常震撼，剧情也很紧凑，演员的表演更是精彩绝伦，强烈推荐给大家！",  # 长文本
        "yyds，永远的神！",                  # 网络用语
        "😀😀😀，今天真开心！",                # 包含emoji
        "不，我不喜欢这个东西。",              # 否定句式
    ]
    
    print("\n1. 测试智能策略选择:")
    print("-" * 60)
    for text in test_texts:
        result = manager.analyze(text)
        print(f"文本: {text}")
        print(f"情感: {result['label']} (得分: {result['score']:.4f})")
        print(f"情感类型: {result['emotion']}")
        print(f"使用策略: {result['source']}")
        print(f"关键词: {result['keywords']}")
        print("-" * 60)
    
    print("\n2. 测试批量分析:")
    print("-" * 60)
    batch_results = manager.analyze_batch(test_texts)
    for i, result in enumerate(batch_results):
        print(f"文本 {i+1}: {test_texts[i]}")
        print(f"情感: {result['label']} (得分: {result['score']:.4f})")
        print(f"使用策略: {result['source']}")
        print("-" * 60)
    
    print("\n3. 测试性能统计:")
    print("-" * 60)
    stats = manager.get_performance_stats()
    print("策略性能统计:")
    for strategy, data in stats['strategies'].items():
        print(f"{strategy}:")
        print(f"  总调用次数: {data['total_calls']}")
        print(f"  平均响应时间: {data['average_time']:.4f}s")
        print(f"  成功率: {data['success_rate']:.4f}")
        print(f"  准确率: {data['accuracy']:.4f}")
    
    print("\n4. 测试健康状态:")
    print("-" * 60)
    health = manager.get_health_status()
    print(f"系统状态: {health['status']}")
    if health['issues']:
        print("问题:")
        for issue in health['issues']:
            print(f"  - {issue}")
    else:
        print("系统健康，无问题")
    
    print("\n5. 测试SentimentService的auto模式:")
    print("-" * 60)
    for text in test_texts[:3]:
        result = SentimentService.analyze(text, mode="auto")
        print(f"文本: {text}")
        print(f"情感: {result['label']} (得分: {result['score']:.4f})")
        print(f"使用策略: {result['source']}")
        print("-" * 60)

def main():
    """主函数"""
    try:
        test_smart_strategy_selector()
        print("\n测试完成！智能策略选择系统工作正常。")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

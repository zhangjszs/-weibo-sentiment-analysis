#!/usr/bin/env python3
"""
测试模型改进效果
功能：验证模型的性能、批处理能力和社交媒体文本适应性
"""

import time
from pathlib import Path

import pandas as pd
from src.model.trainModel import train_best_model, load_data
from src.model.model_version_manager import ModelVersionManager
from src.model.model_monitor import ModelMonitor
from src.services.sentiment_service import SentimentService


def test_model_training():
    """测试模型训练"""
    print("\n=== 测试模型训练 ===")
    base_dir = Path(__file__).parent / "src" / "model"
    df = load_data(base_dir / "target.csv")
    print(f"加载数据: {len(df)} 条")
    
    # 训练模型
    start_time = time.time()
    model = train_best_model(df)
    training_time = time.time() - start_time
    print(f"训练时间: {training_time:.2f} 秒")
    
    return model


def test_model_versions():
    """测试模型版本管理"""
    print("\n=== 测试模型版本管理 ===")
    mvm = ModelVersionManager()
    versions = mvm.list_versions()
    print(f"模型版本数量: {len(versions)}")
    
    if versions:
        print("最新版本:")
        for key, value in versions[0].items():
            if key != "optimization_history":
                print(f"  {key}: {value}")
    
    # 测试获取最佳版本
    best_version = mvm.get_best_version()
    print(f"最佳版本: {best_version}")
    
    return mvm


def test_model_monitoring():
    """测试模型监控"""
    print("\n=== 测试模型监控 ===")
    monitor = ModelMonitor()
    
    # 检查模型健康状态
    health_status = monitor.check_model_health()
    print(f"模型健康状态: {health_status['status']}")
    if health_status['issues']:
        print("问题:")
        for issue in health_status['issues']:
            print(f"  - {issue}")
    
    # 获取请求统计
    request_stats = monitor.get_request_stats()
    print(f"总请求数: {request_stats.get('total_requests', 0)}")
    print(f"平均延迟: {request_stats.get('average_latency', 0):.4f} 秒")
    print(f"预测分布: {request_stats.get('predictions', {})}")
    
    return monitor


def test_sentiment_analysis():
    """测试情感分析服务"""
    print("\n=== 测试情感分析服务 ===")
    service = SentimentService()
    
    # 测试样例文本
    test_texts = [
        "这个产品真的很棒！👍",
        "服务态度很差，再也不会来了",
        "#新年快乐# 大家新年好！🎉",
        "@张三 你说得对",
        "今天天气不错，心情很好",
        "这部电影太无聊了，浪费时间",
        "http://example.com 这是一个链接",
        "哈哈哈，笑死我了😂",
        "工作压力好大，感觉好累",
        "期待明天的旅行✈️"
    ]
    
    # 测试单个分析
    print("\n测试单个分析:")
    for text in test_texts[:3]:
        start_time = time.time()
        result = service.analyze(text, mode="custom")
        latency = time.time() - start_time
        print(f"文本: {text}")
        print(f"结果: {result}")
        print(f"延迟: {latency:.4f} 秒")
        print("-" * 50)
    
    # 测试批量分析
    print("\n测试批量分析:")
    start_time = time.time()
    batch_results = service.analyze_batch(test_texts, mode="custom")
    batch_latency = time.time() - start_time
    print(f"批量分析时间: {batch_latency:.4f} 秒")
    print(f"平均每条延迟: {batch_latency / len(test_texts):.4f} 秒")
    
    # 打印部分结果
    print("\n批量分析结果:")
    for text, result in zip(test_texts[:5], batch_results[:5]):
        print(f"文本: {text}")
        print(f"结果: {result}")
        print("-" * 50)
    
    return service


def test_social_media_features():
    """测试社交媒体特征提取"""
    print("\n=== 测试社交媒体特征提取 ===")
    try:
        from src.model.social_media_preprocessor import SocialMediaPreprocessor
        preprocessor = SocialMediaPreprocessor()
        
        test_text = "#情感分析# 这个产品真的很棒！👍 @用户 推荐给大家"
        cleaned_text, features = preprocessor.transform([test_text])[0], preprocessor.get_social_features(test_text)
        
        print(f"原始文本: {test_text}")
        print(f"清理后文本: {cleaned_text}")
        print(f"社交媒体特征: {features}")
        
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


def test_data_augmentation():
    """测试数据增强"""
    print("\n=== 测试数据增强 ===")
    try:
        from src.model.social_media_augmenter import SocialMediaAugmenter
        augmenter = SocialMediaAugmenter()
        
        test_text = "这个产品真的很棒！"
        augmentations = augmenter.augment(test_text, num_augmentations=3)
        
        print(f"原始文本: {test_text}")
        print("增强结果:")
        for i, aug_text in enumerate(augmentations):
            print(f"  {i+1}. {aug_text}")
        
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试模型改进效果...")
    
    # 测试模型训练
    try:
        model = test_model_training()
        print("✅ 模型训练测试通过")
    except Exception as e:
        print(f"❌ 模型训练测试失败: {e}")
    
    # 测试模型版本管理
    try:
        mvm = test_model_versions()
        print("✅ 模型版本管理测试通过")
    except Exception as e:
        print(f"❌ 模型版本管理测试失败: {e}")
    
    # 测试模型监控
    try:
        monitor = test_model_monitoring()
        print("✅ 模型监控测试通过")
    except Exception as e:
        print(f"❌ 模型监控测试失败: {e}")
    
    # 测试情感分析服务
    try:
        service = test_sentiment_analysis()
        print("✅ 情感分析服务测试通过")
    except Exception as e:
        print(f"❌ 情感分析服务测试失败: {e}")
    
    # 测试社交媒体特征提取
    try:
        success = test_social_media_features()
        if success:
            print("✅ 社交媒体特征提取测试通过")
        else:
            print("❌ 社交媒体特征提取测试失败")
    except Exception as e:
        print(f"❌ 社交媒体特征提取测试失败: {e}")
    
    # 测试数据增强
    try:
        success = test_data_augmentation()
        if success:
            print("✅ 数据增强测试通过")
        else:
            print("❌ 数据增强测试失败")
    except Exception as e:
        print(f"❌ 数据增强测试失败: {e}")
    
    print("\n测试完成！")


if __name__ == "__main__":
    main()

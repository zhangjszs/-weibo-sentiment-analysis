#!/usr/bin/env python3
"""
修复后模型的使用示例
演示如何使用新的模型处理模块
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
model_dir = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "utils"))
sys.path.append(str(model_dir))


def example_data_processing():
    """示例：数据处理"""
    print("=" * 50)
    print("数据处理示例")
    print("=" * 50)

    from improved_index import ModelDataProcessor

    # 创建处理器
    processor = ModelDataProcessor(str(model_dir))

    # 模拟评论数据
    mock_comments = [
        [1, "user1", "2024-01-01", "comment", "这个产品真的很不错，推荐大家购买！"],
        [2, "user2", "2024-01-01", "comment", "质量一般，价格有点贵"],
        [3, "user3", "2024-01-01", "comment", "客服态度很好，物流也很快"],
        [4, "user4", "2024-01-01", "comment", "包装精美，产品符合预期"],
        [5, "user5", "2024-01-01", "comment", "性价比不错，值得购买"],
    ]

    # 处理文本
    segmented_text = processor.clean_and_segment_text(mock_comments)
    print(f"分词结果: {segmented_text[:100]}...")

    # 保存分词结果
    if segmented_text:
        success = processor.write_segmented_text(segmented_text)
        print(f"保存分词结果: {'成功' if success else '失败'}")

        # 计算词频
        freq_success = processor.calculate_word_frequency(max_words=50)
        print(f"词频计算: {'成功' if freq_success else '失败'}")


def example_sentiment_analysis():
    """示例：情感分析"""
    print("=" * 50)
    print("情感分析示例")
    print("=" * 50)

    from improved_yuqing import SentimentAnalyzer

    # 创建分析器
    analyzer = SentimentAnalyzer(str(model_dir))

    # 模拟文本数据
    test_texts = [
        "这个产品真的很棒，强烈推荐！",
        "质量一般，不太满意",
        "还可以吧，中规中矩",
        "非常失望，完全不值这个价格",
        "超出预期，物超所值",
    ]

    # 预处理文本
    processed_texts = analyzer.preprocess_comments(
        [[1, 2, 3, 4, text] for text in test_texts]
    )
    print(f"预处理完成，文本数量: {len(processed_texts)}")

    # 检查模型文件
    if analyzer.model_path.exists():
        print(f"模型文件存在: {analyzer.model_path}")
        # 加载模型
        if analyzer.load_model():
            print("模型加载成功")

            # 进行情感分析
            results = analyzer.analyze_sentiment(processed_texts)
            print(f"分析结果数量: {len(results)}")

            # 显示结果
            for result in results[:3]:  # 显示前3个结果
                print(f"文本: {result['text'][:20]}...")
                print(f"情感: {result['sentiment']}")
                print(f"置信度: {result['confidence']:.2f}")
                print("-" * 30)
        else:
            print("模型加载失败，请先训练模型")
    else:
        print(f"模型文件不存在: {analyzer.model_path}")
        print("请先运行 trainModel.py 训练模型")


def example_word_frequency():
    """示例：词频分析"""
    print("=" * 50)
    print("词频分析示例")
    print("=" * 50)

    from improved_ciPingTotal import WordFrequencyAnalyzer

    # 创建分析器
    analyzer = WordFrequencyAnalyzer(str(model_dir))

    # 检查输入文件
    if analyzer.input_file.exists():
        print(f"输入文件存在: {analyzer.input_file}")

        # 读取文本
        content = analyzer.read_segmented_text()
        if content:
            print(f"读取文本长度: {len(content)}")

            # 计算词频
            word_freq = analyzer.calculate_frequency(content, max_results=20)
            print(f"词频统计完成，词语数量: {len(word_freq)}")

            # 显示TOP 10
            print("\nTOP 10 高频词:")
            for i, (word, freq) in enumerate(word_freq[:10], 1):
                print(f"{i:2d}. {word} ({freq}次)")

            # 保存结果
            save_success = analyzer.save_frequency_results(word_freq)
            print(f"\n保存词频结果: {'成功' if save_success else '失败'}")
        else:
            print("读取文本失败")
    else:
        print(f"输入文件不存在: {analyzer.input_file}")
        print("请先运行数据处理步骤")


def example_pipeline():
    """示例：完整流水线"""
    print("=" * 50)
    print("完整流水线示例")
    print("=" * 50)

    from model_pipeline import ModelPipeline

    # 创建流水线
    pipeline = ModelPipeline(str(model_dir))

    print("流水线初始状态:")
    for key, value in pipeline.pipeline_status.items():
        print(f"  {key}: {value}")

    # 初始化模块
    init_success = pipeline._initialize_modules()
    print(f"\n模块初始化: {'成功' if init_success else '失败'}")

    if init_success:
        print("\n可用的执行模式:")
        print("1. pipeline.run_complete_pipeline() - 完整流水线")
        print("2. pipeline.run_step_by_step() - 逐步执行")
        print("3. pipeline.run_data_processing() - 仅数据处理")
        print("4. pipeline.run_sentiment_analysis() - 仅情感分析")
        print("5. pipeline.run_frequency_analysis() - 仅词频分析")

        # 生成示例报告
        report = pipeline.generate_pipeline_report()
        print(f"\n流水线报告生成: {'成功' if report else '失败'}")


def main():
    """主函数"""
    print("修复后的模型使用示例")
    print("=" * 60)

    try:
        # 示例1: 数据处理
        example_data_processing()

        print("\n")

        # 示例2: 情感分析
        example_sentiment_analysis()

        print("\n")

        # 示例3: 词频分析
        example_word_frequency()

        print("\n")

        # 示例4: 完整流水线
        example_pipeline()

        print("\n" + "=" * 60)
        print("所有示例执行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"示例执行出错: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

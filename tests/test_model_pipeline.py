#!/usr/bin/env python3
"""
模型流水线单元测试
测试范围：数据处理、情感分析、词频统计流水线
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestModelDataProcessor:
    """数据处理模块测试"""

    @pytest.fixture
    def temp_model_dir(self):
        """创建临时模型目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_comments(self):
        """创建示例评论数据"""
        return [
            [1, "2024-01-01", "100", "user1", "这个产品真的很不错，推荐大家购买！"],
            [2, "2024-01-01", "50", "user2", "质量一般，价格有点贵"],
            [3, "2024-01-01", "200", "user3", "客服态度很好，物流也很快"],
            [4, "2024-01-01", "30", "user4", "包装精美，产品符合预期"],
            [5, "2024-01-01", "80", "user5", "性价比不错，值得购买"],
        ]

    @pytest.fixture
    def stop_words_file(self, temp_model_dir):
        """创建停用词文件"""
        stop_words_path = temp_model_dir / "stopWords.txt"
        with open(stop_words_path, "w", encoding="utf-8") as f:
            f.write("的\n了\n在\n是\n我\n有\n和\n就\n不\n人\n")
        return stop_words_path

    def test_load_stop_words(self, temp_model_dir, stop_words_file):
        """测试停用词加载"""
        from model.index import ModelDataProcessor

        processor = ModelDataProcessor(str(temp_model_dir))

        assert len(processor.stop_words) > 0
        assert "的" in processor.stop_words
        assert "了" in processor.stop_words

    def test_clean_and_segment_text(self, temp_model_dir, sample_comments):
        """测试文本清洗和分词"""
        from model.index import ModelDataProcessor

        processor = ModelDataProcessor(str(temp_model_dir))
        result = processor.clean_and_segment_text(sample_comments)

        assert result is not None
        assert len(result) > 0
        assert " " in result

    def test_clean_and_segment_empty_input(self, temp_model_dir):
        """测试空输入处理"""
        from model.index import ModelDataProcessor

        processor = ModelDataProcessor(str(temp_model_dir))
        result = processor.clean_and_segment_text([])

        assert result == ""

    def test_write_segmented_text(self, temp_model_dir):
        """测试分词结果写入"""
        from model.index import ModelDataProcessor

        processor = ModelDataProcessor(str(temp_model_dir))
        test_text = "测试 分词 结果"

        success = processor.write_segmented_text(test_text)

        assert success is True
        assert processor.target_txt.exists()

        with open(processor.target_txt, encoding="utf-8") as f:
            content = f.read()
        assert content == test_text

    def test_calculate_word_frequency(self, temp_model_dir):
        """测试词频计算"""
        from model.index import ModelDataProcessor

        processor = ModelDataProcessor(str(temp_model_dir))

        with open(processor.target_txt, "w", encoding="utf-8") as f:
            f.write("测试 测试 分词 分词 结果")

        success = processor.calculate_word_frequency(max_words=10)

        assert success is True
        assert processor.freq_csv.exists()

    def test_process_data_pipeline(self, temp_model_dir, sample_comments):
        """测试完整数据处理流水线"""
        from model.index import ModelDataProcessor

        with patch.object(
            ModelDataProcessor, "get_comment_list", return_value=sample_comments
        ):
            processor = ModelDataProcessor(str(temp_model_dir))
            success = processor.process_data_pipeline()

            assert success is True

    def test_get_comment_list_prefers_query_dataframe(self, temp_model_dir, monkeypatch):
        """测试评论读取优先走查询层，而不是旧的全量读取函数"""
        import types

        fake_public_data = types.SimpleNamespace(
            getAllCommentsData=lambda: (_ for _ in ()).throw(
                AssertionError("should not load all comments")
            )
        )
        monkeypatch.setitem(sys.modules, "getPublicData", fake_public_data)

        from model.index import ModelDataProcessor
        import model.index as model_index

        monkeypatch.setattr(
            model_index,
            "query_dataframe",
            lambda sql, params=None: __import__("pandas").DataFrame(
                [{"articleId": 1, "created_at": "2026-03-20", "content": "测试评论"}]
            ),
            raising=False,
        )

        processor = ModelDataProcessor(str(temp_model_dir))
        comments = processor.get_comment_list()

        assert len(comments) == 1
        assert comments[0][2] == "测试评论"


class TestSentimentAnalyzer:
    """情感分析器测试"""

    @pytest.fixture
    def temp_model_dir(self):
        """创建临时模型目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_model(self):
        """创建模拟模型"""
        mock = MagicMock()
        mock.predict.return_value = [2]
        mock.predict_proba.return_value = [[0.1, 0.2, 0.7]]
        return mock

    def test_preprocess_comments(self, temp_model_dir):
        """测试评论预处理"""
        from model.yuqing import SentimentAnalyzer

        analyzer = SentimentAnalyzer(str(temp_model_dir))
        comments = [
            [1, "2024-01-01", "100", "user1", "这个产品真的很不错"],
            [2, "2024-01-01", "50", "user2", "质量一般"],
        ]

        result = analyzer.preprocess_comments(comments)

        assert len(result) == 2
        assert all(isinstance(text, str) for text in result)

    def test_preprocess_comments_filters_short(self, temp_model_dir):
        """测试过滤短文本"""
        from model.yuqing import SentimentAnalyzer

        analyzer = SentimentAnalyzer(str(temp_model_dir))
        comments = [
            [1, "2024-01-01", "100", "user1", "好"],
            [2, "2024-01-01", "50", "user2", "这个产品真的很不错"],
        ]

        result = analyzer.preprocess_comments(comments)

        assert len(result) == 1

    def test_analyze_sentiment(self, temp_model_dir, mock_model):
        """测试情感分析"""
        from model.yuqing import SentimentAnalyzer

        analyzer = SentimentAnalyzer(str(temp_model_dir))
        analyzer.model = mock_model

        texts = ["这个很好", "那个很差"]
        results = analyzer.analyze_sentiment(texts)

        assert len(results) == 2
        assert "sentiment" in results[0]
        assert "confidence" in results[0]

    def test_generate_summary_statistics(self, temp_model_dir):
        """测试统计汇总生成"""
        from model.yuqing import SentimentAnalyzer

        analyzer = SentimentAnalyzer(str(temp_model_dir))
        results = [
            {"sentiment": "正面", "confidence": 0.8},
            {"sentiment": "中性", "confidence": 0.5},
            {"sentiment": "负面", "confidence": 0.3},
            {"sentiment": "正面", "confidence": 0.9},
        ]

        summary = analyzer.generate_summary_statistics(results)

        assert summary["total_comments"] == 4
        assert summary["sentiment_counts"]["正面"] == 2
        assert "average_confidence" in summary

    def test_get_comment_data_prefers_query_dataframe(self, temp_model_dir, monkeypatch):
        """测试情感分析器读取评论优先走查询层"""
        import types

        fake_public_data = types.SimpleNamespace(
            getAllCommentsData=lambda: (_ for _ in ()).throw(
                AssertionError("should not load all comments")
            )
        )
        monkeypatch.setitem(sys.modules, "getPublicData", fake_public_data)

        from model.yuqing import SentimentAnalyzer
        import model.yuqing as yuqing_model

        monkeypatch.setattr(
            yuqing_model,
            "query_dataframe",
            lambda sql, params=None: __import__("pandas").DataFrame(
                [{"articleId": 1, "created_at": "2026-03-20", "content": "测试评论"}]
            ),
            raising=False,
        )

        analyzer = SentimentAnalyzer(str(temp_model_dir))
        comments = analyzer.get_comment_data()

        assert len(comments) == 1
        assert comments[0][2] == "测试评论"


class TestWordFrequencyAnalyzer:
    """词频分析器测试"""

    @pytest.fixture
    def temp_model_dir(self):
        """创建临时模型目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def segmented_text_file(self, temp_model_dir):
        """创建分词文本文件"""
        file_path = temp_model_dir / "comment_1_fenci.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("测试 测试 分词 分词 分析 分析 分析 结果")
        return file_path

    def test_read_segmented_text(self, temp_model_dir, segmented_text_file):
        """测试读取分词文本"""
        from model.ciPingTotal import WordFrequencyAnalyzer

        analyzer = WordFrequencyAnalyzer(str(temp_model_dir))
        content = analyzer.read_segmented_text()

        assert content is not None
        assert "测试" in content

    def test_filter_words(self, temp_model_dir):
        """测试词语过滤"""
        from model.ciPingTotal import WordFrequencyAnalyzer

        analyzer = WordFrequencyAnalyzer(str(temp_model_dir))
        words = ["测试", "的", "123", "!!", "分析", "结果"]

        filtered = analyzer.filter_words(words)

        assert "测试" in filtered
        assert "的" not in filtered
        assert "123" not in filtered
        assert "!!" not in filtered

    def test_calculate_frequency(self, temp_model_dir, segmented_text_file):
        """测试词频计算"""
        from model.ciPingTotal import WordFrequencyAnalyzer

        analyzer = WordFrequencyAnalyzer(str(temp_model_dir))
        content = analyzer.read_segmented_text()
        word_freq = analyzer.calculate_frequency(content, max_results=10)

        assert len(word_freq) > 0
        assert all(isinstance(item, tuple) for item in word_freq)
        assert all(len(item) == 2 for item in word_freq)

    def test_save_frequency_results(self, temp_model_dir, segmented_text_file):
        """测试保存词频结果"""
        from model.ciPingTotal import WordFrequencyAnalyzer

        analyzer = WordFrequencyAnalyzer(str(temp_model_dir))
        word_freq = [("测试", 10), ("分词", 8), ("分析", 6)]

        success = analyzer.save_frequency_results(word_freq)

        assert success is True
        assert analyzer.output_file.exists()

    def test_generate_frequency_report(self, temp_model_dir):
        """测试生成词频报告"""
        from model.ciPingTotal import WordFrequencyAnalyzer

        analyzer = WordFrequencyAnalyzer(str(temp_model_dir))
        word_freq = [("测试", 10), ("分词", 8), ("分析", 6), ("结果", 2)]

        report = analyzer.generate_frequency_report(word_freq)

        assert report["total_word_count"] == 26
        assert report["unique_word_count"] == 4
        assert "max_frequency" in report
        assert "min_frequency" in report


class TestModelPipeline:
    """模型流水线测试"""

    @pytest.fixture
    def temp_model_dir(self):
        """创建临时模型目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_pipeline_initialization(self, temp_model_dir):
        """测试流水线初始化"""
        from model.model_pipeline import ModelPipeline

        pipeline = ModelPipeline(str(temp_model_dir))

        assert pipeline.model_dir == temp_model_dir
        assert pipeline.pipeline_status["data_processing"] is False
        assert pipeline.pipeline_status["sentiment_analysis"] is False

    def test_generate_pipeline_report(self, temp_model_dir):
        """测试生成流水线报告"""
        from datetime import datetime

        from model.model_pipeline import ModelPipeline

        pipeline = ModelPipeline(str(temp_model_dir))
        pipeline.pipeline_status["start_time"] = datetime.now()
        pipeline.pipeline_status["end_time"] = datetime.now()
        pipeline.pipeline_status["data_processing"] = True

        report = pipeline.generate_pipeline_report()

        assert "pipeline_status" in report
        assert "execution_time_seconds" in report
        assert "success_rate" in report

    def test_save_pipeline_report(self, temp_model_dir):
        """测试保存流水线报告"""
        from model.model_pipeline import ModelPipeline

        pipeline = ModelPipeline(str(temp_model_dir))
        report = {
            "pipeline_status": {"data_processing": True},
            "execution_time_seconds": 1.5,
        }

        success = pipeline.save_pipeline_report(report)

        assert success is True


class TestHyperparameterOptimizer:
    """超参数优化器测试"""

    @pytest.fixture
    def temp_model_dir(self):
        """创建临时模型目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_csv(self, temp_model_dir):
        """创建示例CSV文件"""
        csv_path = temp_model_dir / "target.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("很好,2\n")
            f.write("不错,2\n")
            f.write("一般,1\n")
            f.write("差,0\n")
            f.write("很差,0\n")
            f.write("非常好,2\n")
            f.write("还可以,1\n")
            f.write("糟糕,0\n")
            f.write("太棒了,2\n")
            f.write("失望,0\n")
        return csv_path

    def test_build_pipeline(self, temp_model_dir):
        """测试构建流水线"""
        from model.hyperparameter_optimizer import HyperparameterOptimizer

        optimizer = HyperparameterOptimizer(str(temp_model_dir))

        for model_name in ["NaiveBayes", "LogReg", "LinearSVM"]:
            pipeline = optimizer.build_pipeline(model_name)
            assert pipeline is not None
            assert hasattr(pipeline, "steps")

    def test_load_data(self, sample_csv):
        """测试数据加载"""
        from model.hyperparameter_optimizer import load_data

        df = load_data(sample_csv)

        assert len(df) == 10
        assert "text" in df.columns
        assert "label" in df.columns

    def test_param_grids_defined(self, temp_model_dir):
        """测试参数网格定义"""
        from model.hyperparameter_optimizer import HyperparameterOptimizer

        optimizer = HyperparameterOptimizer(str(temp_model_dir))

        assert "NaiveBayes" in optimizer.param_grids
        assert "LogReg" in optimizer.param_grids
        assert "LinearSVM" in optimizer.param_grids
        assert "RandomForest" in optimizer.param_grids


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

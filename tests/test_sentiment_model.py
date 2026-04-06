#!/usr/bin/env python3
"""
情感分析模型单元测试
测试范围：模型训练、预测、评估、持久化
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestSentimentModel:
    """情感分析模型测试类"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        return [
            ("这个产品真的很棒，强烈推荐！", 2),
            ("质量一般，不太满意", 1),
            ("还可以吧，中规中矩", 1),
            ("非常失望，完全不值这个价格", 0),
            ("超出预期，物超所值", 2),
            ("糟糕透了，再也不买了", 0),
            ("客服态度很好，物流也很快", 2),
            ("包装精美，产品符合预期", 2),
            ("性价比不错，值得购买", 2),
            ("质量太差了，退货了", 0),
        ]

    @pytest.fixture
    def temp_model_dir(self):
        """创建临时模型目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_csv(self, temp_model_dir, sample_data):
        """创建示例CSV文件"""
        csv_path = temp_model_dir / "target.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            for text, label in sample_data:
                f.write(f"{text},{label}\n")
        return csv_path

    def test_load_data(self, sample_csv):
        """测试数据加载"""
        from model.trainModel import load_data

        df = load_data(sample_csv)

        assert len(df) == 10
        assert "text" in df.columns
        assert "label" in df.columns
        assert df["text"].isna().sum() == 0
        assert df["label"].isna().sum() == 0

    def test_build_pipeline(self):
        """测试流水线构建"""
        from model.trainModel import MODELS, build_pipeline

        for name, estimator in MODELS.items():
            pipeline = build_pipeline(estimator)
            assert pipeline is not None
            assert hasattr(pipeline, "steps")
            assert len(pipeline.steps) == 2

    def test_model_training(self, sample_csv):
        """测试模型训练"""
        from model.trainModel import MODELS, build_pipeline, load_data

        df = load_data(sample_csv)
        X, y = df["text"], df["label"]

        pipeline = build_pipeline(MODELS["NaiveBayes"])
        pipeline.fit(X, y)

        assert pipeline is not None
        assert hasattr(pipeline, "predict")

    def test_model_prediction(self, sample_csv):
        """测试模型预测"""
        from model.trainModel import MODELS, build_pipeline, load_data

        df = load_data(sample_csv)
        X, y = df["text"], df["label"]

        pipeline = build_pipeline(MODELS["NaiveBayes"])
        pipeline.fit(X, y)

        predictions = pipeline.predict(["这个很好"])

        assert len(predictions) == 1
        assert predictions[0] in [0, 1, 2]

    def test_model_predict_proba(self, sample_csv):
        """测试概率预测"""
        from model.trainModel import MODELS, build_pipeline, load_data

        df = load_data(sample_csv)
        X, y = df["text"], df["label"]

        pipeline = build_pipeline(MODELS["NaiveBayes"])
        pipeline.fit(X, y)

        proba = pipeline.predict_proba(["这个很好"])

        assert proba.shape[0] == 1
        assert proba.shape[1] == 3
        assert abs(proba.sum() - 1.0) < 0.001

    def test_model_save_load(self, sample_csv, temp_model_dir):
        """测试模型保存和加载"""
        import joblib

        from model.trainModel import MODELS, build_pipeline, load_data

        df = load_data(sample_csv)
        X, y = df["text"], df["label"]

        pipeline = build_pipeline(MODELS["NaiveBayes"])
        pipeline.fit(X, y)

        model_path = temp_model_dir / "test_model.pkl"
        joblib.dump(pipeline, model_path)

        assert model_path.exists()

        loaded_pipeline = joblib.load(model_path)
        predictions = loaded_pipeline.predict(["测试文本"])

        assert len(predictions) == 1


class TestWeightedMultinomialNB:
    """加权朴素贝叶斯测试"""

    def test_weighted_nb_fit(self):
        """测试加权朴素贝叶斯训练"""
        import numpy as np

        from model.model_utils import WeightedMultinomialNB

        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 0, 1, 2])

        model = WeightedMultinomialNB()
        model.fit(X, y)

        assert model is not None
        assert hasattr(model, "predict")

    def test_weighted_nb_predict(self):
        """测试加权朴素贝叶斯预测"""
        import numpy as np

        from model.model_utils import WeightedMultinomialNB

        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
        y = np.array([0, 0, 1, 1, 2])

        model = WeightedMultinomialNB()
        model.fit(X, y)

        predictions = model.predict([[2, 3]])

        assert len(predictions) == 1


class TestSentimentService:
    """情感分析服务测试"""

    @pytest.fixture
    def mock_snownlp(self):
        """Mock SnowNLP"""
        with patch("services.sentiment_service.SnowNLP") as mock:
            mock_instance = MagicMock()
            mock_instance.sentiments = 0.7
            mock_instance.keywords.return_value = ["关键词1", "关键词2"]
            mock.return_value = mock_instance
            yield mock

    def test_snownlp_strategy(self, mock_snownlp):
        """测试SnowNLP策略"""
        from services.sentiment_service import SnowNLPStrategy

        strategy = SnowNLPStrategy()
        result = strategy.analyze("这是一条测试文本")

        assert result is not None
        assert hasattr(result, "score")
        assert hasattr(result, "label")
        assert result.source == "snownlp"

    def test_sentiment_result_to_dict(self):
        """测试结果转换"""
        from services.sentiment_service import SentimentResult

        result = SentimentResult(
            score=0.8,
            label="positive",
            reasoning="测试理由",
            emotion="喜悦",
            keywords=["关键词"],
            source="test",
        )

        result_dict = result.to_dict()

        assert result_dict["score"] == 0.8
        assert result_dict["label"] == "positive"
        assert result_dict["reasoning"] == "测试理由"

    def test_sentiment_schema_validation(self):
        """测试Schema校验"""
        from services.sentiment_service import SentimentSchema

        valid_data = {
            "score": 0.5,
            "label": "neutral",
            "emotion": "无感",
            "reasoning": "测试",
            "keywords": [],
        }

        schema = SentimentSchema(**valid_data)

        assert schema.score == 0.5
        assert schema.label == "neutral"

    def test_sentiment_schema_invalid_label(self):
        """测试无效标签自动转换"""
        from services.sentiment_service import SentimentSchema

        data = {
            "score": 0.5,
            "label": "invalid_label",
        }

        schema = SentimentSchema(**data)

        assert schema.label == "neutral"

    def test_sentiment_schema_score_range(self):
        """测试分数范围校验"""
        from pydantic import ValidationError

        from services.sentiment_service import SentimentSchema

        with pytest.raises(ValidationError):
            SentimentSchema(score=1.5)

        with pytest.raises(ValidationError):
            SentimentSchema(score=-0.1)


class TestSentimentPredictor:
    """预测器测试"""

    def test_predictor_singleton(self):
        """测试单例模式"""
        from model.trainModel import SentimentPredictor

        assert SentimentPredictor._model is None

    @patch("model.trainModel.joblib.load")
    def test_predictor_load(self, mock_load):
        """测试模型加载"""
        from model.trainModel import SentimentPredictor

        mock_model = MagicMock()
        mock_model.predict.return_value = [1]
        mock_load.return_value = mock_model

        SentimentPredictor._model = None
        model = SentimentPredictor.load("dummy_path.pkl")

        assert model is not None

    @patch("model.trainModel.joblib.load")
    def test_predictor_predict(self, mock_load):
        """测试预测"""
        from model.trainModel import SentimentPredictor

        mock_model = MagicMock()
        mock_model.predict.return_value = [2]
        mock_load.return_value = mock_model

        SentimentPredictor._model = None

        with patch.object(SentimentPredictor, "load", return_value=mock_model):
            result = SentimentPredictor.predict("好的产品")

            assert result in [0, 1, 2]


class TestModelEvaluation:
    """模型评估测试"""

    @pytest.fixture
    def sample_dataframe(self):
        """创建示例DataFrame"""
        import pandas as pd

        data = {
            "text": [
                "很好",
                "不错",
                "一般",
                "差",
                "很差",
                "非常好",
                "还可以",
                "糟糕",
                "太棒了",
                "失望",
            ],
            "label": [2, 2, 1, 0, 0, 2, 1, 0, 2, 0],
        }
        return pd.DataFrame(data)

    def test_evaluate_models(self, sample_dataframe):
        """测试模型评估"""
        from model.trainModel import evaluate_models

        results = evaluate_models(sample_dataframe, k_folds=2, scoring="macro_f1")

        assert results is not None
        assert isinstance(results, dict)

    def test_cross_validation_splits(self, sample_dataframe):
        """测试交叉验证折数"""
        from model.trainModel import evaluate_models

        min_class = sample_dataframe["label"].value_counts().min()

        if min_class < 5:
            results = evaluate_models(sample_dataframe, scoring="macro_f1")
            assert results is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""``src/services/sentiment_backend.py`` 单元测试。

覆盖：
- ``SklearnBackend`` / ``BertBackend`` / ``SnowNLPBackend`` 的 ``predict`` 行为
  （通过 mock，避免依赖真实模型文件）
- ``AutoBackendSelector`` 的优先级选择与降级链
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.sentiment_backend import (  # noqa: E402
    AutoBackendSelector,
    BACKEND_REGISTRY,
    BertBackend,
    LABEL_NEGATIVE,
    LABEL_NEUTRAL,
    LABEL_POSITIVE,
    ModelBackend,
    SklearnBackend,
    SnowNLPBackend,
)


# ---------------------------------------------------------------------------
# SklearnBackend
# ---------------------------------------------------------------------------


class _FakeSklearnModel:
    """模拟 sklearn 模型：predict 返回整数 label，predict_proba 返回概率。"""

    def __init__(self, predictions, probs):
        self._preds = list(predictions)
        self._probs = list(probs)

    def predict(self, texts):
        return self._preds[: len(texts)]

    def predict_proba(self, texts):
        return self._probs[: len(texts)]


class TestSklearnBackend:
    def test_is_loaded_false_when_file_missing(self, tmp_path):
        backend = SklearnBackend(model_path=str(tmp_path / "no_such.pkl"))
        assert backend.is_loaded is False

    def test_predict_maps_int_labels_and_proba(self):
        model = _FakeSklearnModel(
            predictions=[2, 0, 1],
            probs=[[0.1, 0.1, 0.8], [0.7, 0.2, 0.1], [0.2, 0.6, 0.2]],
        )
        backend = SklearnBackend(model_path="/dev/null")
        # 直接注入模型跳过 _load
        backend._model = model
        results = backend.predict(["好", "差", "一般"])
        assert results == [
            (LABEL_POSITIVE, 0.8),
            (LABEL_NEGATIVE, 0.7),
            (LABEL_NEUTRAL, 0.6),
        ]

    def test_predict_without_predict_proba_defaults_to_half(self):
        class _NoProbaModel:
            def predict(self, texts):
                return [2, 0]

        backend = SklearnBackend(model_path="/dev/null")
        backend._model = _NoProbaModel()
        results = backend.predict(["好", "差"])
        assert results == [(LABEL_POSITIVE, 0.5), (LABEL_NEGATIVE, 0.5)]

    def test_predict_empty_input(self):
        backend = SklearnBackend(model_path="/dev/null")
        backend._model = _FakeSklearnModel([], [])
        assert backend.predict([]) == []

    def test_predict_raises_when_model_not_loaded(self, tmp_path):
        backend = SklearnBackend(model_path=str(tmp_path / "no_such.pkl"))
        with pytest.raises(RuntimeError):
            backend.predict(["x"])


# ---------------------------------------------------------------------------
# BertBackend（真实实现，无模型文件时 is_loaded=False）
# ---------------------------------------------------------------------------


class TestBertBackend:
    def test_is_loaded_false_when_model_missing(self, tmp_path):
        backend = BertBackend(model_path=str(tmp_path / "no_such_dir"))
        assert backend.is_loaded is False

    def test_predict_raises_runtime_error_when_not_loaded(self, tmp_path):
        backend = BertBackend(model_path=str(tmp_path / "no_such_dir"))
        with pytest.raises(RuntimeError):
            backend.predict(["x"])

    def test_predict_empty_input_skips_load(self, tmp_path):
        backend = BertBackend(model_path=str(tmp_path / "no_such_dir"))
        assert backend.predict([]) == []

    def test_map_three_class_binary_positive(self):
        backend = BertBackend.__new__(BertBackend)
        backend._id2label = {0: "Negative", 1: "Positive"}
        backend.POSITIVE_THRESHOLD = 0.7
        backend.NEGATIVE_THRESHOLD = 0.3
        # probs=[neg=0.05, pos=0.95] → positive
        label, score = backend._map_three_class([0.05, 0.95])
        assert label == LABEL_POSITIVE
        assert score == pytest.approx(0.95, abs=1e-6)

    def test_map_three_class_binary_negative(self):
        backend = BertBackend.__new__(BertBackend)
        backend._id2label = {0: "Negative", 1: "Positive"}
        backend.POSITIVE_THRESHOLD = 0.7
        backend.NEGATIVE_THRESHOLD = 0.3
        # probs=[neg=0.92, pos=0.08] → negative
        label, score = backend._map_three_class([0.92, 0.08])
        assert label == LABEL_NEGATIVE
        assert score == pytest.approx(0.92, abs=1e-6)

    def test_map_three_class_binary_neutral(self):
        backend = BertBackend.__new__(BertBackend)
        backend._id2label = {0: "Negative", 1: "Positive"}
        backend.POSITIVE_THRESHOLD = 0.7
        backend.NEGATIVE_THRESHOLD = 0.3
        # probs=[neg=0.45, pos=0.55] → neutral
        label, score = backend._map_three_class([0.45, 0.55])
        assert label == LABEL_NEUTRAL
        # score = 1 - |0.55 - 0.5| * 2 = 1 - 0.1 = 0.9
        assert score == pytest.approx(0.9, abs=1e-6)

    def test_map_three_class_already_three_class(self):
        backend = BertBackend.__new__(BertBackend)
        backend._id2label = {0: "negative", 1: "neutral", 2: "positive"}
        backend.POSITIVE_THRESHOLD = 0.7
        backend.NEGATIVE_THRESHOLD = 0.3
        label, score = backend._map_three_class([0.1, 0.2, 0.7])
        assert label == LABEL_POSITIVE
        assert score == pytest.approx(0.7, abs=1e-6)

    def test_softmax_normalizes(self):
        backend = BertBackend.__new__(BertBackend)
        probs = backend._softmax([1.0, 2.0, 3.0])
        assert sum(probs) == pytest.approx(1.0, abs=1e-6)
        assert probs[2] > probs[1] > probs[0]

    def test_run_inference_with_mock_model(self):
        """注入 mock model+tokenizer 验证 _run_inference 流程。"""
        backend = BertBackend.__new__(BertBackend)
        backend.model_path = "/dev/null"
        backend.max_length = 64
        backend.batch_size = 4
        backend._id2label = {0: "Negative", 1: "Positive"}
        backend.POSITIVE_THRESHOLD = 0.7
        backend.NEGATIVE_THRESHOLD = 0.3

        # mock tokenizer: 返回 dummy inputs
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": [[1]]}
        backend._tokenizer = mock_tokenizer

        # mock model: 返回 logits [[-3, 3]] (softmax → ~[0.018, 0.982] → positive)
        mock_model = MagicMock()
        mock_output = MagicMock()
        mock_output.logits = [[-3.0, 3.0]]
        mock_model.return_value = mock_output
        backend._model = mock_model

        results = backend.predict(["好棒"])
        assert len(results) == 1
        label, score = results[0]
        assert label == LABEL_POSITIVE
        assert score > 0.7


# ---------------------------------------------------------------------------
# SnowNLPBackend
# ---------------------------------------------------------------------------


class TestSnowNLPBackend:
    def test_is_loaded_always_true(self):
        assert SnowNLPBackend().is_loaded is True

    def test_predict_returns_positive_for_good_text(self):
        """通过 mock SnowNLPStrategy 验证包装逻辑。"""
        backend = SnowNLPBackend()
        mock_strategy = MagicMock()
        mock_strategy.analyze.return_value = MagicMock(
            label=LABEL_POSITIVE, score=0.85
        )
        backend._strategy = mock_strategy
        results = backend.predict(["好棒"])
        assert results == [(LABEL_POSITIVE, 0.85)]

    def test_predict_falls_back_to_neutral_on_exception(self):
        backend = SnowNLPBackend()
        mock_strategy = MagicMock()
        mock_strategy.analyze.side_effect = ValueError("boom")
        backend._strategy = mock_strategy
        results = backend.predict(["x", "y"])
        assert results == [(LABEL_NEUTRAL, 0.5), (LABEL_NEUTRAL, 0.5)]

    def test_predict_empty_input(self):
        backend = SnowNLPBackend()
        assert backend.predict([]) == []


# ---------------------------------------------------------------------------
# AutoBackendSelector
# ---------------------------------------------------------------------------


class _StubBackend(ModelBackend):
    """可编程的 backend 桩，便于控制 is_loaded / predict 行为。"""

    name = "stub"

    def __init__(self, loaded=True, predict_result=None, raise_on_predict=None):
        self._loaded = loaded
        self._predict_result = predict_result or [(LABEL_POSITIVE, 0.9)]
        self._raise = raise_on_predict
        self.predict_call_count = 0

    @property
    def is_loaded(self):
        return self._loaded

    def predict(self, texts):
        self.predict_call_count += 1
        if self._raise:
            raise self._raise
        return list(self._predict_result)


class TestAutoBackendSelector:
    def test_preferred_bert_unloaded_falls_back_to_sklearn(self):
        selector = AutoBackendSelector(preferred="bert")
        bert = _StubBackend(loaded=False)
        sklearn = _StubBackend(
            loaded=True, predict_result=[(LABEL_POSITIVE, 0.7)]
        )
        selector._backends = {"bert": bert, "sklearn": sklearn, "snownlp": _StubBackend()}
        results = selector.predict(["x"])
        assert results == [(LABEL_POSITIVE, 0.7)]
        assert bert.predict_call_count == 0
        assert sklearn.predict_call_count == 1

    def test_preferred_sklearn_loaded_uses_sklearn(self):
        selector = AutoBackendSelector(preferred="sklearn")
        sklearn = _StubBackend(
            loaded=True, predict_result=[(LABEL_NEUTRAL, 0.5)]
        )
        selector._backends = {
            "bert": _StubBackend(loaded=False),
            "sklearn": sklearn,
            "snownlp": _StubBackend(),
        }
        results = selector.predict(["x"])
        assert results == [(LABEL_NEUTRAL, 0.5)]
        assert sklearn.predict_call_count == 1

    def test_sklearn_predict_failure_degrades_to_snownlp(self):
        selector = AutoBackendSelector(preferred="sklearn")
        sklearn = _StubBackend(
            loaded=True, raise_on_predict=RuntimeError("model broken")
        )
        snownlp = _StubBackend(
            loaded=True, predict_result=[(LABEL_NEGATIVE, 0.4)]
        )
        selector._backends = {
            "bert": _StubBackend(loaded=False),
            "sklearn": sklearn,
            "snownlp": snownlp,
        }
        results = selector.predict(["x"])
        assert results == [(LABEL_NEGATIVE, 0.4)]
        assert sklearn.predict_call_count == 1
        assert snownlp.predict_call_count == 1

    def test_all_backends_fail_returns_neutral(self):
        selector = AutoBackendSelector(preferred="bert")
        selector._backends = {
            "bert": _StubBackend(loaded=True, raise_on_predict=ValueError("x")),
            "sklearn": _StubBackend(
                loaded=True, raise_on_predict=RuntimeError("x")
            ),
            # snownlp 也抛错
            "snownlp": _StubBackend(loaded=True, raise_on_predict=ValueError("x")),
        }
        results = selector.predict(["a", "b"])
        assert results == [(LABEL_NEUTRAL, 0.5), (LABEL_NEUTRAL, 0.5)]

    def test_auto_mode_uses_degradation_chain_order(self):
        # auto 模式：bert 未加载 → sklearn 未加载 → snownlp 加载
        selector = AutoBackendSelector(preferred="auto")
        bert = _StubBackend(loaded=False)
        sklearn = _StubBackend(loaded=False)
        snownlp = _StubBackend(
            loaded=True, predict_result=[(LABEL_POSITIVE, 0.99)]
        )
        selector._backends = {
            "bert": bert,
            "sklearn": sklearn,
            "snownlp": snownlp,
        }
        results = selector.predict(["x"])
        assert results == [(LABEL_POSITIVE, 0.99)]
        assert snownlp.predict_call_count == 1

    def test_select_returns_first_loaded_backend(self):
        selector = AutoBackendSelector(preferred="auto")
        bert = _StubBackend(loaded=False)
        sklearn = _StubBackend(loaded=True)
        snownlp = _StubBackend(loaded=True)
        selector._backends = {"bert": bert, "sklearn": sklearn, "snownlp": snownlp}
        assert selector.select() is sklearn

    def test_select_falls_back_to_snownlp_when_all_unavailable(self):
        selector = AutoBackendSelector(preferred="auto")
        # 用真实 SnowNLPBackend 而非 _StubBackend，确保 .name == 'snownlp'
        selector._backends = {
            "bert": _StubBackend(loaded=False),
            "sklearn": _StubBackend(loaded=False),
            "snownlp": SnowNLPBackend(),
        }
        backend = selector.select()
        assert backend.name == "snownlp"

    def test_empty_input_returns_empty(self):
        selector = AutoBackendSelector(preferred="auto")
        assert selector.predict([]) == []

    def test_registry_contains_three_backends(self):
        assert set(BACKEND_REGISTRY.keys()) == {"bert", "sklearn", "snownlp"}
        assert BACKEND_REGISTRY["bert"] is BertBackend
        assert BACKEND_REGISTRY["sklearn"] is SklearnBackend
        assert BACKEND_REGISTRY["snownlp"] is SnowNLPBackend

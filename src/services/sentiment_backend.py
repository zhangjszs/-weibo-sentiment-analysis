"""情感分析后端抽象层（Phase 3）。

提供统一的 ``ModelBackend`` ABC，封装 sklearn / BERT / SnowNLP 三种后端，
并通过 :class:`AutoBackendSelector` 实现按配置选择 + 自动降级。

设计目标
--------
- 上层策略（``CustomModelStrategy``）只面向 ``ModelBackend`` 接口，不再关心底层
  是 sklearn 还是 BERT，便于后续替换与回滚。
- BERT 后端可独立训练 / 加载 / 升级，与 sklearn 解耦。
- 失败时按 ``bert → sklearn → snownlp`` 链路自动降级，保证可用性。

统一标签 schema
---------------
所有后端 ``predict`` 返回的 label 必须是英文 ``positive`` / ``negative`` /
``neutral``（详见 Phase 3.7 标签 schema 统一）。中文展示由
:func:`src.utils.sentiment.label_to_chinese` 完成。
"""
from __future__ import annotations

import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from config.settings import Config

logger = logging.getLogger(__name__)

# 统一英文标签常量（Phase 3.7 后全仓统一使用英文 label）
LABEL_POSITIVE = "positive"
LABEL_NEUTRAL = "neutral"
LABEL_NEGATIVE = "negative"

# 类型别名：标签字符串与单条预测结果 (label, confidence_score 0..1)
Label = str
PredictResult = Tuple[Label, float]


class ModelBackend(ABC):
    """所有情感分析后端的抽象基类。"""

    #: 后端名称，用于缓存 key、日志、版本管理
    name: str = "abstract"

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """后端是否就绪（模型/词典加载完成）。"""

    @abstractmethod
    def predict(self, texts: List[str]) -> List[PredictResult]:
        """对一批文本做预测，返回 ``[(label, score), ...]``。

        实现需保证：
        - 输出长度与输入长度一致
        - score 取值范围 ``[0, 1]``
        - label 必须为英文 ``positive`` / ``negative`` / ``neutral``
        """

    def predict_batch(self, texts: List[str]) -> List[PredictResult]:
        """批量预测，默认等同 :meth:`predict`。

        BERT / sklearn 可重写为一次性推理以获得更好的吞吐。
        """
        return self.predict(texts)

    def close(self) -> None:
        """释放底层资源（如 ONNX session），默认无操作。"""


class SklearnBackend(ModelBackend):
    """sklearn 传统模型后端，加载 ``best_sentiment_model.pkl``。"""

    name = "sklearn"

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path or os.path.join(
            Config.BASE_DIR, "model", "best_sentiment_model.pkl"
        )
        self._model: Any = None
        self._metadata: Dict[str, Any] = {}

    @property
    def is_loaded(self) -> bool:
        if self._model is None:
            self._load()
        return self._model is not None

    def _load(self) -> None:
        if self._model is not None:
            return
        if not os.path.exists(self.model_path):
            logger.warning("SklearnBackend: 模型文件不存在: %s", self.model_path)
            return
        try:
            import joblib  # noqa: WPS433 - 延迟导入避免无模型环境 ImportError

            # pickle 反序列化需要 model_utils 在 sys.path 上
            model_dir = os.path.join(Config.BASE_DIR, "model")
            if model_dir not in sys.path:
                sys.path.append(model_dir)

            try:
                from model.model_version_manager import load_model_with_versioning

                self._model, self._metadata = load_model_with_versioning(model_dir)
            except (ImportError, OSError) as e:
                logger.warning(
                    "SklearnBackend: 版本管理加载失败，回退普通加载: %s", e
                )
                self._model = joblib.load(self.model_path)
                self._metadata = {"loaded": True, "model_path": self.model_path}
        except Exception as e:  # pragma: no cover - 加载失败由 is_loaded 反映
            logger.error("SklearnBackend: 加载失败: %s", e)
            self._model = None

    @staticmethod
    def _map_label(prediction: Any) -> Label:
        """将 sklearn 预测值统一为英文 label。"""
        if isinstance(prediction, str):
            return {
                "positive": LABEL_POSITIVE,
                "pos": LABEL_POSITIVE,
                "negative": LABEL_NEGATIVE,
                "neg": LABEL_NEGATIVE,
            }.get(prediction, LABEL_NEUTRAL)
        return {0: LABEL_NEGATIVE, 1: LABEL_NEUTRAL, 2: LABEL_POSITIVE}.get(
            prediction, LABEL_NEUTRAL
        )

    def predict(self, texts: List[str]) -> List[PredictResult]:
        if not texts:
            return []
        self._load()
        if self._model is None:
            raise RuntimeError("SklearnBackend: 模型未加载")
        processed = [t[:512] for t in texts]
        predictions = self._model.predict(processed)
        results: List[PredictResult] = []
        if hasattr(self._model, "predict_proba"):
            probs = self._model.predict_proba(processed)
            for pred, prob in zip(predictions, probs):
                results.append((self._map_label(pred), float(max(prob))))
        else:
            for pred in predictions:
                results.append((self._map_label(pred), 0.5))
        return results


class BertBackend(ModelBackend):
    """BERT 预训练模型后端（基于 ONNX Runtime）。

    - 模型：``IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment``（二分类）
    - 推理：``optimum.onnxruntime.ORTModelForSequenceClassification``
    - 三分类扩展：原始模型只有 Negative/Positive 两类，按设计 B3 用阈值
      ``>0.7 → positive``、``<0.3 → negative``、其余 ``neutral`` 拓展为三分类

    模型文件缺失或依赖未安装时 ``is_loaded`` 返回 ``False``，
    :class:`AutoBackendSelector` 会自动降级到 sklearn / snownlp。
    """

    name = "bert"

    # 三分类阈值（基于 softmax 后的 positive 概率）
    POSITIVE_THRESHOLD = 0.7
    NEGATIVE_THRESHOLD = 0.3

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path or Config.BERT_MODEL_PATH
        self.max_length = Config.BERT_MAX_LENGTH
        self.batch_size = Config.BERT_BATCH_SIZE
        self._model: Any = None
        self._tokenizer: Any = None
        self._id2label: Dict[int, str] = {}

    @property
    def is_loaded(self) -> bool:
        if self._model is None:
            self._load()
        return self._model is not None

    def _load(self) -> None:
        if self._model is not None:
            return
        onnx_file = os.path.join(self.model_path, "model.onnx")
        if not os.path.exists(onnx_file):
            logger.info(
                "BertBackend: ONNX 模型不存在: %s（运行 scripts/download_bert_model.py 下载）",
                onnx_file,
            )
            return
        try:
            from transformers import AutoTokenizer
            from optimum.onnxruntime import ORTModelForSequenceClassification
        except ImportError as e:
            logger.warning(
                "BertBackend: 缺少依赖 %s（pip install optimum[onnxruntime] transformers）", e
            )
            return
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self._model = ORTModelForSequenceClassification.from_pretrained(
                self.model_path
            )
            self._id2label = getattr(self._model.config, "id2label", {0: "Negative", 1: "Positive"})
            logger.info(
                "BertBackend: 模型加载完成，id2label=%s", self._id2label
            )
        except Exception as e:  # pragma: no cover - 加载失败由 is_loaded 反映
            logger.error("BertBackend: 加载失败: %s", e)
            self._model = None
            self._tokenizer = None

    def _softmax(self, logits: List[float]) -> List[float]:
        import math

        if not logits:
            return []
        m = max(logits)
        exps = [math.exp(x - m) for x in logits]
        s = sum(exps)
        return [e / s for e in exps]

    def _map_three_class(self, probs: List[float]) -> PredictResult:
        """将二分类概率映射为三分类 (label, score)。

        Erlangshen-Roberta-110M-Sentiment 的 id2label 通常是
        ``{0: 'Negative', 1: 'Positive'}``。取 positive 概率：
        - ``> 0.7`` → positive
        - ``< 0.3`` → negative
        - 中间 → neutral
        score 取该 label 对应的最大概率（neutral 时取 1 - max_prob）。
        """
        if len(probs) == 2:
            # 假设 id2label={0:'Negative',1:'Positive'}（不区分大小写）
            neg_label = str(self._id2label.get(0, "Negative")).lower()
            pos_label = str(self._id2label.get(1, "Positive")).lower()
            if "pos" in pos_label and "neg" in neg_label:
                pos_prob = probs[1]
            elif "pos" in neg_label and "neg" in pos_label:
                pos_prob = probs[0]
            else:
                # 无法识别顺序，按 argmax 给极性
                idx = int(probs.index(max(probs)))
                lbl = self._id2label.get(idx, "").lower()
                if "pos" in lbl:
                    return (LABEL_POSITIVE, max(probs))
                if "neg" in lbl:
                    return (LABEL_NEGATIVE, max(probs))
                return (LABEL_NEUTRAL, max(probs))
        elif len(probs) == 3:
            # 已是三分类，按 argmax 直接返回
            idx = int(probs.index(max(probs)))
            lbl = str(self._id2label.get(idx, "")).lower()
            mapping = {
                "positive": LABEL_POSITIVE,
                "pos": LABEL_POSITIVE,
                "neutral": LABEL_NEUTRAL,
                "neu": LABEL_NEUTRAL,
                "negative": LABEL_NEGATIVE,
                "neg": LABEL_NEGATIVE,
            }
            for key, val in mapping.items():
                if key in lbl:
                    return (val, max(probs))
            return (LABEL_NEUTRAL, max(probs))
        else:
            pos_prob = 0.5

        if pos_prob > self.POSITIVE_THRESHOLD:
            return (LABEL_POSITIVE, pos_prob)
        if pos_prob < self.NEGATIVE_THRESHOLD:
            return (LABEL_NEGATIVE, 1.0 - pos_prob)
        return (LABEL_NEUTRAL, 1.0 - abs(pos_prob - 0.5) * 2)

    def _run_inference(self, texts: List[str]) -> List[PredictResult]:
        if not texts:
            return []
        if self._model is None or self._tokenizer is None:
            raise RuntimeError("BertBackend: 模型未加载")

        results: List[PredictResult] = []
        # 分批避免显存/内存峰值
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            inputs = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            outputs = self._model(**inputs)
            raw = outputs.logits if hasattr(outputs, "logits") else outputs[0]
            # 兼容 torch.Tensor（有 .tolist()）与 list/numpy 等序列
            logits = raw.tolist() if hasattr(raw, "tolist") else list(raw)
            for row in logits:
                probs = self._softmax(row)
                results.append(self._map_three_class(probs))
        return results

    def predict(self, texts: List[str]) -> List[PredictResult]:
        return self._run_inference(texts)

    def predict_batch(self, texts: List[str]) -> List[PredictResult]:
        # _run_inference 已分批，predict_batch 等同 predict
        return self._run_inference(texts)

    def close(self) -> None:
        self._model = None
        self._tokenizer = None


class SnowNLPBackend(ModelBackend):
    """SnowNLP 后端，包装 :class:`SnowNLPStrategy` 的核心打分逻辑。

    作为兜底降级路径，不依赖任何模型文件，永远 ``is_loaded=True``。
    """

    name = "snownlp"

    def __init__(self) -> None:
        self._strategy: Any = None

    @property
    def is_loaded(self) -> bool:
        return True

    def _get_strategy(self):
        if self._strategy is None:
            # 延迟导入打破与 sentiment_service 的循环依赖
            from .sentiment_service import SnowNLPStrategy

            self._strategy = SnowNLPStrategy()
        return self._strategy

    def predict(self, texts: List[str]) -> List[PredictResult]:
        if not texts:
            return []
        strategy = self._get_strategy()
        results: List[PredictResult] = []
        for text in texts:
            try:
                r = strategy.analyze(text)
                results.append((r.label, float(r.score)))
            except Exception as e:
                logger.warning(
                    "SnowNLPBackend: 单条分析失败，返回 neutral: %s", e
                )
                results.append((LABEL_NEUTRAL, 0.5))
        return results


# 后端注册表（按优先级排序，AutoBackendSelector 降级链也基于此）
BACKEND_REGISTRY: Dict[str, type] = {
    "bert": BertBackend,
    "sklearn": SklearnBackend,
    "snownlp": SnowNLPBackend,
}


class AutoBackendSelector:
    """按配置选择主后端，并在加载/推理失败时按降级链切换。

    降级链：``bert → sklearn → snownlp``。当 ``preferred='auto'`` 时按此链
    逐个尝试；指定具体后端时优先使用指定项，失败再走降级链。
    """

    DEGRADATION_CHAIN: List[str] = ["bert", "sklearn", "snownlp"]

    def __init__(self, preferred: Optional[str] = None) -> None:
        self.preferred = (preferred or self._read_config()).lower()
        self._backends: Dict[str, ModelBackend] = {}

    @staticmethod
    def _read_config() -> str:
        return getattr(Config, "SENTIMENT_BACKEND", "auto")

    def _get_backend(self, name: str) -> Optional[ModelBackend]:
        if name not in self._backends:
            cls = BACKEND_REGISTRY.get(name)
            if cls is None:
                return None
            try:
                self._backends[name] = cls()
            except Exception as e:
                logger.error(
                    "AutoBackendSelector: 后端 %s 实例化失败: %s", name, e
                )
                return None
        return self._backends[name]

    def _ordered_candidates(self) -> List[str]:
        """返回尝试顺序：preferred 优先，其余按降级链补齐。"""
        if self.preferred in ("auto", "", None):
            return list(self.DEGRADATION_CHAIN)
        return [self.preferred] + [
            n for n in self.DEGRADATION_CHAIN if n != self.preferred
        ]

    def select(self) -> ModelBackend:
        """返回首个 ``is_loaded=True`` 的后端；全部失败时返回 SnowNLPBackend。"""
        for name in self._ordered_candidates():
            backend = self._get_backend(name)
            if backend is None:
                continue
            try:
                if backend.is_loaded:
                    logger.info("AutoBackendSelector: 选中后端 %s", name)
                    return backend
            except Exception as e:
                logger.warning(
                    "AutoBackendSelector: 后端 %s is_loaded 检查失败: %s",
                    name,
                    e,
                )
        logger.warning("AutoBackendSelector: 所有后端不可用，回退 SnowNLPBackend")
        return self._get_backend("snownlp") or SnowNLPBackend()

    def predict(self, texts: List[str]) -> List[PredictResult]:
        """选择后端并执行预测；首选失败时按链降级。"""
        if not texts:
            return []
        last_error: Optional[Exception] = None
        for name in self._ordered_candidates():
            backend = self._get_backend(name)
            if backend is None:
                continue
            try:
                if not backend.is_loaded:
                    continue
                return backend.predict_batch(texts)
            except Exception as e:
                logger.warning(
                    "AutoBackendSelector: 后端 %s 预测失败，尝试下一个: %s",
                    name,
                    e,
                )
                last_error = e
        # 最终兜底：SnowNLP（永远可用）
        try:
            snow = self._get_backend("snownlp") or SnowNLPBackend()
            return snow.predict(texts)
        except Exception as e:  # pragma: no cover - 极端情况
            logger.error("AutoBackendSelector: SnowNLP 兜底也失败: %s", e)
            return [(LABEL_NEUTRAL, 0.5) for _ in texts]

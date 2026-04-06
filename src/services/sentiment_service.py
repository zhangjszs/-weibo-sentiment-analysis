#!/usr/bin/env python3
"""
情感分析服务模块
功能：提供多种情感分析策略（SnowNLP/LLM/自定义模型）
特性：熔断器保护、Redis缓存、JSON Schema校验、自动降级
"""

import hashlib
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional

import requests
from circuitbreaker import circuit
from pydantic import BaseModel, Field, field_validator
from snownlp import SnowNLP

from config.settings import Config

logger = logging.getLogger(__name__)

# 尝试导入Redis（可选依赖）
try:
    import redis

    redis_params = Config.get_redis_connection_params()
    redis_params.update(
        {
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "health_check_interval": 30,
        }
    )
    redis_client = redis.Redis(**redis_params)
    # 测试连接
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis缓存已启用")
except Exception as e:
    logger.warning(f"Redis连接失败，将使用内存缓存: {e}")
    redis_client = None
    REDIS_AVAILABLE = False


class SentimentResult:
    """统一的情感分析结果对象"""

    def __init__(
        self,
        score,
        label,
        reasoning=None,
        emotion=None,
        keywords=None,
        cached=False,
        source="unknown",
    ):
        self.score = score  # 0-1 float
        self.label = label  # positive/negative/neutral
        self.reasoning = reasoning  # 分析理由 (LLM特有)
        self.emotion = emotion  # 细粒度情感 (喜怒哀乐等)
        self.keywords = keywords or []  # 关键词列表
        self.cached = cached  # 是否来自缓存
        self.source = source  # 来源：cache/llm/snownlp/fallback

    def to_dict(self):
        return {
            "score": self.score,
            "label": self.label,
            "reasoning": self.reasoning,
            "emotion": self.emotion,
            "keywords": self.keywords,
            "cached": self.cached,
            "source": self.source,
        }


class SentimentSchema(BaseModel):
    """LLM输出Schema校验"""

    score: float = Field(ge=0.0, le=1.0, default=0.5, description="情感得分，0-1之间")
    label: str = Field(default="neutral", description="情感标签")
    emotion: Optional[str] = Field(default="无感", description="细粒度情绪")
    reasoning: Optional[str] = Field(default="", max_length=100, description="分析理由")
    keywords: Optional[List[str]] = Field(
        default_factory=list, description="关键词列表"
    )

    @field_validator("label")
    def validate_label(cls, v):
        allowed = ["positive", "neutral", "negative"]
        if v not in allowed:
            return "neutral"  # 非法值自动转为neutral
        return v


class SentimentStrategy(ABC):
    """情感分析策略基类"""

    @abstractmethod
    def analyze(self, text: str) -> SentimentResult:
        raise NotImplementedError


class SnowNLPStrategy(SentimentStrategy):
    """基础策略: 使用 SnowNLP (本地/快速)"""

    def analyze(self, text: str) -> SentimentResult:
        if not text:
            return SentimentResult(0.5, "neutral", source="snownlp")

        s = SnowNLP(text)
        score = s.sentiments

        label = "neutral"
        if score > 0.6:
            label = "positive"
        elif score < 0.4:
            label = "negative"

        return SentimentResult(
            score=score,
            label=label,
            keywords=s.keywords(5),
            reasoning="基于文本极性概率计算",
            source="snownlp",
        )


def get_cache_key(text: str, mode: str) -> str:
    """生成缓存键"""
    key_data = f"sentiment:v2:{mode}:{text}"
    return hashlib.md5(key_data.encode()).hexdigest()


def get_from_cache(text: str, mode: str) -> Optional[SentimentResult]:
    """从缓存获取结果"""
    if not REDIS_AVAILABLE:
        return None

    try:
        cache_key = get_cache_key(text, mode)
        cached = redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            return SentimentResult(
                score=data.get("score", 0.5),
                label=data.get("label", "neutral"),
                reasoning=data.get("reasoning"),
                emotion=data.get("emotion"),
                keywords=data.get("keywords", []),
                cached=True,
                source="cache",
            )
    except Exception as e:
        logger.warning(f"缓存读取失败: {e}")

    return None


def save_to_cache(text: str, mode: str, result: SentimentResult) -> None:
    """保存结果到缓存"""
    if not REDIS_AVAILABLE:
        return

    try:
        cache_key = get_cache_key(text, mode)
        data = {
            "score": result.score,
            "label": result.label,
            "reasoning": result.reasoning,
            "emotion": result.emotion,
            "keywords": result.keywords,
        }
        redis_client.setex(cache_key, Config.LLM_CACHE_TTL, json.dumps(data))
    except Exception as e:
        logger.warning(f"缓存写入失败: {e}")


class LLMStrategy(SentimentStrategy):
    """智能策略: 使用 LLM (API/DeepSeek/OpenAI) + 熔断器 + 缓存"""

    def __init__(self):
        self.api_key = Config.LLM_API_KEY
        self.api_url = Config.LLM_API_URL
        self.model = Config.LLM_MODEL
        self.timeout = Config.LLM_TIMEOUT

    def analyze(self, text: str) -> SentimentResult:
        # 1. 检查缓存
        cached_result = get_from_cache(text, "smart")
        if cached_result:
            logger.debug(f"缓存命中: {text[:30]}...")
            return cached_result

        # 2. 检查API Key
        if not self.api_key:
            logger.warning("未配置 LLM_API_KEY，降级使用 SnowNLP")
            return SnowNLPStrategy().analyze(text)

        # 3. 使用熔断器调用LLM
        try:
            result = self._analyze_with_circuit(text)
            # 写入缓存
            save_to_cache(text, "smart", result)
            return result
        except Exception as e:
            logger.error(f"LLM熔断器触发，降级到SnowNLP: {e}")
            return SnowNLPStrategy().analyze(text)

    @circuit(failure_threshold=3, recovery_timeout=60, expected_exception=Exception)
    def _analyze_with_circuit(self, text: str) -> SentimentResult:
        """带熔断器的LLM调用"""
        # 构造 Prompt
        prompt = f"""
        请对以下微博文本进行情感分析。
        文本: "{text}"

        请以JSON格式返回结果，包含以下字段:
        - score: 情感得分(0-1之间，1为最积极)
        - label: 情感标签(positive/neutral/negative)
        - emotion: 细粒度情绪(如: 愤怒, 喜悦, 悲伤, 焦虑, 期待, 讽刺, 无感)
        - reasoning: 简短分析理由(50字以内)
        - keywords: 3-5个关键情绪词

        只返回JSON，不要包含markdown格式或其他内容。
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        # 发送请求（带连接和读取超时）
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=(3, self.timeout),  # (connect timeout, read timeout)
        )
        response.raise_for_status()

        result_json = response.json()
        content = result_json["choices"][0]["message"]["content"]

        # 解析和校验
        return self._parse_and_validate(content)

    def _parse_and_validate(self, content: str) -> SentimentResult:
        """解析LLM输出并进行Schema校验"""
        # 清理可能的 markdown 标记
        content = content.replace("```json", "").replace("```", "").strip()

        try:
            # 尝试解析JSON
            data = json.loads(content)

            # Pydantic Schema校验
            validated = SentimentSchema(**data)

            return SentimentResult(
                score=validated.score,
                label=validated.label,
                reasoning=validated.reasoning,
                emotion=validated.emotion,
                keywords=validated.keywords,
                source="llm",
            )

        except json.JSONDecodeError as e:
            logger.error(f"LLM输出JSON解析失败: {e}, content: {content[:200]}")
            # 尝试容错解析
            return self._fallback_parse(content)
        except Exception as e:
            logger.error(f"LLM输出校验失败: {e}")
            raise  # 抛出异常触发熔断器

    def _fallback_parse(self, content: str) -> SentimentResult:
        """容错解析：从非标准输出中提取关键信息"""
        import re

        # 尝试提取score
        score_match = re.search(
            r'["\']?score["\']?\s*[:=]\s*(0?\.\d+|1\.0|[01])', content
        )
        score = float(score_match.group(1)) if score_match else 0.5

        # 尝试提取label
        label_match = re.search(
            r'["\']?label["\']?\s*[:=]\s*["\']?(positive|neutral|negative)',
            content,
            re.IGNORECASE,
        )
        label = label_match.group(1).lower() if label_match else "neutral"

        # 尝试提取emotion
        emotion_match = re.search(
            r'["\']?emotion["\']?\s*[:=]\s*["\']?([^"\']+)', content
        )
        emotion = emotion_match.group(1) if emotion_match else "无感"

        logger.warning(f"容错解析结果: score={score}, label={label}, emotion={emotion}")

        return SentimentResult(
            score=score,
            label=label,
            emotion=emotion,
            reasoning="容错解析（LLM输出非标准JSON）",
            keywords=[],
            source="llm_fallback",
        )


class CustomModelStrategy(SentimentStrategy):
    """自定义模型策略 (sklearn)"""

    def __init__(self):
        self.model_path = os.path.join(
            Config.BASE_DIR, "model", "best_sentiment_model.pkl"
        )
        self._model = None

    def _load_model(self):
        if self._model is None:
            import sys

            import joblib

            # 添加 model 目录 to sys.path 以便 pickle 可以找到 model_utils
            model_dir = os.path.join(Config.BASE_DIR, "model")
            if model_dir not in sys.path:
                sys.path.append(model_dir)

            if os.path.exists(self.model_path):
                self._model = joblib.load(self.model_path)
        return self._model

    def _analyze_with_model(self, text: str) -> SentimentResult:
        """
        使用本地模型进行情感分析

        Args:
            text: 待分析文本

        Returns:
            SentimentResult: 情感分析结果
        """
        model = self._load_model()
        if not model:
            raise RuntimeError("模型未加载成功")

        # 长文本截断处理（模型通常有输入长度限制）
        max_length = 512
        if len(text) > max_length:
            logger.debug(f"文本长度超过{max_length}，进行截断处理")
            text = text[:max_length]

        # 预测类别
        prediction = model.predict([text])[0]

        # 预测概率 (如果模型支持)
        score = 0.5
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba([text])[0]
            score = float(max(probs))

        # 映射标签
        label_map = {0: "negative", 1: "neutral", 2: "positive"}
        label = label_map.get(prediction, "neutral")

        # 如果预测出来是字符串, 尝试转换
        if isinstance(prediction, str):
            if prediction in ["positive", "pos"]:
                label = "positive"
            elif prediction in ["negative", "neg"]:
                label = "negative"
            else:
                label = "neutral"

        return SentimentResult(
            score=score,
            label=label,
            reasoning="基于自定义训练模型预测",
            keywords=[],
            source="custom_model",
        )

    def analyze(self, text: str) -> SentimentResult:
        """
        执行情感分析，带缓存和错误降级处理

        Args:
            text: 待分析文本

        Returns:
            SentimentResult: 情感分析结果
        """
        if not text or not text.strip():
            return SentimentResult(0.5, "neutral", reasoning="空文本", source="custom_model")

        # 1. 检查缓存
        cache_key = get_cache_key(text, "custom_model")
        if REDIS_AVAILABLE:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return SentimentResult(
                        score=data.get("score", 0.5),
                        label=data.get("label", "neutral"),
                        reasoning="缓存结果",
                        keywords=data.get("keywords", []),
                        cached=True,
                        source="cache",
                    )
            except Exception as e:
                logger.debug(f"缓存读取失败: {e}")

        # 2. 调用模型分析
        try:
            result = self._analyze_with_model(text)
        except Exception as e:
            logger.error(f"模型分析失败，降级到SnowNLP: {e}")
            return SnowNLPStrategy().analyze(text)

        # 3. 写入缓存
        if REDIS_AVAILABLE:
            try:
                data = {
                    "score": result.score,
                    "label": result.label,
                    "keywords": result.keywords,
                }
                redis_client.setex(cache_key, Config.LLM_CACHE_TTL, json.dumps(data))
            except Exception as e:
                logger.debug(f"缓存写入失败: {e}")

        return result


class SentimentService:
    """情感分析服务工厂"""

    @staticmethod
    def analyze(text: str, mode: str = "custom") -> dict:
        """
        执行情感分析
        Args:
            text: 待分析文本
            mode: 模式 'custom'(默认), 'smart'(LLM), 'simple'(SnowNLP)
        Returns:
            dict: 分析结果字典
        """
        if mode == "smart":
            strategy = LLMStrategy()
        elif mode == "custom":
            strategy = CustomModelStrategy()
        else:
            strategy = SnowNLPStrategy()

        result = strategy.analyze(text)
        return result.to_dict()

    @staticmethod
    def analyze_batch(texts: list, mode: str = "smart") -> list:
        """
        批量情感分析
        Args:
            texts: 文本列表
            mode: 分析模式
        Returns:
            list: 结果列表
        """
        results = []
        for text in texts:
            try:
                result = SentimentService.analyze(text, mode)
                results.append(result)
            except Exception as e:
                logger.error(f"批量分析失败: {e}")
                # 失败时返回中性结果
                results.append(
                    {
                        "score": 0.5,
                        "label": "neutral",
                        "reasoning": "分析失败",
                        "emotion": "未知",
                        "keywords": [],
                        "error": True,
                    }
                )
        return results

    @staticmethod
    def analyze_distribution(
        texts: list, mode: str = "simple", sample_size: int = 100
    ) -> dict:
        """
        统计文本情感分布并使用 Redis 缓存结果，避免接口层重复计算。
        """
        sentiment_counts = {"正面": 0, "中性": 0, "负面": 0}
        sample_texts = [
            str(text).strip() for text in (texts or []) if str(text).strip()
        ][:sample_size]

        if not sample_texts:
            return sentiment_counts

        cache_key = None
        if REDIS_AVAILABLE:
            # 限制 key_data 长度，避免超长文本导致内存/性能问题
            # 采样最多前100个字符的文本摘要用于生成缓存键
            max_text_len = 100
            max_samples = 50
            truncated_texts = [
                t[:max_text_len] for t in sample_texts[:max_samples]
            ]
            key_data = (
                f"sentiment:distribution:{mode}:{sample_size}:{'|'.join(truncated_texts)}"
            )
            cache_key = hashlib.sha256(key_data.encode()).hexdigest()
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    loaded = json.loads(cached)
                    if isinstance(loaded, dict):
                        return {
                            "正面": int(loaded.get("正面", 0)),
                            "中性": int(loaded.get("中性", 0)),
                            "负面": int(loaded.get("负面", 0)),
                        }
            except Exception as e:
                logger.warning(f"情感分布缓存读取失败: {e}")

        results = SentimentService.analyze_batch(sample_texts, mode)
        for item in results:
            label = (item or {}).get("label", "neutral")
            if label == "positive":
                sentiment_counts["正面"] += 1
            elif label == "negative":
                sentiment_counts["负面"] += 1
            else:
                sentiment_counts["中性"] += 1

        if REDIS_AVAILABLE and cache_key:
            try:
                redis_client.setex(
                    cache_key,
                    Config.LLM_CACHE_TTL,
                    json.dumps(sentiment_counts, ensure_ascii=False),
                )
            except Exception as e:
                logger.warning(f"情感分布缓存写入失败: {e}")

        return sentiment_counts

    @staticmethod
    def get_cache_stats() -> dict:
        """获取缓存统计信息"""
        if not REDIS_AVAILABLE:
            return {"available": False, "message": "Redis未连接"}

        try:
            info = redis_client.info("memory")
            return {
                "available": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "keys": redis_client.dbsize(),
                "hit_rate": "N/A",  # 需要更复杂的统计
            }
        except Exception as e:
            return {"available": False, "error": str(e)}

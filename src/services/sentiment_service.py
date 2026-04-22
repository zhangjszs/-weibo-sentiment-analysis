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

from src.config.settings import Config
from .sentiment_dictionaries import sentiment_dict

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
        snownlp_score = s.sentiments

        # 使用情感词典计算得分
        dict_score, positive_words, negative_words = sentiment_dict.get_sentiment_score(text)

        # 检测否定句式
        negation_patterns = ['不', '没', '无', '非', '未', '别', '不要', '没有', '不是', '不会', '不能']
        negation_count = sum(1 for pattern in negation_patterns if pattern in text)
        
        # 检测讽刺和反语
        sarcasm_patterns = ['呵呵', '太棒了', '真的', '一点都不', '可真是', '绝了', '服了', '醉了', '吐了', '无语']
        is_sarcastic = any(pattern in text for pattern in sarcasm_patterns)
        
        # 检测程度副词
        degree_adverbs = {
            '非常': 1.5, '特别': 1.4, '十分': 1.3, '很': 1.2, '挺': 1.1,
            '有点': 0.8, '稍微': 0.7, '比较': 0.9, '相当': 1.2, '极其': 1.6
        }
        degree_factor = 1.0
        for adverb, factor in degree_adverbs.items():
            if adverb in text:
                degree_factor = factor
                break
        
        # 处理否定句式
        if negation_count > 0:
            # 对于否定句，反转情感倾向
            snownlp_score = 1.0 - snownlp_score
            dict_score = 1.0 - dict_score
            # 否定强度调整
            negation_strength = min(negation_count * 0.2, 0.5)
            snownlp_score = max(0.0, min(1.0, snownlp_score - negation_strength))
            dict_score = max(0.0, min(1.0, dict_score - negation_strength))
        
        # 处理讽刺和反语
        if is_sarcastic:
            # 对于讽刺和反语，反转情感倾向并增强效果
            snownlp_score = 1.0 - snownlp_score
            dict_score = 1.0 - dict_score
            # 讽刺强度调整
            sarcasm_strength = 0.3
            if any(word in text for word in ['好', '棒', '开心', '高兴', '喜欢']):
                snownlp_score = max(0.0, snownlp_score - sarcasm_strength)
                dict_score = max(0.0, dict_score - sarcasm_strength)
            elif any(word in text for word in ['不生气', '没关系', '还好']):
                snownlp_score = max(0.0, snownlp_score - sarcasm_strength)
                dict_score = max(0.0, dict_score - sarcasm_strength)
        
        # 应用程度副词调整
        if degree_factor != 1.0:
            if snownlp_score > 0.5:
                # 正向情感增强
                snownlp_score = min(1.0, (snownlp_score - 0.5) * degree_factor + 0.5)
            else:
                # 负向情感增强
                snownlp_score = max(0.0, 0.5 - (0.5 - snownlp_score) * degree_factor)
            
            if dict_score > 0.5:
                dict_score = min(1.0, (dict_score - 0.5) * degree_factor + 0.5)
            else:
                dict_score = max(0.0, 0.5 - (0.5 - dict_score) * degree_factor)

        # 融合得分：SnowNLP得分占60%，情感词典得分占40%
        score = snownlp_score * 0.6 + dict_score * 0.4
        score = max(0.0, min(1.0, score))  # 确保得分在0-1范围内

        label = "neutral"
        if score > 0.65:
            label = "positive"
        elif score < 0.35:
            label = "negative"

        # 细粒度情感识别
        emotion = self._get_emotion(text, positive_words, negative_words, score)

        # 对于特定负面情感，强制调整为negative
        if emotion in ['愤怒', '悲伤', '失望', '焦虑', '无奈', '讽刺'] and label == 'neutral':
            label = "negative"
            score = min(score, 0.35)

        # 对于特定正面情感，强制调整为positive
        if emotion in ['喜悦', '感动', '兴奋', '期待'] and label == 'neutral':
            label = "positive"
            score = max(score, 0.65)

        return SentimentResult(
            score=score,
            label=label,
            keywords=s.keywords(5),
            reasoning=f"基于SnowNLP和情感词典融合计算，正向词: {positive_words}, 负向词: {negative_words}，否定词数量: {negation_count}, 是否讽刺: {is_sarcastic}",
            emotion=emotion,
            source="snownlp",
        )

    def _get_emotion(self, text: str, positive_words: list, negative_words: list, score: float) -> str:
        """
        细粒度情感识别
        
        Args:
            text: 待分析文本
            positive_words: 正向词列表
            negative_words: 负向词列表
            score: 情感得分
            
        Returns:
            str: 细粒度情感标签
        """
        # 检测讽刺和反语
        sarcasm_patterns = [
            ('呵呵', '讽刺'),
            ('太棒了', '反语'),
            ('真的', '可能反语'),
            ('一点都不', '反语'),
            ('可真是', '讽刺'),
            ('绝了', '讽刺'),
            ('服了', '无奈'),
            ('醉了', '无奈'),
            ('吐了', '厌恶'),
            ('无语', '无奈'),
        ]
        
        for pattern, emotion in sarcasm_patterns:
            if pattern in text:
                # 对于讽刺和反语，情感倾向通常与字面意思相反
                if any(word in text for word in ['好', '棒', '开心', '高兴', '喜欢']):
                    return "讽刺"
                elif any(word in text for word in ['不生气', '没关系', '还好']):
                    return "愤怒"
                else:
                    return emotion
        
        # 检测网络用语情感
        internet_emotions = {
            'yyds': '喜悦',
            '永远的神': '喜悦',
            '绝绝子': '喜悦',
            '666': '喜悦',
            'nb': '喜悦',
            '牛批': '喜悦',
            '牛逼': '喜悦',
            '奥利给': '喜悦',
            '给力': '喜悦',
            'nice': '喜悦',
            '赞': '喜悦',
            '好评': '喜悦',
            '种草': '喜悦',
            '安利': '喜悦',
            '真香': '喜悦',
            '爱了': '喜悦',
            '破防': '悲伤',
            '破防了': '悲伤',
            '崩溃': '悲伤',
            '绝望': '悲伤',
            '难受': '悲伤',
            '痛苦': '悲伤',
            '伤心': '悲伤',
            '难过': '悲伤',
            '生气': '愤怒',
            '愤怒': '愤怒',
            '恼火': '愤怒',
            '烦躁': '愤怒',
            '焦虑': '焦虑',
            '担忧': '焦虑',
            '害怕': '恐惧',
            '恐惧': '恐惧',
            '紧张': '焦虑',
            '压力': '焦虑',
            '负担': '焦虑',
            '烦恼': '焦虑',
            '无聊': '无奈',
            '枯燥': '无奈',
            '失望': '失望',
            '绝望': '悲伤',
        }
        
        for word, emotion in internet_emotions.items():
            if word in text:
                return emotion
        
        # 检测emoji表情情感
        emoji_emotions = {
            '😄': '喜悦', '😊': '喜悦', '😃': '喜悦', '😁': '喜悦', '😆': '喜悦', '😅': '喜悦', '🤣': '喜悦', '😂': '喜悦',
            '😍': '喜悦', '😘': '喜悦', '😗': '喜悦', '😙': '喜悦', '😚': '喜悦', '😋': '喜悦', '😛': '喜悦', '😝': '喜悦',
            '🤩': '喜悦', '🥳': '喜悦', '👍': '喜悦', '👌': '喜悦', '✌️': '喜悦', '🤞': '喜悦', '🤟': '喜悦', '🤘': '喜悦',
            '😢': '悲伤', '😭': '悲伤', '😞': '悲伤', '😔': '悲伤', '😟': '悲伤', '😕': '悲伤', '🙁': '悲伤', '☹️': '悲伤',
            '😤': '愤怒', '😠': '愤怒', '😡': '愤怒', '🤬': '愤怒',
            '😰': '焦虑', '😥': '焦虑', '😓': '焦虑', '😨': '焦虑',
            '😱': '恐惧', '😨': '恐惧', '😰': '恐惧',
            '🤢': '厌恶', '🤮': '厌恶',
            '😴': '无感', '🤔': '无感', '😐': '无感', '😑': '无感',
        }
        
        for emoji, emotion in emoji_emotions.items():
            if emoji in text:
                return emotion
        
        # 基于情感词和得分判断细粒度情感
        if score > 0.7:
            if any(word in text for word in ['开心', '高兴', '快乐', '喜悦', '兴奋', '激动', '惊喜']):
                return "喜悦"
            elif any(word in text for word in ['感动', '温暖', '感激', '感谢']):
                return "感动"
            elif any(word in text for word in ['惊喜', '兴奋', '激动']):
                return "兴奋"
            else:
                return "积极"
        elif score < 0.3:
            if any(word in text for word in ['生气', '愤怒', '恼火', '烦躁', '不满']):
                return "愤怒"
            elif any(word in text for word in ['伤心', '难过', '悲伤', '痛苦', '流泪']):
                return "悲伤"
            elif any(word in text for word in ['失望', '遗憾', '沮丧']):
                return "失望"
            elif any(word in text for word in ['厌恶', '讨厌', '反感']):
                return "厌恶"
            else:
                return "消极"
        else:
            if any(word in text for word in ['担心', '焦虑', '紧张', '压力', '担忧']):
                return "焦虑"
            elif any(word in text for word in ['期待', '希望', '憧憬', '向往']):
                return "期待"
            elif any(word in text for word in ['麻烦', '压力', '负担', '无奈']):
                return "无奈"
            elif any(word in text for word in ['平静', '淡定', '从容']):
                return "平静"
            else:
                return "无感"


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
        请对以下文本进行细粒度情感分析，需要深入理解文本的整体语境、隐含情绪和上下文关联。
        文本: "{text}"

        分析要求：
        1. 情感得分(score): 0-1之间，1为最积极，0为最消极
        2. 情感标签(label): positive(积极)/neutral(中性)/negative(消极)
        3. 细粒度情绪(emotion): 从以下类别中选择最符合的一个：
           喜悦、愤怒、悲伤、焦虑、期待、感动、兴奋、失望、无奈、讽刺、惊讶、恐惧、厌恶、平静、无感
        4. 分析理由(reasoning): 详细说明情感判断的依据，包括关键词分析、语境理解、否定句式处理、反语识别等
        5. 关键词(keywords): 提取3-5个最能代表情感的词语，包括网络用语和新兴词汇

        请以JSON格式返回结果，严格按照以下格式：
        {{"score": 0.0-1.0, "label": "positive/neutral/negative", "emotion": "具体情绪", "reasoning": "分析理由", "keywords": ["关键词1", "关键词2", ...]}}

        注意：
        - 只返回JSON，不要包含任何其他内容
        - 确保JSON格式正确，可直接解析
        - 情感分析要考虑上下文语境，不仅是字面意思
        - 对于讽刺、反语、否定句式等复杂表达，要准确识别其真实情感
        - 要特别注意网络用语、emoji表情和新兴词汇的情感含义
        - 分析时要考虑文本的整体语境，而不是孤立地分析每个词语
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
        # 清理可能的 markdown 标记和多余字符
        content = content.replace("```json", "").replace("```", "").strip()
        content = content.replace("\n", "").replace("\r", "")
        
        # 尝试从文本中提取JSON部分
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)

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
            # 尝试容错解析，而不是直接触发熔断器
            return self._fallback_parse(content)

    def _fallback_parse(self, content: str) -> SentimentResult:
        """容错解析：从非标准输出中提取关键信息"""
        import re

        # 尝试提取score
        score_match = re.search(
            r'["\']?score["\']?\s*[:=]\s*(0?\.\d+|1\.0|[01])', content
        )
        score = float(score_match.group(1)) if score_match else 0.5
        score = max(0.0, min(1.0, score))  # 确保score在0-1范围内

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
        emotion = emotion_match.group(1).strip() if emotion_match else "无感"
        
        # 尝试提取reasoning
        reasoning_match = re.search(
            r'["\']?reasoning["\']?\s*[:=]\s*["\']?([^"\']+)', content
        )
        reasoning = reasoning_match.group(1).strip() if reasoning_match else "容错解析（LLM输出非标准JSON）"
        
        # 尝试提取keywords
        keywords_match = re.search(
            r'["\']?keywords["\']?\s*[:=]\s*\[(.*?)\]', content
        )
        keywords = []
        if keywords_match:
            keywords_str = keywords_match.group(1)
            # 提取关键词
            keyword_pattern = re.findall(r'["\']?([^"\',\s]+)["\']?', keywords_str)
            keywords = [k.strip() for k in keyword_pattern[:5]]  # 最多提取5个关键词

        logger.warning(f"容错解析结果: score={score}, label={label}, emotion={emotion}")

        return SentimentResult(
            score=score,
            label=label,
            emotion=emotion,
            reasoning=reasoning,
            keywords=keywords,
            source="llm_fallback",
        )


class CustomModelStrategy(SentimentStrategy):
    """自定义模型策略 (sklearn)"""

    def __init__(self):
        self.model_path = os.path.join(
            Config.BASE_DIR, "model", "best_sentiment_model.pkl"
        )
        self._model = None
        self._model_metadata = None

    def _load_model(self):
        if self._model is None:
            import sys

            import joblib

            # 添加 model 目录 to sys.path 以便 pickle 可以找到 model_utils
            model_dir = os.path.join(Config.BASE_DIR, "model")
            if model_dir not in sys.path:
                sys.path.append(model_dir)

            if os.path.exists(self.model_path):
                # 使用版本管理加载模型
                try:
                    from src.model.model_version_manager import load_model_with_versioning
                    self._model, self._model_metadata = load_model_with_versioning(model_dir)
                except Exception as e:
                    logger.warning(f"使用版本管理加载模型失败，使用普通加载: {e}")
                    self._model = joblib.load(self.model_path)
                    self._model_metadata = {"loaded": True, "model_path": self.model_path}
        return self._model

    def _analyze_with_model(self, text: str) -> SentimentResult:
        """
        使用本地模型进行情感分析

        Args:
            text: 待分析文本

        Returns:
            SentimentResult: 情感分析结果
        """
        return self._analyze_batch_with_model([text])[0]

    def _analyze_batch_with_model(self, texts: list) -> list:
        """
        批量分析文本

        Args:
            texts: 文本列表

        Returns:
            list: 情感分析结果列表
        """
        model = self._load_model()
        if not model:
            raise RuntimeError("模型未加载成功")

        # 长文本截断处理
        max_length = 512
        processed_texts = []
        for text in texts:
            if len(text) > max_length:
                processed_texts.append(text[:max_length])
            else:
                processed_texts.append(text)

        # 记录开始时间
        import time
        start_time = time.time()

        # 批量预测
        predictions = model.predict(processed_texts)
        
        # 批量获取概率
        scores = []
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(processed_texts)
            scores = [float(max(prob)) for prob in probs]
        else:
            scores = [0.5] * len(texts)

        # 计算处理时间
        processing_time = time.time() - start_time

        # 处理结果
        results = []
        for i, (text, prediction, score) in enumerate(zip(texts, predictions, scores)):
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

            # 提取关键词
            keywords = []
            try:
                from model.social_media_preprocessor import SocialMediaPreprocessor
                preprocessor = SocialMediaPreprocessor()
                features = preprocessor.get_social_features(text)
                # 可以根据需要从特征中提取关键词
            except Exception as e:
                logger.debug(f"提取关键词失败: {e}")

            # 构建推理理由
            reasoning = "基于自定义训练模型预测"
            if self._model_metadata:
                version = self._model_metadata.get("current_version", "unknown")
                reasoning += f" (版本: {version})"

            # 记录预测（使用监控）
            try:
                from src.model.model_monitor import ModelMonitor
                monitor = ModelMonitor()
                monitor.log_prediction(text, label, score, processing_time / len(texts))
            except Exception as e:
                logger.debug(f"记录预测监控失败: {e}")

            results.append(SentimentResult(
                score=score,
                label=label,
                reasoning=reasoning,
                keywords=keywords,
                source="custom_model",
            ))

        return results

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

    def analyze_batch(self, texts: list) -> list:
        """
        批量分析文本

        Args:
            texts: 文本列表

        Returns:
            list: 情感分析结果列表
        """
        if not texts:
            return []

        # 1. 检查缓存
        results = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                results.append(SentimentResult(0.5, "neutral", reasoning="空文本", source="custom_model"))
                continue

            # 检查缓存
            cache_key = get_cache_key(text, "custom_model")
            if REDIS_AVAILABLE:
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        data = json.loads(cached)
                        results.append(SentimentResult(
                            score=data.get("score", 0.5),
                            label=data.get("label", "neutral"),
                            reasoning="缓存结果",
                            keywords=data.get("keywords", []),
                            cached=True,
                            source="cache",
                        ))
                        continue
                except Exception as e:
                    logger.debug(f"缓存读取失败: {e}")

            # 未缓存的文本
            uncached_texts.append(text)
            uncached_indices.append(i)

        # 2. 批量分析未缓存的文本
        if uncached_texts:
            try:
                batch_results = self._analyze_batch_with_model(uncached_texts)
                
                # 填充结果
                for i, result in zip(uncached_indices, batch_results):
                    results.insert(i, result)
                    
                    # 写入缓存
                    if REDIS_AVAILABLE:
                        try:
                            cache_key = get_cache_key(uncached_texts[uncached_indices.index(i)], "custom_model")
                            data = {
                                "score": result.score,
                                "label": result.label,
                                "keywords": result.keywords,
                            }
                            redis_client.setex(cache_key, Config.LLM_CACHE_TTL, json.dumps(data))
                        except Exception as e:
                            logger.debug(f"缓存写入失败: {e}")
            except Exception as e:
                logger.error(f"批量分析失败，降级到SnowNLP: {e}")
                # 降级到逐个分析
                snow_strategy = SnowNLPStrategy()
                for i, text in zip(uncached_indices, uncached_texts):
                    results.insert(i, snow_strategy.analyze(text))

        return results


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
        if not texts:
            return []

        # 对于自定义模型，使用批处理
        if mode == "custom":
            try:
                strategy = CustomModelStrategy()
                batch_results = strategy.analyze_batch(texts)
                return [result.to_dict() for result in batch_results]
            except Exception as e:
                logger.error(f"批量分析失败，降级到逐个分析: {e}")

        # 其他模式使用逐个分析
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

    @staticmethod
    def analyze_sequence(texts: list, mode: str = "custom") -> dict:
        """
        分析文本序列的情感，考虑上下文关联，添加情感突变检测
        
        Args:
            texts: 文本序列列表
            mode: 分析模式
            
        Returns:
            dict: 包含序列情感分析结果和情感突变信息
        """
        if not texts:
            return {
                "sequence_analysis": [],
                "overall_sentiment": {
                    "label": "neutral",
                    "score": 0.5
                },
                "sentiment_changes": [],
                "emotion_transitions": [],
                "analysis_count": 0
            }
        
        # 分析每个文本的情感
        sequence_analysis = []
        previous_score = None
        previous_emotion = None
        sentiment_changes = []
        emotion_transitions = []
        
        for i, text in enumerate(texts):
            result = SentimentService.analyze(text, mode)
            sequence_analysis.append({
                "index": i,
                "text": text,
                "sentiment": result
            })
            
            # 检测情感突变
            if previous_score is not None:
                score_diff = abs(result["score"] - previous_score)
                if score_diff > 0.3:
                    sentiment_changes.append({
                        "from_index": i-1,
                        "to_index": i,
                        "from_score": previous_score,
                        "to_score": result["score"],
                        "change_score": score_diff,
                        "from_label": sequence_analysis[i-1]["sentiment"]["label"],
                        "to_label": result["label"]
                    })
            
            # 检测情感类型变化
            if previous_emotion is not None and result["emotion"] != previous_emotion:
                emotion_transitions.append({
                    "from_index": i-1,
                    "to_index": i,
                    "from_emotion": previous_emotion,
                    "to_emotion": result["emotion"]
                })
            
            previous_score = result["score"]
            previous_emotion = result["emotion"]
        
        # 计算整体情感
        scores = [item["sentiment"]["score"] for item in sequence_analysis]
        average_score = sum(scores) / len(scores) if scores else 0.5
        
        overall_label = "neutral"
        if average_score > 0.65:
            overall_label = "positive"
        elif average_score < 0.35:
            overall_label = "negative"
        
        return {
            "sequence_analysis": sequence_analysis,
            "overall_sentiment": {
                "label": overall_label,
                "score": average_score
            },
            "sentiment_changes": sentiment_changes,
            "emotion_transitions": emotion_transitions,
            "analysis_count": len(sequence_analysis)
        }

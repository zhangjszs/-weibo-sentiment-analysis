"""情感分析策略实现。

拆分自原 ``sentiment_service.py``，逻辑保持不变。包含：
- ``SentimentStrategy`` 抽象基类
- ``SnowNLPStrategy`` 本地 SnowNLP + 词典融合
- ``LLMStrategy`` LLM + 熔断器 + 缓存
- ``CustomModelStrategy`` 自定义模型（面向 ModelBackend 抽象）
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests
from circuitbreaker import circuit
from snownlp import SnowNLP

from config.settings import Config
from ..sentiment_dictionaries import sentiment_dict
from .models import SentimentResult, SentimentSchema
from .cache import get_from_cache, save_to_cache

logger = logging.getLogger(__name__)


class SentimentStrategy(ABC):
    """情感分析策略基类"""

    @abstractmethod
    def analyze(self, text: str) -> SentimentResult:
        raise NotImplementedError


class SnowNLPStrategy(SentimentStrategy):
    """基础策略: 使用 SnowNLP (本地/快速)"""

    # 预定义的模式和词典（类变量，避免重复创建）
    negation_patterns = {'不', '没', '无', '非', '未', '别', '不要', '没有', '不是', '不会', '不能'}
    sarcasm_patterns = {'呵呵', '太棒了', '真的', '一点都不', '可真是', '绝了', '服了', '醉了', '吐了', '无语'}
    degree_adverbs = {
        '非常': 1.5, '特别': 1.4, '十分': 1.3, '很': 1.2, '挺': 1.1,
        '有点': 0.8, '稍微': 0.7, '比较': 0.9, '相当': 1.2, '极其': 1.6
    }
    negative_indicators = {'差', '糟糕', '烂', '垃圾', '失望', '讨厌', '生气', '难过', '悲伤', '痛苦',
                         '不好', '失败', '错误', '麻烦', '困难', '复杂', '缓慢', '低效', '不安全',
                         '不可靠', '不稳定', '落后', '不专业', '冷漠', '冰冷', '无聊', '枯燥',
                         '不推荐', '不值得', '物有所值', '性价比低', '质量差', '服务差', '态度差',
                         '难用', '不实用', '不方便', '慢', '丑陋', '过时', '弱小', '破防', '破防了',
                         '无语', '醉了', '吐了', '服了', '晕了', '崩溃', '绝望', '难受', '痛苦',
                         '伤心', '难过', '生气', '愤怒', '恼火', '烦躁', '焦虑', '担忧', '害怕',
                         '恐惧', '紧张', '压力', '负担', '烦恼', '无聊', '枯燥', '失望', '绝望'}
    positive_indicators = {'好', '优秀', '棒', '赞', '满意', '喜欢', '高兴', '开心', '快乐', '幸福',
                         '美好', '精彩', '出色', '成功', '完美', '舒适', '便利', '快速', '高效',
                         '安全', '可靠', '稳定', '创新', '专业', '贴心', '温暖', '感动', '惊喜',
                         '推荐', '值得', '物超所值', '性价比高', '质量好', '服务好', '态度好',
                         '好用', '实用', '方便', '快捷', '美观', '时尚', '流行', '先进', '强大',
                         'yyds', '永远的神', '绝绝子', '666', 'nb', '牛批', '牛逼', '厉害',
                         '奥利给', '给力', 'nice', '赞', '好评', '种草', '安利', '真香', '爱了'}
    neutral_indicators = {'一般', '普通', '还行', '还好', '马马虎虎', '凑合', '一般般', '平常', '正常', '常规'}
    positive_emotions = {'喜悦', '感动', '兴奋', '期待'}
    negative_emotions = {'愤怒', '悲伤', '失望', '焦虑', '无奈', '讽刺'}

    @staticmethod
    def _adjust_score(score: float, factor: float) -> float:
        if score > 0.5:
            return min(1.0, (score - 0.5) * factor + 0.5)
        return max(0.0, 0.5 - (0.5 - score) * factor)

    def _compute_scores(self, text: str):
        s = SnowNLP(text)
        snownlp_score = s.sentiments
        dict_score, pos_words, neg_words = sentiment_dict.get_sentiment_score(text)

        negation_count = sum(1 for p in self.negation_patterns if p in text)
        is_sarcastic = any(p in text for p in self.sarcasm_patterns)

        degree_factor = 1.0
        for adverb, factor in self.degree_adverbs.items():
            if adverb in text:
                degree_factor = factor
                break

        if negation_count > 0:
            snownlp_score = 1.0 - snownlp_score
            dict_score = 1.0 - dict_score
            strength = min(negation_count * 0.2, 0.4)
            snownlp_score = max(0.0, min(1.0, snownlp_score - strength))
            dict_score = max(0.0, min(1.0, dict_score - strength))

        if is_sarcastic:
            pos_words_set = {'好', '棒', '开心', '高兴', '喜欢', '优秀', '厉害'}
            if any(w in text for w in pos_words_set):
                snownlp_score = 1.0 - snownlp_score
                dict_score = 1.0 - dict_score
                snownlp_score = max(0.0, min(1.0, snownlp_score - 0.2))
                dict_score = max(0.0, min(1.0, dict_score - 0.2))

        if degree_factor != 1.0:
            snownlp_score = self._adjust_score(snownlp_score, degree_factor)
            dict_score = self._adjust_score(dict_score, degree_factor)

        weight = 0.7 if dict_score < 0.5 else 0.5
        score = max(0.0, min(1.0, snownlp_score * (1 - weight) + dict_score * weight))

        return s, score, snownlp_score, dict_score, pos_words, neg_words, negation_count, is_sarcastic, degree_factor

    def _determine_label(self, score: float, text: str, negation_count: int, emotion: str) -> str:
        label = "neutral"
        if score > 0.6:
            label = "positive"
        elif score < 0.4:
            label = "negative"

        if any(ind in text for ind in self.negative_indicators) and score > 0.5:
            return "negative"
        if any(ind in text for ind in self.positive_indicators) and negation_count == 0 and score < 0.5:
            return "positive"
        if any(ind in text for ind in self.neutral_indicators):
            return "neutral"
        if negation_count > 0:
            return "negative"
        if emotion in self.negative_emotions:
            return "negative"
        if emotion in self.positive_emotions:
            return "positive"
        return label

    def _build_reasoning(self, pos_words, neg_words, negation_count, is_sarcastic,
                         degree_factor, dict_score, snownlp_score, score, emotion) -> str:
        parts = ["基于SnowNLP和情感词典融合计算"]
        if pos_words:
            parts.append(f"正向词: {', '.join(pos_words[:3])}")
        if neg_words:
            parts.append(f"负向词: {', '.join(neg_words[:3])}")
        if negation_count > 0:
            parts.append(f"包含{negation_count}个否定词，情感倾向反转")
        if is_sarcastic:
            parts.append("检测到讽刺或反语，情感倾向反转")
        if degree_factor != 1.0:
            parts.append(f"包含程度副词，情感强度调整为{degree_factor}倍")
        if dict_score < 0.5:
            parts.append("负面文本，情感词典权重更高")
        parts.append(f"最终得分: SnowNLP({snownlp_score:.2f}) + 情感词典({dict_score:.2f}) = {score:.2f}")
        # Phase 3.7：内部用英文 label，展示层用 label_to_chinese 转中文
        from utils.sentiment import label_to_chinese
        label_en = "positive" if score > 0.6 else ("negative" if score < 0.4 else "neutral")
        parts.append(f"判断为{label_to_chinese(label_en)}情感")
        if emotion != "无感":
            parts.append(f"细粒度情感: {emotion}")
        return "，".join(parts)

    _EMOTION_RELATED_WORDS = {
        "喜悦": ["开心", "高兴", "快乐", "喜悦", "兴奋", "激动", "惊喜", "赞", "好", "棒"],
        "愤怒": ["生气", "愤怒", "恼火", "烦躁", "不满", "讨厌", "恨"],
        "悲伤": ["伤心", "难过", "悲伤", "痛苦", "流泪", "失望", "遗憾"],
        "焦虑": ["担心", "焦虑", "紧张", "压力", "担忧"],
        "期待": ["期待", "希望", "憧憬", "向往"],
        "感动": ["感动", "温暖", "感激", "感谢"],
        "兴奋": ["兴奋", "激动", "亢奋"],
        "失望": ["失望", "遗憾", "沮丧"],
        "无奈": ["无奈", "无语", "尴尬"],
        "讽刺": ["讽刺", "反语", "嘲笑"],
        "惊讶": ["惊讶", "震惊", "意外"],
        "恐惧": ["害怕", "恐惧", "担心"],
        "厌恶": ["厌恶", "讨厌", "反感"],
        "平静": ["平静", "淡定", "从容"],
    }

    def _extract_keywords(self, s, pos_words, neg_words, emotion, text) -> list:
        base = s.keywords(10)
        base_set = set(base)
        sentiment_kw = [w for w in (pos_words + neg_words) if w in base_set]

        emotion_kw = []
        if emotion != "无感":
            for w in self._EMOTION_RELATED_WORDS.get(emotion, []):
                if w in text and w not in emotion_kw:
                    emotion_kw.append(w)

        seen = set()
        result = []
        for kw in sentiment_kw + emotion_kw + base:
            if kw not in seen:
                result.append(kw)
                seen.add(kw)
        return result[:5]

    def analyze(self, text: str) -> SentimentResult:
        if not text:
            return SentimentResult(0.5, "neutral", source="snownlp")

        s, score, sn_score, dict_score, pos, neg, neg_cnt, sarcastic, degree = self._compute_scores(text)
        emotion = self._get_emotion(text, pos, neg, score)
        label = self._determine_label(score, text, neg_cnt, emotion)

        adj_score = min(score, 0.45) if label == "negative" else (max(score, 0.55) if label == "positive" else score)
        if any(ind in text for ind in self.neutral_indicators):
            adj_score = 0.5

        reasoning = self._build_reasoning(pos, neg, neg_cnt, sarcastic, degree, dict_score, sn_score, adj_score, emotion)
        keywords = self._extract_keywords(s, pos, neg, emotion, text)

        return SentimentResult(
            score=adj_score, label=label, keywords=keywords,
            reasoning=reasoning, emotion=emotion, source="snownlp",
        )

    # 预定义的情感模式（类变量，避免重复创建）
    sarcasm_patterns = {
        '呵呵': '讽刺',
        '太棒了': '反语',
        '真的': '可能反语',
        '一点都不': '反语',
        '可真是': '讽刺',
        '绝了': '讽刺',
        '服了': '无奈',
        '醉了': '无奈',
        '吐了': '厌恶',
        '无语': '无奈'
    }

    internet_emotions = {
        'yyds': '喜悦', '永远的神': '喜悦', '绝绝子': '喜悦', '666': '喜悦', 'nb': '喜悦',
        '牛批': '喜悦', '牛逼': '喜悦', '奥利给': '喜悦', '给力': '喜悦', 'nice': '喜悦',
        '赞': '喜悦', '好评': '喜悦', '种草': '喜悦', '安利': '喜悦', '真香': '喜悦', '爱了': '喜悦',
        '破防': '悲伤', '破防了': '悲伤', '崩溃': '悲伤', '绝望': '悲伤', '难受': '悲伤',
        '痛苦': '悲伤', '伤心': '悲伤', '难过': '悲伤',
        '生气': '愤怒', '愤怒': '愤怒', '恼火': '愤怒', '烦躁': '愤怒',
        '焦虑': '焦虑', '担忧': '焦虑', '紧张': '焦虑', '压力': '焦虑', '负担': '焦虑', '烦恼': '焦虑',
        '害怕': '恐惧', '恐惧': '恐惧',
        '无聊': '无奈', '枯燥': '无奈',
        '失望': '失望'
    }

    emoji_emotions = {
        '😄': '喜悦', '😊': '喜悦', '😃': '喜悦', '😁': '喜悦', '😆': '喜悦', '😅': '喜悦', '🤣': '喜悦', '😂': '喜悦',
        '😍': '喜悦', '😘': '喜悦', '😗': '喜悦', '😙': '喜悦', '😚': '喜悦', '😋': '喜悦', '😛': '喜悦', '😝': '喜悦',
        '🤩': '喜悦', '🥳': '喜悦', '👍': '喜悦', '👌': '喜悦', '✌️': '喜悦', '🤞': '喜悦', '🤟': '喜悦', '🤘': '喜悦',
        '😢': '悲伤', '😭': '悲伤', '😞': '悲伤', '😔': '悲伤', '😟': '悲伤', '😕': '悲伤', '🙁': '悲伤', '☹️': '悲伤',
        '😤': '愤怒', '😠': '愤怒', '😡': '愤怒', '🤬': '愤怒',
        '😰': '焦虑', '😥': '焦虑', '😓': '焦虑', '😨': '焦虑',
        '😱': '恐惧', '😨': '恐惧', '😰': '恐惧',
        '🤢': '厌恶', '🤮': '厌恶',
        '😴': '无感', '🤔': '无感', '😐': '无感', '😑': '无感'
    }

    _SCORE_EMOTION_MAP = {
        "positive": [
            (['开心', '高兴', '快乐', '喜悦', '兴奋', '激动', '惊喜'], "喜悦"),
            (['感动', '温暖', '感激', '感谢'], "感动"),
            (['惊喜', '兴奋', '激动'], "兴奋"),
        ],
        "negative": [
            (['生气', '愤怒', '恼火', '烦躁', '不满'], "愤怒"),
            (['伤心', '难过', '悲伤', '痛苦', '流泪'], "悲伤"),
            (['失望', '遗憾', '沮丧'], "失望"),
            (['厌恶', '讨厌', '反感'], "厌恶"),
        ],
        "neutral": [
            (['担心', '焦虑', '紧张', '压力', '担忧'], "焦虑"),
            (['期待', '希望', '憧憬', '向往'], "期待"),
            (['麻烦', '压力', '负担', '无奈'], "无奈"),
            (['平静', '淡定', '从容'], "平静"),
        ],
    }

    def _lookup_emotion_by_words(self, text: str, word_groups: list, default: str) -> str:
        for words, emotion in word_groups:
            if any(w in text for w in words):
                return emotion
        return default

    def _get_emotion(self, text: str, positive_words: list, negative_words: list, score: float) -> str:
        """细粒度情感识别"""
        for pattern, emotion in self.sarcasm_patterns.items():
            if pattern in text:
                if any(w in text for w in ['好', '棒', '开心', '高兴', '喜欢']):
                    return "讽刺"
                if any(w in text for w in ['不生气', '没关系', '还好']):
                    return "愤怒"
                return emotion

        for word, emotion in self.internet_emotions.items():
            if word in text:
                return emotion

        for emoji, emotion in self.emoji_emotions.items():
            if emoji in text:
                return emotion

        if score > 0.7:
            bucket = "positive"
            default = "积极"
        elif score < 0.3:
            bucket = "negative"
            default = "消极"
        else:
            bucket = "neutral"
            default = "无感"

        return self._lookup_emotion_by_words(text, self._SCORE_EMOTION_MAP[bucket], default)


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
        except (requests.RequestException, ValueError, KeyError) as e:
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
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"LLM输出校验失败: {e}")
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
    """自定义模型策略（Phase 3 起面向 ModelBackend 抽象）。

    不再直接持有 sklearn 模型，而是通过 :class:`AutoBackendSelector` 选择
    底层 backend（bert / sklearn / snownlp），上层只负责缓存、SnowNLP
    融合与结果封装。降级链路由 backend 自身处理。
    """

    def __init__(self):
        # 延迟导入避免与 sentiment_backend 形成模块级循环依赖
        from ..sentiment_backend import AutoBackendSelector

        self._selector = AutoBackendSelector()
        self._backend = None  # 懒加载：首次 predict 时才 select
        self._snow_strategy: Optional[SnowNLPStrategy] = None

    @property
    def backend(self):
        """懒加载选中 backend，便于在测试中替换。"""
        if self._backend is None:
            self._backend = self._selector.select()
        return self._backend

    def _get_snow_strategy(self) -> "SnowNLPStrategy":
        if self._snow_strategy is None:
            self._snow_strategy = SnowNLPStrategy()
        return self._snow_strategy

    @staticmethod
    def _extract_model_keywords(text: str) -> list:
        try:
            s = SnowNLP(text)
            base = s.keywords(10)
            pos_set = {'好', '优秀', '棒', '赞', '满意', '喜欢', '高兴', '开心', '快乐', '幸福',
                       '美好', '精彩', '出色', '成功', '完美', 'yyds', '666', 'nb', '厉害', 'nice'}
            neg_set = {'差', '糟糕', '烂', '垃圾', '失望', '讨厌', '生气', '难过', '悲伤', '痛苦',
                       '不好', '失败', '错误', '崩溃', '绝望', '难受', '无语', '醉了', '吐了'}
            sentiment = [w for w in base if w in pos_set or w in neg_set]
            seen = set(sentiment)
            result = sentiment + [w for w in base if w not in seen]
            return result[:5]
        except (ValueError, AttributeError):
            try:
                return SnowNLP(text).keywords(5)
            except (ValueError, AttributeError):
                return []

    def _build_model_reasoning(
        self, label: str, score: float, emotion: Optional[str], backend_name: str
    ) -> str:
        from utils.sentiment import label_to_chinese

        parts = [f"基于{backend_name}后端预测"]
        parts.append(f"预测置信度: {score:.2f}")
        if label != "neutral" and score < 0.7:
            parts.append("模型置信度较低，结合SnowNLP分析进行调整")
        parts.append(f"预测为{label_to_chinese(label)}情感")
        if emotion:
            parts.append(f"细粒度情感: {emotion}")
        return "，".join(parts)

    def _finalize_single_result(
        self, text: str, label: str, score: float, processing_time: float,
        snow_strategy: "SnowNLPStrategy", backend_name: str,
    ) -> SentimentResult:
        keywords = self._extract_model_keywords(text)
        emotion = None
        try:
            emotion = snow_strategy.analyze(text).emotion
        except (ValueError, AttributeError):
            pass

        reasoning = self._build_model_reasoning(label, score, emotion, backend_name)

        try:
            from model.model_monitor import ModelMonitor
            ModelMonitor().log_prediction(text, label, score, processing_time)
        except (ImportError, AttributeError):
            pass

        # 中性且低置信度时，融合 SnowNLP 结果做二次判定
        if label == "neutral" and score < 0.7:
            snow_result = snow_strategy.analyze(text)
            if snow_result.label != "neutral":
                label = snow_result.label
                score = (score + snow_result.score) / 2
                reasoning += f"，结合SnowNLP分析: {snow_result.reasoning}"
                keywords = snow_result.keywords

        return SentimentResult(
            score=score, label=label, reasoning=reasoning,
            emotion=emotion, keywords=keywords, source=backend_name,
        )

    def _predict_with_backend(self, texts: list):
        """调用 backend.predict_batch，返回 [(label, score), ...]。"""
        return self.backend.predict_batch(texts)

    def analyze(self, text: str) -> SentimentResult:
        """执行情感分析，带缓存和错误降级处理。"""
        if not text or not text.strip():
            return SentimentResult(0.5, "neutral", reasoning="空文本", source="custom_model")

        backend_name = self.backend.name

        # 1. 检查缓存（按 backend 维度隔离）
        cached_result = get_from_cache(text, "custom_model", backend_name)
        if cached_result:
            return cached_result

        # 2. 调用 backend 预测
        try:
            predictions = self._predict_with_backend([text])
            if not predictions:
                raise RuntimeError("backend 返回空结果")
            label, score = predictions[0]
        except Exception as e:
            logger.error(f"backend({backend_name}) 分析失败，降级到SnowNLP: {e}")
            return self._get_snow_strategy().analyze(text)

        # 3. 封装结果（含 SnowNLP 融合与 model_monitor 记录）
        result = self._finalize_single_result(
            text, label, float(score), 0.0, self._get_snow_strategy(), backend_name
        )

        # 4. 写入缓存
        save_to_cache(text, "custom_model", result, backend_name)
        return result

    def analyze_batch(self, texts: list) -> list:
        """批量分析文本。"""
        if not texts:
            return []

        backend_name = self.backend.name

        # 1. 批量检查缓存
        results: list = [None] * len(texts)
        uncached_texts: list = []
        uncached_indices: list = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                results[i] = SentimentResult(
                    0.5, "neutral", reasoning="空文本", source="custom_model"
                )
                continue
            cached_result = get_from_cache(text, "custom_model", backend_name)
            if cached_result:
                results[i] = cached_result
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # 2. 批量预测未缓存的文本
        if uncached_texts:
            try:
                start_time = time.time()
                predictions = self._predict_with_backend(uncached_texts)
                per_item_time = (time.time() - start_time) / max(len(uncached_texts), 1)

                if len(predictions) != len(uncached_texts):
                    raise RuntimeError(
                        f"backend 返回长度不匹配: {len(predictions)} != {len(uncached_texts)}"
                    )

                snow = self._get_snow_strategy()
                for i, (index, text) in enumerate(zip(uncached_indices, uncached_texts)):
                    label, score = predictions[i]
                    result = self._finalize_single_result(
                        text, label, float(score), per_item_time, snow, backend_name
                    )
                    results[index] = result
                    save_to_cache(text, "custom_model", result, backend_name)
            except Exception as e:
                logger.error(f"批量分析失败，降级到SnowNLP: {e}")
                snow_strategy = self._get_snow_strategy()
                for index, text in zip(uncached_indices, uncached_texts):
                    results[index] = snow_strategy.analyze(text)

        return results

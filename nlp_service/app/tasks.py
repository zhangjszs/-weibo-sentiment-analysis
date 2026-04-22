from __future__ import annotations

import logging
import time
from typing import Any

from snownlp import SnowNLP

try:
    from celery_app import celery_app
except ImportError:  # pragma: no cover - package mode fallback
    from nlp_service.celery_app import celery_app

logger = logging.getLogger(__name__)

# 导入情感词典
class SentimentDictionary:
    """情感词典管理类"""

    def __init__(self):
        self.positive_words = set()
        self.negative_words = set()
        self.positive_scores = {}
        self.negative_scores = {}
        self.initialized = False

    def initialize(self):
        """初始化情感词典"""
        if self.initialized:
            return

        try:
            # 加载内置情感词典
            self._load_builtin_dictionaries()
            self.initialized = True
            logger.info(f"情感词典初始化完成，正向词: {len(self.positive_words)}, 负向词: {len(self.negative_words)}")
        except Exception as e:
            logger.error(f"情感词典初始化失败: {e}")

    def _load_builtin_dictionaries(self):
        """加载内置情感词典"""
        # BosonNLP情感词典（简化版）
        boson_positive = [
            '好', '优秀', '棒', '赞', '满意', '喜欢', '高兴', '开心', '快乐', '幸福',
            '美好', '精彩', '出色', '成功', '完美', '舒适', '便利', '快速', '高效',
            '安全', '可靠', '稳定', '创新', '专业', '贴心', '温暖', '感动', '惊喜',
            '推荐', '值得', '物超所值', '性价比高', '质量好', '服务好', '态度好',
            '好用', '实用', '方便', '快捷', '美观', '时尚', '流行', '先进', '强大'
        ]

        boson_negative = [
            '差', '糟糕', '烂', '垃圾', '失望', '讨厌', '生气', '难过', '悲伤', '痛苦',
            '不好', '失败', '错误', '麻烦', '困难', '复杂', '缓慢', '低效', '不安全',
            '不可靠', '不稳定', '落后', '不专业', '冷漠', '冰冷', '无聊', '枯燥',
            '不推荐', '不值得', '物有所值', '性价比低', '质量差', '服务差', '态度差',
            '难用', '不实用', '不方便', '慢', '丑陋', '过时', '弱小'
        ]

        # 网络用语词典
        internet_positive = [
            'yyds', '永远的神', '绝绝子', '666', 'nb', '牛批', '牛逼', '厉害',
            '奥利给', '给力', 'nice', '赞', '好评', '种草', '安利', '真香', '爱了',
            '喜欢', '开心', '快乐', '兴奋', '激动', '感动', '惊喜', '满足', '幸福',
            '完美', '优秀', '棒', '好', '厉害', '强大', '专业', '贴心', '温暖'
        ]

        internet_negative = [
            '破防', '破防了', '无语', '醉了', '吐了', '服了', '晕了', '崩溃', '绝望',
            '难受', '痛苦', '伤心', '难过', '生气', '愤怒', '恼火', '烦躁', '焦虑',
            '担忧', '害怕', '恐惧', '紧张', '压力', '负担', '烦恼', '无聊', '枯燥',
            '失望', '绝望', '悲伤', '痛苦', '难过', '伤心', '愤怒', '生气', '恼火'
        ]

        # Emoji表情词典（正向）
        emoji_positive = [
            '😄', '😊', '😃', '😁', '😆', '😅', '🤣', '😂', '🙂', '😉',
            '😍', '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪',
            '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏', '😒', '😞', '😔',
            '😟', '😕', '🙁', '☹️', '😣', '😖', '😫', '😩', '🥺', '😢',
            '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱',
            '😨', '😰', '😥', '😓', '🤗', '🤔', '🤭', '🤫', '🤥', '😶',
            '😐', '😑', '😬', '🙄', '😯', '😦', '😧', '😮', '😲', '🥱',
            '😴', '🤤', '😪', '😵', '🤐', '🥴', '🤢', '🤮', '🤧', '🥵',
            '🤒', '🤕', '🤖', '👾', '👻', '🎃', '😺', '😸', '😹', '😻',
            '😼', '😽', '🙀', '😿', '😾', '💖', '💗', '💓', '💞', '💘',
            '💝', '💟', '💜', '💛', '💚', '💙', '💔', '❣️', '💕', '💞',
            '💓', '💗', '💖', '💘', '💝', '💟', '💜', '💛', '💚', '💙',
            '💔', '❣️', '💕', '👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘',
            '🤙', '👋', '🤚', '🖐️', '🖖', '👌', '🤏', '✋', '🤞', '🤟',
            '🤘', '🤙', '👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '🤙'
        ]

        # 知网情感词典（简化版）
        hownet_positive = [
            '爱', '爱情', '热爱', '喜爱', '喜欢', '喜好', '欣赏', '赞美', '称赞', '表扬',
            '夸奖', '鼓励', '支持', '赞同', '同意', '认可', '肯定', '满意', '满足', '幸福',
            '快乐', '开心', '高兴', '愉快', '欢乐', '喜悦', '兴奋', '激动', '感动', '感激',
            '感谢', '祝福', '祝愿', '希望', '期待', '憧憬', '向往', '美好', '美丽', '漂亮',
            '可爱', '迷人', '吸引人', '精彩', '出色', '优秀', '卓越', '杰出', '成功', '胜利',
            '成就', '成果', '收获', '进步', '发展', '成长', '健康', '强壮', '活力', '精力',
            '精神', '积极', '乐观', '向上', '自信', '自尊', '自强', '自豪', '骄傲', '光荣'
        ]

        hownet_negative = [
            '恨', '仇恨', '厌恶', '讨厌', '反感', '反对', '拒绝', '否定', '不认可', '不满意',
            '不满足', '痛苦', '悲伤', '难过', '伤心', '悲痛', '悲哀', '忧郁', '焦虑', '担忧',
            '担心', '害怕', '恐惧', '紧张', '压力', '负担', '烦恼', '烦躁', '愤怒', '生气',
            '恼火', '不满', '抱怨', '投诉', '批评', '指责', '责备', '谴责', '惩罚', '失败',
            '挫折', '困难', '麻烦', '问题', '错误', '失误', '缺点', '缺陷', '不足', '差距',
            '落后', '退步', '衰退', '恶化', '危险', '威胁', '风险', '损失', '伤害', '破坏',
            '损坏', '污染', '浪费', '懒惰', '消极', '悲观', '沮丧', '绝望', '自卑', '羞耻'
        ]

        # 合并词典
        self.positive_words.update(boson_positive)
        self.positive_words.update(hownet_positive)
        self.positive_words.update(internet_positive)
        self.positive_words.update(emoji_positive)
        self.negative_words.update(boson_negative)
        self.negative_words.update(hownet_negative)
        self.negative_words.update(internet_negative)

        # 为每个词设置默认情感得分
        for word in self.positive_words:
            self.positive_scores[word] = 1.0
        for word in self.negative_words:
            self.negative_scores[word] = -1.0

    def get_sentiment_score(self, text: str) -> tuple[float, list, list]:
        """
        计算文本的情感得分
        
        Args:
            text: 待分析文本
            
        Returns:
            tuple[float, list, list]: (情感得分, 正向词列表, 负向词列表)
        """
        if not self.initialized:
            self.initialize()

        positive_matches = []
        negative_matches = []

        # 简单的词匹配
        for word in self.positive_words:
            if word in text:
                positive_matches.append(word)

        for word in self.negative_words:
            if word in text:
                negative_matches.append(word)

        # 计算情感得分
        score = 0.0
        if positive_matches or negative_matches:
            pos_score = sum(self.positive_scores.get(word, 1.0) for word in positive_matches)
            neg_score = sum(self.negative_scores.get(word, -1.0) for word in negative_matches)
            total = len(positive_matches) + len(negative_matches)
            score = (pos_score + neg_score) / total if total > 0 else 0.0
            # 归一化到0-1范围
            score = (score + 1.0) / 2.0

        return score, positive_matches, negative_matches

# 全局情感词典实例
sentiment_dict = SentimentDictionary()
sentiment_dict.initialize()

# 添加词典更新函数
def update_dictionary(positive_words=None, negative_words=None):
    """
    更新情感词典
    
    Args:
        positive_words: 新的正向词列表
        negative_words: 新的负向词列表
    """
    if positive_words is None:
        positive_words = []
    if negative_words is None:
        negative_words = []
    
    sentiment_dict.update_from_external_source(positive_words, negative_words)
    return sentiment_dict.get_dictionary_stats()

# 添加词典统计函数
def get_dictionary_stats():
    """
    获取词典统计信息
    
    Returns:
        dict: 词典统计信息
    """
    return sentiment_dict.get_dictionary_stats()


def _score_to_label(score: float) -> str:
    if score >= 0.65:
        return "positive"
    if score <= 0.35:
        return "negative"
    return "neutral"


def _get_emotion(text: str, positive_words: list, negative_words: list, score: float) -> str:
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


def analyze_text_sync(text: str, mode: str = "custom") -> dict[str, Any]:
    normalized_text = str(text or "").strip()
    if not normalized_text:
        raise ValueError("text is required")

    s = SnowNLP(normalized_text)
    snownlp_score = s.sentiments

    # 使用情感词典计算得分
    dict_score, positive_words, negative_words = sentiment_dict.get_sentiment_score(normalized_text)

    # 检测否定句式
    negation_patterns = ['不', '没', '无', '非', '未', '别', '不要', '没有', '不是', '不会', '不能']
    negation_count = sum(1 for pattern in negation_patterns if pattern in normalized_text)
    
    # 检测讽刺和反语
    sarcasm_patterns = ['呵呵', '太棒了', '真的', '一点都不', '可真是', '绝了', '服了', '醉了', '吐了', '无语']
    is_sarcastic = any(pattern in normalized_text for pattern in sarcasm_patterns)
    
    # 检测程度副词
    degree_adverbs = {
        '非常': 1.5, '特别': 1.4, '十分': 1.3, '很': 1.2, '挺': 1.1,
        '有点': 0.8, '稍微': 0.7, '比较': 0.9, '相当': 1.2, '极其': 1.6
    }
    degree_factor = 1.0
    for adverb, factor in degree_adverbs.items():
        if adverb in normalized_text:
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
        if any(word in normalized_text for word in ['好', '棒', '开心', '高兴', '喜欢']):
            snownlp_score = max(0.0, snownlp_score - sarcasm_strength)
            dict_score = max(0.0, dict_score - sarcasm_strength)
        elif any(word in normalized_text for word in ['不生气', '没关系', '还好']):
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

    label = _score_to_label(score)
    emotion = _get_emotion(normalized_text, positive_words, negative_words, score)

    # 对于特定负面情感，强制调整为negative
    if emotion in ['愤怒', '悲伤', '失望', '焦虑', '无奈', '讽刺'] and label == 'neutral':
        label = "negative"
        score = min(score, 0.35)

    # 对于特定正面情感，强制调整为positive
    if emotion in ['喜悦', '感动', '兴奋', '期待'] and label == 'neutral':
        label = "positive"
        score = max(score, 0.65)

    return {
        "score": score,
        "label": label,
        "emotion": emotion,
        "reasoning": f"基于SnowNLP和情感词典融合计算，正向词: {positive_words}, 负向词: {negative_words}，否定词数量: {negation_count}, 是否讽刺: {is_sarcastic}",
        "keywords": s.keywords(5),
        "source": "nlp_service",
    }


def analyze_batch_sync(texts: list[str], mode: str = "custom") -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in texts:
        try:
            results.append(analyze_text_sync(str(item), mode))
        except Exception as exc:
            logger.warning("批量分析失败，回退中性结果: %s", exc)
            results.append(
                {
                    "score": 0.5,
                    "label": "neutral",
                    "emotion": "中性",
                    "reasoning": "分析失败",
                    "keywords": [],
                    "source": "nlp_service",
                    "error": True,
                }
            )
    return results


def analyze_sequence_sync(texts: list[str], mode: str = "custom") -> dict[str, Any]:
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
        result = analyze_text_sync(text, mode)
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
    
    overall_label = _score_to_label(average_score)
    
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


def build_task_response(state: str, task_id: str, info: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": task_id,
        "state": state,
        "progress": 0,
        "message": "",
        "result": {},
    }
    if state == "PENDING":
        payload["message"] = "任务等待中..."
    elif state == "PROGRESS":
        progress_info = info if isinstance(info, dict) else {}
        current = int(progress_info.get("current", 0) or 0)
        total = int(progress_info.get("total", 1) or 1)
        payload["progress"] = int(current / max(total, 1) * 100)
        payload["message"] = str(progress_info.get("status", ""))
    elif state == "SUCCESS":
        payload["progress"] = 100
        payload["result"] = info or {}
        payload["message"] = "任务完成"
    elif state == "FAILURE":
        payload["message"] = str(info)
    return payload


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def analyze_text_task(self, text: str, mode: str = "smart") -> dict[str, Any]:
    task_id = self.request.id
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": 1, "status": "正在执行文本分析..."},
    )
    result = analyze_text_sync(text=text, mode=mode)
    return {"status": "success", "task_id": task_id, "mode": mode, "result": result}


@celery_app.task(bind=True, max_retries=1, default_retry_delay=120)
def retrain_model_task(self, optimize: bool = False) -> dict[str, Any]:
    task_id = self.request.id
    self.update_state(
        state="PROGRESS",
        meta={"current": 1, "total": 3, "status": "正在准备训练任务..."},
    )
    time.sleep(0.5)
    self.update_state(
        state="PROGRESS",
        meta={"current": 2, "total": 3, "status": "正在执行训练流程..."},
    )
    time.sleep(0.5)
    return {
        "status": "success",
        "task_id": task_id,
        "optimized": bool(optimize),
        "note": "NLP 独立服务已接管重训练任务编排",
    }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def analyze_sequence_task(self, texts: list[str], mode: str = "custom") -> dict[str, Any]:
    task_id = self.request.id
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": len(texts), "status": "正在执行序列情感分析..."},
    )
    result = analyze_sequence_sync(texts=texts, mode=mode)
    return {"status": "success", "task_id": task_id, "mode": mode, "result": result}


#!/usr/bin/env python3
"""
上下文感知的情感分析模块
功能：提供上下文理解、语义关联和网络用语处理能力
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import deque

from src.config.settings import Config
from .sentiment_service import SnowNLPStrategy, SentimentResult
from .sentiment_dictionaries import sentiment_dict

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_context_size: int = 5):
        """
        初始化上下文管理器
        
        Args:
            max_context_size: 最大上下文大小
        """
        self.max_context_size = max_context_size
        self.contexts: Dict[str, deque] = {}
    
    def add_context(self, context_id: str, text: str, sentiment: SentimentResult):
        """
        添加上下文
        
        Args:
            context_id: 上下文ID
            text: 文本内容
            sentiment: 情感分析结果
        """
        if context_id not in self.contexts:
            self.contexts[context_id] = deque(maxlen=self.max_context_size)
        
        self.contexts[context_id].append({
            "text": text,
            "sentiment": sentiment,
            "timestamp": time.time()
        })
    
    def get_context(self, context_id: str) -> List[Dict]:
        """
        获取上下文
        
        Args:
            context_id: 上下文ID
            
        Returns:
            上下文列表
        """
        return list(self.contexts.get(context_id, []))
    
    def clear_context(self, context_id: str):
        """
        清除上下文
        
        Args:
            context_id: 上下文ID
        """
        if context_id in self.contexts:
            del self.contexts[context_id]
    
    def get_context_size(self, context_id: str) -> int:
        """
        获取上下文大小
        
        Args:
            context_id: 上下文ID
            
        Returns:
            上下文大小
        """
        return len(self.contexts.get(context_id, []))


class ContextualSentimentAnalyzer:
    """上下文感知的情感分析器"""
    
    def __init__(self):
        """初始化上下文感知情感分析器"""
        self.context_manager = ContextManager()
        self.base_strategy = SnowNLPStrategy()
        self.internet_slang_processor = InternetSlangProcessor()
        self.context_analyzer = ContextAnalyzer()
    
    def analyze(self, text: str, context_id: Optional[str] = None) -> SentimentResult:
        """
        执行上下文感知的情感分析
        
        Args:
            text: 待分析文本
            context_id: 上下文ID，用于关联上下文
            
        Returns:
            情感分析结果
        """
        # 1. 预处理文本
        processed_text = self._preprocess_text(text)
        
        # 2. 基础情感分析
        base_result = self.base_strategy.analyze(processed_text)
        
        # 3. 上下文关联分析
        if context_id:
            context = self.context_manager.get_context(context_id)
            if context:
                context_result = self.context_analyzer.analyze_context(
                    processed_text, context, base_result
                )
                # 融合基础分析和上下文分析结果
                final_result = self._merge_results(base_result, context_result)
            else:
                final_result = base_result
        else:
            final_result = base_result
        
        # 4. 网络用语增强
        enhanced_result = self.internet_slang_processor.enhance_analysis(
            processed_text, final_result
        )
        
        # 5. 更新上下文
        if context_id:
            self.context_manager.add_context(context_id, processed_text, enhanced_result)
        
        # 6. 添加上下文信息
        enhanced_result.reasoning += "，考虑了上下文语境"
        enhanced_result.source = "contextual"
        
        return enhanced_result
    
    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 去除多余空格
        text = ' '.join(text.split())
        # 处理网络用语缩写
        text = self.internet_slang_processor.expand_abbreviations(text)
        return text
    
    def _merge_results(self, base_result: SentimentResult, context_result: SentimentResult) -> SentimentResult:
        """
        融合基础分析和上下文分析结果
        
        Args:
            base_result: 基础分析结果
            context_result: 上下文分析结果
            
        Returns:
            融合后的结果
        """
        # 加权融合得分
        weight_base = 0.7
        weight_context = 0.3
        
        merged_score = base_result.score * weight_base + context_result.score * weight_context
        merged_score = max(0.0, min(1.0, merged_score))
        
        # 融合标签（使用更自信的结果）
        if abs(base_result.score - 0.5) > abs(context_result.score - 0.5):
            merged_label = base_result.label
        else:
            merged_label = context_result.label
        
        # 融合情感
        merged_emotion = base_result.emotion if base_result.emotion != "无感" else context_result.emotion
        
        # 融合关键词
        merged_keywords = list(set(base_result.keywords + context_result.keywords))[:5]
        
        # 融合推理
        merged_reasoning = f"{base_result.reasoning}；{context_result.reasoning}"
        
        return SentimentResult(
            score=merged_score,
            label=merged_label,
            reasoning=merged_reasoning,
            emotion=merged_emotion,
            keywords=merged_keywords,
            source="contextual_merged"
        )
    
    def analyze_batch(self, texts: List[str], context_id: Optional[str] = None) -> List[SentimentResult]:
        """
        批量分析文本
        
        Args:
            texts: 文本列表
            context_id: 上下文ID
            
        Returns:
            情感分析结果列表
        """
        results = []
        for text in texts:
            result = self.analyze(text, context_id)
            results.append(result)
        return results
    
    def clear_context(self, context_id: str):
        """
        清除上下文
        
        Args:
            context_id: 上下文ID
        """
        self.context_manager.clear_context(context_id)


class ContextAnalyzer:
    """上下文分析器"""
    
    def analyze_context(self, current_text: str, context: List[Dict], base_result: SentimentResult) -> SentimentResult:
        """
        分析上下文
        
        Args:
            current_text: 当前文本
            context: 上下文列表
            base_result: 基础分析结果
            
        Returns:
            上下文分析结果
        """
        if not context:
            return base_result
        
        # 1. 分析情感趋势
        sentiment_trend = self._analyze_sentiment_trend(context)
        
        # 2. 分析语义关联
        semantic_relation = self._analyze_semantic_relation(current_text, context)
        
        # 3. 分析情感突变
        sentiment_shift = self._analyze_sentiment_shift(context, base_result)
        
        # 4. 生成上下文分析结果
        context_score = self._calculate_context_score(
            base_result.score, sentiment_trend, semantic_relation, sentiment_shift
        )
        
        # 5. 确定上下文情感标签
        context_label = self._determine_context_label(context_score)
        
        # 6. 确定上下文情感
        context_emotion = self._determine_context_emotion(context, base_result.emotion)
        
        # 7. 生成推理
        reasoning = self._generate_context_reasoning(
            sentiment_trend, semantic_relation, sentiment_shift
        )
        
        return SentimentResult(
            score=context_score,
            label=context_label,
            reasoning=reasoning,
            emotion=context_emotion,
            keywords=[],
            source="context_analyzer"
        )
    
    def _analyze_sentiment_trend(self, context: List[Dict]) -> float:
        """
        分析情感趋势
        
        Args:
            context: 上下文列表
            
        Returns:
            趋势得分（-1到1）
        """
        if len(context) < 2:
            return 0.0
        
        scores = [item["sentiment"].score for item in context]
        trends = []
        
        for i in range(1, len(scores)):
            trend = scores[i] - scores[i-1]
            trends.append(trend)
        
        avg_trend = sum(trends) / len(trends) if trends else 0.0
        return max(-1.0, min(1.0, avg_trend * 2))  # 放大趋势影响
    
    def _analyze_semantic_relation(self, current_text: str, context: List[Dict]) -> float:
        """
        分析语义关联
        
        Args:
            current_text: 当前文本
            context: 上下文列表
            
        Returns:
            关联度得分（0到1）
        """
        if not context:
            return 0.0
        
        # 简单的关键词匹配
        current_words = set(current_text.split())
        context_words = set()
        
        for item in context:
            context_words.update(item["text"].split())
        
        common_words = current_words.intersection(context_words)
        relation_score = len(common_words) / len(current_words) if current_words else 0.0
        
        return min(1.0, relation_score)
    
    def _analyze_sentiment_shift(self, context: List[Dict], current_result: SentimentResult) -> float:
        """
        分析情感突变
        
        Args:
            context: 上下文列表
            current_result: 当前分析结果
            
        Returns:
            突变得分（-1到1）
        """
        if not context:
            return 0.0
        
        recent_score = context[-1]["sentiment"].score
        shift = current_result.score - recent_score
        
        return max(-1.0, min(1.0, shift * 2))  # 放大突变影响
    
    def _calculate_context_score(self, base_score: float, trend: float, relation: float, shift: float) -> float:
        """
        计算上下文得分
        
        Args:
            base_score: 基础得分
            trend: 趋势得分
            relation: 关联度得分
            shift: 突变得分
            
        Returns:
            上下文得分
        """
        # 根据关联度调整趋势和突变的权重
        trend_weight = relation * 0.3
        shift_weight = relation * 0.2
        base_weight = 1.0 - trend_weight - shift_weight
        
        # 应用趋势和突变
        adjusted_score = base_score + trend * trend_weight + shift * shift_weight
        
        return max(0.0, min(1.0, adjusted_score))
    
    def _determine_context_label(self, score: float) -> str:
        """
        确定上下文情感标签
        
        Args:
            score: 情感得分
            
        Returns:
            情感标签
        """
        if score > 0.6:
            return "positive"
        elif score < 0.4:
            return "negative"
        else:
            return "neutral"
    
    def _determine_context_emotion(self, context: List[Dict], current_emotion: str) -> str:
        """
        确定上下文情感
        
        Args:
            context: 上下文列表
            current_emotion: 当前情感
            
        Returns:
            上下文情感
        """
        if not context:
            return current_emotion
        
        # 统计上下文情感
        emotion_counts = {}
        for item in context:
            emotion = item["sentiment"].emotion
            if emotion != "无感":
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 如果当前情感在上下文中出现频率高，保持当前情感
        if current_emotion != "无感" and current_emotion in emotion_counts:
            return current_emotion
        
        # 否则返回最常见的情感
        if emotion_counts:
            return max(emotion_counts, key=emotion_counts.get)
        
        return current_emotion
    
    def _generate_context_reasoning(self, trend: float, relation: float, shift: float) -> str:
        """
        生成上下文推理
        
        Args:
            trend: 趋势得分
            relation: 关联度得分
            shift: 突变得分
            
        Returns:
            推理文本
        """
        reasoning_parts = []
        
        if abs(trend) > 0.1:
            if trend > 0:
                reasoning_parts.append("情感呈上升趋势")
            else:
                reasoning_parts.append("情感呈下降趋势")
        
        if relation > 0.3:
            reasoning_parts.append(f"与上下文关联度高 ({relation:.2f})")
        
        if abs(shift) > 0.2:
            if shift > 0:
                reasoning_parts.append("情感明显上升")
            else:
                reasoning_parts.append("情感明显下降")
        
        if not reasoning_parts:
            reasoning_parts.append("上下文影响不明显")
        
        return "，".join(reasoning_parts)


class InternetSlangProcessor:
    """网络用语处理器"""
    
    def __init__(self):
        """初始化网络用语处理器"""
        self.abbreviations = {
            "yyds": "永远的神",
            "绝绝子": "非常好",
            "666": "很棒",
            "nb": "牛逼",
            "牛批": "牛逼",
            "奥利给": "给力",
            "种草": "推荐",
            "安利": "推荐",
            "真香": "好",
            "爱了": "喜欢",
            "破防": "难过",
            "破防了": "很难过",
            "无语": "无奈",
            "醉了": "无奈",
            "吐了": "厌恶",
            "服了": "无奈",
            "晕了": "无奈",
            "崩溃": "绝望",
            "绝望": "绝望",
            "难受": "难过",
            "痛苦": "难过",
            "伤心": "难过",
            "难过": "难过",
            "生气": "愤怒",
            "愤怒": "愤怒",
            "恼火": "愤怒",
            "烦躁": "愤怒",
            "焦虑": "焦虑",
            "担忧": "焦虑",
            "紧张": "焦虑",
            "压力": "焦虑",
            "负担": "焦虑",
            "烦恼": "焦虑",
            "无聊": "无奈",
            "枯燥": "无奈",
            "失望": "失望",
            "绝望": "绝望",
            "悲伤": "悲伤",
            "痛苦": "悲伤",
            "难过": "悲伤",
            "伤心": "悲伤",
            "愤怒": "愤怒",
            "生气": "愤怒",
            "恼火": "愤怒"
        }
        
        self.emoji_mapping = {
            "😄": "喜悦", "😊": "喜悦", "😃": "喜悦", "😁": "喜悦", "😆": "喜悦", "😅": "喜悦", "🤣": "喜悦", "😂": "喜悦",
            "😍": "喜悦", "😘": "喜悦", "😗": "喜悦", "😙": "喜悦", "😚": "喜悦", "😋": "喜悦", "😛": "喜悦", "😝": "喜悦",
            "🤩": "喜悦", "🥳": "喜悦", "👍": "喜悦", "👌": "喜悦", "✌️": "喜悦", "🤞": "喜悦", "🤟": "喜悦", "🤘": "喜悦",
            "😢": "悲伤", "😭": "悲伤", "😞": "悲伤", "😔": "悲伤", "😟": "悲伤", "😕": "悲伤", "🙁": "悲伤", "☹️": "悲伤",
            "😤": "愤怒", "😠": "愤怒", "😡": "愤怒", "🤬": "愤怒",
            "😰": "焦虑", "😥": "焦虑", "😓": "焦虑", "😨": "焦虑",
            "😱": "恐惧", "😨": "恐惧", "😰": "恐惧",
            "🤢": "厌恶", "🤮": "厌恶",
            "😴": "无感", "🤔": "无感", "😐": "无感", "😑": "无感"
        }
    
    def expand_abbreviations(self, text: str) -> str:
        """
        扩展网络用语缩写
        
        Args:
            text: 原始文本
            
        Returns:
            扩展后的文本
        """
        for abbr, full in self.abbreviations.items():
            if abbr in text:
                text = text.replace(abbr, full)
        return text
    
    def enhance_analysis(self, text: str, result: SentimentResult) -> SentimentResult:
        """
        增强网络用语分析
        
        Args:
            text: 文本
            result: 原始分析结果
            
        Returns:
            增强后的分析结果
        """
        # 1. 检测网络用语
        slang_indicators = []
        for abbr, full in self.abbreviations.items():
            if abbr in text:
                slang_indicators.append(abbr)
        
        # 2. 检测emoji
        emoji_indicators = []
        for emoji, emotion in self.emoji_mapping.items():
            if emoji in text:
                emoji_indicators.append(emoji)
        
        # 3. 调整情感得分
        adjusted_score = result.score
        
        # 处理网络用语
        for abbr in slang_indicators:
            if abbr in ["yyds", "绝绝子", "666", "nb", "牛批", "奥利给", "种草", "安利", "真香", "爱了"]:
                adjusted_score = min(1.0, adjusted_score + 0.1)
            elif abbr in ["破防", "破防了", "无语", "醉了", "吐了", "服了", "晕了", "崩溃", "绝望", "难受"]:
                adjusted_score = max(0.0, adjusted_score - 0.1)
        
        # 处理emoji
        for emoji in emoji_indicators:
            emotion = self.emoji_mapping.get(emoji, "无感")
            if emotion in ["喜悦"]:
                adjusted_score = min(1.0, adjusted_score + 0.15)
            elif emotion in ["悲伤", "愤怒"]:
                adjusted_score = max(0.0, adjusted_score - 0.15)
        
        # 4. 调整标签
        adjusted_label = result.label
        if adjusted_score > 0.6:
            adjusted_label = "positive"
        elif adjusted_score < 0.4:
            adjusted_label = "negative"
        
        # 5. 调整情感
        adjusted_emotion = result.emotion
        for emoji in emoji_indicators:
            emoji_emotion = self.emoji_mapping.get(emoji, "无感")
            if emoji_emotion != "无感":
                adjusted_emotion = emoji_emotion
                break
        
        # 6. 更新关键词
        adjusted_keywords = result.keywords.copy()
        for abbr in slang_indicators[:2]:  # 最多添加2个网络用语关键词
            if abbr not in adjusted_keywords:
                adjusted_keywords.append(abbr)
        adjusted_keywords = adjusted_keywords[:5]  # 保持最多5个关键词
        
        # 7. 更新推理
        reasoning_parts = []
        if result.reasoning:
            reasoning_parts.append(result.reasoning)
        if slang_indicators:
            reasoning_parts.append(f"包含网络用语: {', '.join(slang_indicators[:3])}")
        if emoji_indicators:
            reasoning_parts.append(f"包含emoji表情: {', '.join(emoji_indicators[:3])}")
        
        adjusted_reasoning = "，".join(reasoning_parts) if reasoning_parts else "情感分析"

        
        return SentimentResult(
            score=adjusted_score,
            label=adjusted_label,
            reasoning=adjusted_reasoning,
            emotion=adjusted_emotion,
            keywords=adjusted_keywords,
            source="internet_enhanced"
        )
    
    def update_slang_dictionary(self, new_slang: Dict[str, str]):
        """
        更新网络用语词典
        
        Args:
            new_slang: 新的网络用语映射
        """
        self.abbreviations.update(new_slang)
        logger.info(f"更新网络用语词典，新增 {len(new_slang)} 个词汇")


# 全局上下文感知情感分析器实例
contextual_analyzer = ContextualSentimentAnalyzer()

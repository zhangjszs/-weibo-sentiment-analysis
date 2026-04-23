"""
社交媒体文本预处理模块
功能：处理社交媒体特有特征，如表情符号、话题标签、用户提及等
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

import emoji
import jieba
from sklearn.base import BaseEstimator, TransformerMixin


class SocialMediaPreprocessor(BaseEstimator, TransformerMixin):
    """社交媒体文本预处理器"""

    def __init__(self, use_emoji_features: bool = True, use_hashtag_features: bool = True):
        self.use_emoji_features = use_emoji_features
        self.use_hashtag_features = use_hashtag_features
        self.emoji_sentiment_map = self._build_emoji_sentiment_map()

    def _build_emoji_sentiment_map(self) -> Dict[str, float]:
        """构建表情符号情感映射"""
        # 简化的表情符号情感字典
        return {
            '😊': 0.8, '😂': 0.7, '❤️': 0.9, '👍': 0.8, '🎉': 0.85,
            '😢': -0.7, '😡': -0.8, '👎': -0.7, '😞': -0.6, '😓': -0.4,
            '😐': 0.0, '😕': -0.2, '🤔': 0.0, '🙄': -0.3, '😏': 0.1
        }

    def _extract_emojis(self, text: str) -> List[str]:
        """提取文本中的表情符号"""
        return [char for char in text if char in emoji.EMOJI_DATA]

    def _extract_hashtags(self, text: str) -> List[str]:
        """提取话题标签"""
        return re.findall(r'#([^#\s]+)#', text)

    def _extract_mentions(self, text: str) -> List[str]:
        """提取用户提及"""
        return re.findall(r'@([^@\s]+)', text)

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除URL
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # 移除话题标签和用户提及（保留内容）
        text = re.sub(r'#([^#\s]+)#', r'\1', text)
        text = re.sub(r'@([^@\s]+)', '', text)
        # 移除特殊字符，保留中文、英文和数字
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _get_emoji_sentiment(self, text: str) -> float:
        """计算表情符号情感得分"""
        emojis = self._extract_emojis(text)
        if not emojis:
            return 0.0
        
        sentiments = []
        for e in emojis:
            if e in self.emoji_sentiment_map:
                sentiments.append(self.emoji_sentiment_map[e])
        
        return sum(sentiments) / len(sentiments) if sentiments else 0.0

    def transform(self, X, y=None):
        """转换文本数据"""
        transformed = []
        for text in X:
            if not isinstance(text, str):
                text = str(text)
            
            # 基础清理
            cleaned = self._clean_text(text)
            
            # 分词
            words = jieba.lcut(cleaned)
            processed_text = ' '.join(words)
            
            transformed.append(processed_text)
        return transformed

    def fit(self, X, y=None):
        """拟合（无操作）"""
        return self

    def get_social_features(self, text: str) -> Dict[str, any]:
        """获取社交媒体特有特征"""
        if not isinstance(text, str):
            text = str(text)
        
        features = {
            'emoji_count': len(self._extract_emojis(text)),
            'hashtag_count': len(self._extract_hashtags(text)),
            'mention_count': len(self._extract_mentions(text)),
            'emoji_sentiment': self._get_emoji_sentiment(text),
            'text_length': len(text),
            'word_count': len(jieba.lcut(text))
        }
        
        return features


def preprocess_social_media_text(text: str) -> Tuple[str, Dict[str, any]]:
    """预处理社交媒体文本
    
    Args:
        text: 原始文本
    
    Returns:
        预处理后的文本和特征字典
    """
    preprocessor = SocialMediaPreprocessor()
    cleaned_text = preprocessor.transform([text])[0]
    features = preprocessor.get_social_features(text)
    return cleaned_text, features

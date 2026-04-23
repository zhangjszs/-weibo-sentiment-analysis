"""
社交媒体文本增强模块
功能：增加数据增强和社交媒体特有特征处理
"""

from __future__ import annotations

import random
import re
from typing import Dict, List, Tuple

import jieba


class SocialMediaAugmenter:
    """社交媒体文本增强器"""

    def __init__(self):
        self.slang_map = self._build_slang_map()
        self.emoji_variants = self._build_emoji_variants()
        self.negation_words = ["不", "没", "无", "非", "未", "别", "不要", "没有"]

    def _build_slang_map(self) -> Dict[str, List[str]]:
        """构建网络流行语映射"""
        return {
            "点赞": ["赞", "👍", "支持", "like"],
            "评论": ["评", "留言", "回复", "comment"],
            "转发": ["转", "分享", "扩散", "share"],
            "关注": ["粉", "follow", "留意"],
            "热门": ["火", "爆款", "热搜", "trending"],
            "很棒": ["厉害", "牛", "666", "awesome", "牛逼"],
            "很差": ["垃圾", "辣鸡", "不行", "糟糕", "terrible"],
            "开心": ["高兴", "快乐", "喜悦", "😊", "happy"],
            "难过": ["伤心", "悲伤", "难过", "😢", "sad"],
        }

    def _build_emoji_variants(self) -> Dict[str, List[str]]:
        """构建表情符号变体"""
        return {
            "😊": ["😀", "😃", "😄", "😁"],
            "😂": ["🤣", "😆", "😅"],
            "❤️": ["💓", "💕", "💖", "💗"],
            "👍": ["👌", "✅", "✔️"],
            "😢": ["😭", "😿", "😥"],
            "😡": ["😠", "🤬", "💢"],
        }

    def synonym_replacement(self, text: str, ratio: float = 0.2) -> str:
        """同义词替换"""
        words = jieba.lcut(text)
        new_words = []
        
        for word in words:
            replaced = False
            for key, synonyms in self.slang_map.items():
                if word == key and random.random() < ratio:
                    new_words.append(random.choice(synonyms))
                    replaced = True
                    break
            if not replaced:
                new_words.append(word)
        
        return ''.join(new_words)

    def emoji_variation(self, text: str) -> str:
        """表情符号变体替换"""
        for emoji_char, variants in self.emoji_variants.items():
            if emoji_char in text and random.random() < 0.5:
                text = text.replace(emoji_char, random.choice(variants))
        return text

    def random_insertion(self, text: str, ratio: float = 0.1) -> str:
        """随机插入情感词"""
        words = jieba.lcut(text)
        insert_count = max(1, int(len(words) * ratio))
        
        for _ in range(insert_count):
            position = random.randint(0, len(words))
            # 随机选择一个情感词
            emotion_words = ["非常", "特别", "超级", "真的", "很", "太", "十分"]
            words.insert(position, random.choice(emotion_words))
        
        return ''.join(words)

    def random_deletion(self, text: str, ratio: float = 0.1) -> str:
        """随机删除词"""
        words = jieba.lcut(text)
        if len(words) <= 2:
            return text
        
        keep_count = max(1, int(len(words) * (1 - ratio)))
        kept_words = random.sample(words, keep_count)
        return ''.join(kept_words)

    def negation_augmentation(self, text: str) -> str:
        """否定词增强"""
        words = jieba.lcut(text)
        if len(words) < 2:
            return text
        
        # 随机选择一个位置插入否定词
        if random.random() < 0.3:
            position = random.randint(0, len(words) - 1)
            negation = random.choice(self.negation_words)
            words.insert(position, negation)
            return ''.join(words)
        return text

    def augment(self, text: str, num_augmentations: int = 3) -> List[str]:
        """执行数据增强
        
        Args:
            text: 原始文本
            num_augmentations: 增强数量
            
        Returns:
            list: 增强后的文本列表
        """
        augmentations = []
        
        # 应用不同的增强方法
        methods = [
            self.synonym_replacement,
            self.emoji_variation,
            self.random_insertion,
            self.random_deletion,
            self.negation_augmentation,
        ]
        
        for _ in range(num_augmentations):
            augmented = text
            # 随机选择2-3种方法
            selected_methods = random.sample(methods, random.randint(2, 3))
            for method in selected_methods:
                augmented = method(augmented)
            augmentations.append(augmented)
        
        return augmentations

    def process_social_media_text(self, text: str) -> str:
        """处理社交媒体文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 处理后的文本
        """
        # 处理话题标签
        text = re.sub(r'#([^#\s]+)#', r'\1', text)
        
        # 处理用户提及
        text = re.sub(r'@([^@\s]+)', '', text)
        
        # 处理URL
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # 处理重复字符（如"好好好" -> "好"）
        text = re.sub(r'(.)\1{2,}', r'\1', text)
        
        # 处理表情符号
        text = self.emoji_variation(text)
        
        return text.strip()

    def extract_social_features(self, text: str) -> Dict[str, any]:
        """提取社交媒体特征
        
        Args:
            text: 原始文本
            
        Returns:
            dict: 特征字典
        """
        features = {
            'hashtag_count': len(re.findall(r'#([^#\s]+)#', text)),
            'mention_count': len(re.findall(r'@([^@\s]+)', text)),
            'url_count': len(re.findall(r'http\S+|www\S+|https\S+', text)),
            'emoji_count': len([c for c in text if c in '😊😂❤️👍😢😡🤣😆😅💓💕💖💗👌✅✔️😭😿😥😠🤬💢']),
            'text_length': len(text),
            'word_count': len(jieba.lcut(text)),
        }
        
        # 检查是否包含特定社交媒体词汇
        social_terms = ['转发', '评论', '点赞', '关注', '热门', '热搜']
        for term in social_terms:
            features[f'has_{term}'] = term in text
        
        return features


def augment_data(texts: List[str], labels: List[str], num_augmentations: int = 2) -> Tuple[List[str], List[str]]:
    """增强数据集
    
    Args:
        texts: 文本列表
        labels: 标签列表
        num_augmentations: 每个文本的增强数量
        
    Returns:
        tuple: (增强后的文本列表, 增强后的标签列表)
    """
    augmenter = SocialMediaAugmenter()
    augmented_texts = []
    augmented_labels = []
    
    for text, label in zip(texts, labels):
        # 添加原始样本
        augmented_texts.append(text)
        augmented_labels.append(label)
        
        # 添加增强样本
        augmentations = augmenter.augment(text, num_augmentations)
        for aug_text in augmentations:
            augmented_texts.append(aug_text)
            augmented_labels.append(label)
    
    return augmented_texts, augmented_labels

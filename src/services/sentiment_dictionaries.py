#!/usr/bin/env python3
"""
情感词典模块
功能：管理和加载情感词典，提供情感词匹配和得分计算
"""

import os
import time
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class SentimentDictionary:
    """情感词典管理类"""

    def __init__(self):
        self.positive_words = set()
        self.negative_words = set()
        self.positive_scores = {}
        self.negative_scores = {}
        self.initialized = False
        self.last_updated = None

    def initialize(self):
        """初始化情感词典"""
        if self.initialized:
            return

        try:
            # 加载内置情感词典
            self._load_builtin_dictionaries()
            self.initialized = True
            self.last_updated = os.path.getmtime(__file__)
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
            'yyds', '永远的神', '绝绝子', 'yyds', '666', 'nb', '牛批', '牛逼', '厉害',
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

    def get_sentiment_score(self, text: str) -> Tuple[float, List[str], List[str]]:
        """
        计算文本的情感得分
        
        Args:
            text: 待分析文本
            
        Returns:
            Tuple[float, List[str], List[str]]: (情感得分, 正向词列表, 负向词列表)
        """
        if not self.initialized:
            self.initialize()

        # 检查是否需要更新词典
        self._check_for_updates()

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

    def _check_for_updates(self):
        """检查是否需要更新词典"""
        try:
            # 检查文件修改时间
            current_mtime = os.path.getmtime(__file__)
            if self.last_updated is None or current_mtime > self.last_updated:
                logger.info("检测到词典文件更新，重新加载词典")
                self.initialized = False
                self.initialize()
        except Exception as e:
            logger.debug(f"检查词典更新失败: {e}")

    def update_from_external_source(self, positive_words: list, negative_words: list):
        """
        从外部源更新词典
        
        Args:
            positive_words: 新的正向词列表
            negative_words: 新的负向词列表
        """
        try:
            # 添加新词汇
            self.positive_words.update(positive_words)
            self.negative_words.update(negative_words)
            
            # 更新得分
            for word in positive_words:
                self.positive_scores[word] = 1.0
            for word in negative_words:
                self.negative_scores[word] = -1.0
            
            self.last_updated = time.time()
            logger.info(f"从外部源更新词典，新增正向词: {len(positive_words)}, 新增负向词: {len(negative_words)}")
        except Exception as e:
            logger.error(f"更新词典失败: {e}")

    def get_dictionary_stats(self):
        """
        获取词典统计信息
        
        Returns:
            dict: 词典统计信息
        """
        return {
            "positive_words_count": len(self.positive_words),
            "negative_words_count": len(self.negative_words),
            "last_updated": self.last_updated,
            "initialized": self.initialized
        }


# 全局情感词典实例
sentiment_dict = SentimentDictionary()
sentiment_dict.initialize()
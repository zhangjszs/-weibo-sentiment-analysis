#!/usr/bin/env python3
"""
数据增强模块
功能：文本数据增强，包括同义词替换、随机删除、随机交换、回译等
"""

import logging
import random
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

try:
    import jieba

    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logger.warning("jieba未安装，部分功能不可用")


class SynonymReplacer:
    """同义词替换器"""

    def __init__(self, synonym_dict: Dict[str, List[str]] = None):
        self.synonym_dict = synonym_dict or self._load_default_synonyms()

    def _load_default_synonyms(self) -> Dict[str, List[str]]:
        """加载默认同义词词典"""
        return {
            "好": ["棒", "优秀", "出色", "不错", "良好"],
            "坏": ["差", "糟糕", "恶劣", "不好"],
            "喜欢": ["爱", "喜爱", "钟爱", "热爱"],
            "讨厌": ["厌恶", "憎恨", "不喜欢", "反感"],
            "漂亮": ["美丽", "好看", "美观", "秀丽"],
            "丑": ["难看", "丑陋", "不美观"],
            "大": ["巨大", "庞大", "硕大"],
            "小": ["微小", "细小", "渺小"],
            "快": ["迅速", "快速", "飞快"],
            "慢": ["缓慢", "迟缓", "徐徐"],
            "高兴": ["开心", "快乐", "愉快", "欣喜"],
            "难过": ["伤心", "悲伤", "痛苦", "忧愁"],
            "便宜": ["廉价", "实惠", "低价"],
            "贵": ["昂贵", "高价", "不便宜"],
            "推荐": ["建议", "推介", "安利"],
            "满意": ["满足", "称心", "如意"],
            "失望": ["失落", "沮丧", "不满"],
            "质量": ["品质", "质地", "做工"],
            "服务": ["客服", "售后", "态度"],
            "物流": ["快递", "配送", "发货"],
        }

    def replace(self, text: str, n: int = 1) -> str:
        """
        替换文本中的n个词为同义词

        Args:
            text: 原始文本
            n: 替换数量

        Returns:
            str: 替换后的文本
        """
        if not JIEBA_AVAILABLE:
            return text

        words = list(jieba.cut(text))
        candidates = [w for w in words if w in self.synonym_dict]

        if not candidates:
            return text

        n = min(n, len(candidates))
        to_replace = random.sample(candidates, n)

        new_words = []
        for word in words:
            if word in to_replace:
                synonyms = self.synonym_dict[word]
                new_word = random.choice(synonyms)
                new_words.append(new_word)
            else:
                new_words.append(word)

        return "".join(new_words)


class RandomDeleter:
    """随机删除器"""

    def __init__(self, p: float = 0.1):
        """
        Args:
            p: 删除概率
        """
        self.p = p

    def delete(self, text: str) -> str:
        """
        随机删除文本中的词

        Args:
            text: 原始文本

        Returns:
            str: 删除后的文本
        """
        if not JIEBA_AVAILABLE:
            return text

        words = list(jieba.cut(text))

        if len(words) <= 3:
            return text

        new_words = []
        for word in words:
            if random.random() > self.p:
                new_words.append(word)

        if not new_words:
            return random.choice(words)

        return "".join(new_words)


class RandomSwapper:
    """随机交换器"""

    def __init__(self, n: int = 1):
        """
        Args:
            n: 交换次数
        """
        self.n = n

    def swap(self, text: str) -> str:
        """
        随机交换文本中的词的位置

        Args:
            text: 原始文本

        Returns:
            str: 交换后的文本
        """
        if not JIEBA_AVAILABLE:
            return text

        words = list(jieba.cut(text))

        if len(words) < 2:
            return text

        for _ in range(self.n):
            idx1, idx2 = random.sample(range(len(words)), 2)
            words[idx1], words[idx2] = words[idx2], words[idx1]

        return "".join(words)


class BackTranslator:
    """回译增强器"""

    def __init__(self):
        self.translators = {}

    def _get_translator(self, src: str, dest: str):
        """获取翻译器"""
        try:
            import googletrans

            if f"{src}-{dest}" not in self.translators:
                self.translators[f"{src}-{dest}"] = googletrans.Translator()
            return self.translators[f"{src}-{dest}"]
        except ImportError:
            logger.warning("googletrans未安装，回译功能不可用")
            return None

    def back_translate(self, text: str, intermediate_lang: str = "en") -> str:
        """
        回译增强：中文 -> 英文 -> 中文

        Args:
            text: 原始文本
            intermediate_lang: 中间语言

        Returns:
            str: 回译后的文本
        """
        translator = self._get_translator("zh-cn", intermediate_lang)

        if translator is None:
            return text

        try:
            translated = translator.translate(text, src="zh-cn", dest=intermediate_lang)
            back_translated = translator.translate(
                translated.text, src=intermediate_lang, dest="zh-cn"
            )
            return back_translated.text
        except Exception as e:
            logger.warning(f"回译失败: {e}")
            return text


class TextAugmenter:
    """文本增强器 - 整合所有增强方法"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: 配置字典
        """
        self.config = config or {
            "synonym_replace_prob": 0.3,
            "random_delete_prob": 0.1,
            "random_swap_prob": 0.3,
            "num_augmentations": 4,
        }

        self.synonym_replacer = SynonymReplacer()
        self.random_deleter = RandomDeleter(p=self.config["random_delete_prob"])
        self.random_swapper = RandomSwapper(n=1)
        self.back_translator = BackTranslator()

    def augment(self, text: str, methods: List[str] = None) -> List[str]:
        """
        对文本进行数据增强

        Args:
            text: 原始文本
            methods: 使用的增强方法列表

        Returns:
            List[str]: 增强后的文本列表
        """
        if methods is None:
            methods = ["synonym", "delete", "swap"]

        augmented = [text]

        if "synonym" in methods:
            augmented.append(self.synonym_replacer.replace(text, n=1))

        if "delete" in methods:
            augmented.append(self.random_deleter.delete(text))

        if "swap" in methods:
            augmented.append(self.random_swapper.swap(text))

        return list(set(augmented))

    def augment_dataset(
        self,
        texts: List[str],
        labels: List[int],
        augment_factor: int = 2,
        balance: bool = True,
    ) -> Tuple[List[str], List[int]]:
        """
        对数据集进行增强

        Args:
            texts: 文本列表
            labels: 标签列表
            augment_factor: 增强倍数
            balance: 是否平衡各类别

        Returns:
            Tuple[List[str], List[int]]: 增强后的文本和标签
        """
        from collections import Counter

        augmented_texts = list(texts)
        augmented_labels = list(labels)

        if balance:
            label_counts = Counter(labels)
            max_count = max(label_counts.values())

            for label, count in label_counts.items():
                if count < max_count:
                    label_texts = [t for t, lbl in zip(texts, labels) if lbl == label]
                    needed = max_count - count

                    for _ in range(needed):
                        original = random.choice(label_texts)
                        augmented_text = random.choice(self.augment(original))
                        augmented_texts.append(augmented_text)
                        augmented_labels.append(label)
        else:
            for _ in range(augment_factor - 1):
                for text, label in zip(texts, labels):
                    augmented_text = random.choice(self.augment(text))
                    augmented_texts.append(augmented_text)
                    augmented_labels.append(label)

        return augmented_texts, augmented_labels


class NoiseInjector:
    """噪声注入器"""

    def __init__(self, noise_prob: float = 0.05):
        self.noise_prob = noise_prob
        self.noise_chars = list('，。！？、；：""（）【】')

    def inject(self, text: str) -> str:
        """
        注入随机噪声

        Args:
            text: 原始文本

        Returns:
            str: 注入噪声后的文本
        """
        chars = list(text)

        for i in range(len(chars)):
            if random.random() < self.noise_prob:
                noise_type = random.choice(["insert", "replace", "delete"])

                if noise_type == "insert":
                    chars.insert(i, random.choice(self.noise_chars))
                elif noise_type == "replace" and chars[i] not in self.noise_chars:
                    chars[i] = random.choice(self.noise_chars)
                elif noise_type == "delete":
                    chars[i] = ""

        return "".join(chars)


def augment_training_data(
    input_path: str, output_path: str, augment_factor: int = 2, balance: bool = True
) -> Dict[str, Any]:
    """
    增强训练数据

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        augment_factor: 增强倍数
        balance: 是否平衡类别

    Returns:
        dict: 增强统计信息
    """
    import pandas as pd

    df = pd.read_csv(input_path, header=None, names=["text", "label"])

    original_count = len(df)
    label_dist = df["label"].value_counts().to_dict()

    augmenter = TextAugmenter()
    augmented_texts, augmented_labels = augmenter.augment_dataset(
        df["text"].tolist(),
        df["label"].tolist(),
        augment_factor=augment_factor,
        balance=balance,
    )

    augmented_df = pd.DataFrame({"text": augmented_texts, "label": augmented_labels})

    augmented_df.to_csv(output_path, index=False, header=False)

    new_label_dist = augmented_df["label"].value_counts().to_dict()

    return {
        "original_count": original_count,
        "augmented_count": len(augmented_df),
        "augment_factor": len(augmented_df) / original_count,
        "original_label_dist": label_dist,
        "new_label_dist": new_label_dist,
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="文本数据增强")
    parser.add_argument("--input", type=str, help="输入文件路径")
    parser.add_argument("--output", type=str, help="输出文件路径")
    parser.add_argument("--factor", type=int, default=2, help="增强倍数")
    parser.add_argument("--balance", action="store_true", help="平衡类别")
    parser.add_argument("--demo", action="store_true", help="演示模式")

    args = parser.parse_args()

    if args.demo:
        augmenter = TextAugmenter()
        demo_texts = [
            "这个产品质量很好，非常满意",
            "物流太慢了，等了好久才收到",
            "一般般吧，没什么特别的",
        ]

        print("数据增强演示:")
        print("=" * 50)

        for text in demo_texts:
            augmented = augmenter.augment(text)
            print(f"原文: {text}")
            for i, aug_text in enumerate(augmented[1:], 1):
                print(f"增强{i}: {aug_text}")
            print("-" * 30)

        return

    if args.input and args.output:
        stats = augment_training_data(
            args.input, args.output, augment_factor=args.factor, balance=args.balance
        )

        print("数据增强完成:")
        print(f"原始样本数: {stats['original_count']}")
        print(f"增强后样本数: {stats['augmented_count']}")
        print(f"增强倍数: {stats['augment_factor']:.2f}")
        print(f"原始类别分布: {stats['original_label_dist']}")
        print(f"新类别分布: {stats['new_label_dist']}")


if __name__ == "__main__":
    main()

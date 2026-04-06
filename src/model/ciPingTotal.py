#!/usr/bin/env python3
"""
修复后的词频统计模块
解决原有逻辑问题，提升性能和安全性
"""

import csv
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WordFrequencyAnalyzer:
    """词频分析器 - 修复版本"""

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent

        self.input_file = self.model_dir / "comment_1_fenci.txt"
        self.output_file = self.model_dir / "comment_1_fenci_qutingyongci_cipin.csv"
        self.stop_words_file = self.model_dir / "stopWords.txt"

        self.stop_words = self._load_stop_words()

        logger.info("词频分析器初始化完成")

    def _load_stop_words(self) -> set:
        """加载停用词表"""
        stop_words = set()

        try:
            if self.stop_words_file.exists():
                with open(self.stop_words_file, encoding="utf-8") as f:
                    stop_words = {line.strip() for line in f if line.strip()}
                logger.info(f"加载停用词 {len(stop_words)} 个")
            else:
                logger.warning(f"停用词文件不存在: {self.stop_words_file}")
                stop_words = {
                    "的",
                    "了",
                    "在",
                    "是",
                    "我",
                    "有",
                    "和",
                    "就",
                    "不",
                    "人",
                    "都",
                    "一",
                    "一个",
                    "上",
                    "也",
                    "很",
                    "到",
                    "说",
                    "要",
                    "去",
                    "你",
                    "会",
                    "着",
                    "没有",
                    "看",
                    "好",
                    "自己",
                    "这",
                    "能",
                    "而",
                }
        except Exception as e:
            logger.error(f"加载停用词失败: {e}")
            stop_words = set()

        return stop_words

    def read_segmented_text(self) -> Optional[str]:
        """读取分词文本"""
        try:
            if not self.input_file.exists():
                logger.error(f"输入文件不存在: {self.input_file}")
                return None

            with open(self.input_file, encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                logger.warning("输入文件为空")
                return None

            logger.info(f"读取分词文本，长度: {len(content)}")
            return content

        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return None

    def filter_words(self, words: List[str]) -> List[str]:
        """过滤无效词语"""
        filtered_words = []

        for word in words:
            word = word.strip()

            if (
                word
                and len(word) > 1
                and word not in self.stop_words
                and not re.match(r"^\d+$", word)
                and not re.match(r"^[^\u4e00-\u9fa5a-zA-Z]+$", word)
                and len(word) <= 10
            ):
                filtered_words.append(word)

        return filtered_words

    def calculate_frequency(
        self, content: str, max_results: int = 300
    ) -> List[Tuple[str, int]]:
        """计算词频 - 改进版"""
        try:
            words = content.split()

            if not words:
                logger.warning("没有找到词语")
                return []

            filtered_words = self.filter_words(words)

            if not filtered_words:
                logger.warning("过滤后没有有效词语")
                return []

            word_counter = Counter(filtered_words)

            most_common = word_counter.most_common(max_results)

            logger.info(f"词频统计完成，共 {len(most_common)} 个词语")
            return most_common

        except Exception as e:
            logger.error(f"词频计算失败: {e}")
            return []

    def save_frequency_results(self, word_freq: List[Tuple[str, int]]) -> bool:
        """保存词频结果 - 安全版"""
        if not word_freq:
            logger.warning("词频结果为空，跳过保存")
            return False

        try:
            if self.output_file.exists():
                backup_file = self.output_file.with_suffix(".csv.bak")
                self.output_file.rename(backup_file)
                logger.info(f"原文件已备份为: {backup_file}")

            with open(self.output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["词语", "频次"])

                for word, freq in word_freq:
                    writer.writerow([word, freq])

            logger.info(f"词频结果已保存: {self.output_file}")
            return True

        except Exception as e:
            logger.error(f"保存词频结果失败: {e}")
            return False

    def generate_frequency_report(self, word_freq: List[Tuple[str, int]]) -> Dict:
        """生成词频分析报告"""
        if not word_freq:
            return {}

        try:
            total_words = sum(freq for _, freq in word_freq)
            unique_words = len(word_freq)

            frequencies = [freq for _, freq in word_freq]
            max_freq = max(frequencies)
            min_freq = min(frequencies)
            avg_freq = total_words / unique_words if unique_words > 0 else 0

            freq_distribution = {
                "高频词(>10次)": len([f for f in frequencies if f > 10]),
                "中频词(3-10次)": len([f for f in frequencies if 3 <= f <= 10]),
                "低频词(1-2次)": len([f for f in frequencies if f <= 2]),
            }

            report = {
                "total_word_count": total_words,
                "unique_word_count": unique_words,
                "max_frequency": max_freq,
                "min_frequency": min_freq,
                "average_frequency": round(avg_freq, 2),
                "frequency_distribution": freq_distribution,
                "top_10_words": word_freq[:10],
            }

            logger.info(f"词频报告生成完成: {report}")
            return report

        except Exception as e:
            logger.error(f"生成词频报告失败: {e}")
            return {}

    def run_frequency_analysis(self, max_results: int = 300) -> bool:
        """运行完整的词频分析流程"""
        logger.info("开始执行词频分析...")

        try:
            content = self.read_segmented_text()
            if not content:
                logger.error("无法读取分词文本，分析终止")
                return False

            word_freq = self.calculate_frequency(content, max_results)
            if not word_freq:
                logger.error("词频计算失败，分析终止")
                return False

            if not self.save_frequency_results(word_freq):
                logger.error("保存词频结果失败")
                return False

            report = self.generate_frequency_report(word_freq)
            if report:
                report_file = self.model_dir / "frequency_report.json"
                import json

                with open(report_file, "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                logger.info(f"分析报告已保存: {report_file}")

            logger.info("词频分析完成")
            return True

        except Exception as e:
            logger.error(f"词频分析异常: {e}")
            return False

    def get_top_words(self, n: int = 20) -> List[Tuple[str, int]]:
        """获取高频词TOP N"""
        try:
            if not self.output_file.exists():
                logger.error(f"词频文件不存在: {self.output_file}")
                return []

            df = pd.read_csv(self.output_file)

            top_words = []
            for _, row in df.head(n).iterrows():
                top_words.append((row["词语"], int(row["频次"])))

            logger.info(f"获取TOP {n} 高频词完成")
            return top_words

        except Exception as e:
            logger.error(f"获取高频词失败: {e}")
            return []


def main():
    """主函数"""
    try:
        analyzer = WordFrequencyAnalyzer()

        success = analyzer.run_frequency_analysis(max_results=300)

        if success:
            logger.info("词频分析成功!")

            top_words = analyzer.get_top_words(10)
            if top_words:
                logger.info("TOP 10 高频词:")
                for i, (word, freq) in enumerate(top_words, 1):
                    logger.info(f"  {i:2d}. {word} ({freq}次)")
        else:
            logger.error("词频分析失败!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

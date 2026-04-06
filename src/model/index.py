#!/usr/bin/env python3
"""
修复后的模型数据处理模块
解决原有逻辑问题，提升性能和稳定性
"""

import csv
import logging
import os
import re
import sys
from pathlib import Path
from typing import List

import jieba

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))

from utils.query import query_dataframe


class ModelDataProcessor:
    """模型数据处理类 - 修复版本"""

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent
        self.stop_words = self._load_stop_words()

        self.target_txt = self.model_dir / "comment_1_fenci.txt"
        self.target_csv = self.model_dir / "target.csv"
        self.freq_csv = self.model_dir / "comment_1_fenci_qutingyongci_cipin.csv"
        self.stop_words_file = self.model_dir / "stopWords.txt"

        logger.info("模型数据处理器初始化完成")

    def _load_stop_words(self) -> set:
        """加载停用词 - 改进版"""
        stop_words_path = self.model_dir / "stopWords.txt"
        stop_words = set()

        try:
            if stop_words_path.exists():
                with open(stop_words_path, encoding="UTF-8") as f:
                    stop_words = {line.strip() for line in f if line.strip()}
                logger.info(f"加载停用词 {len(stop_words)} 个")
            else:
                logger.warning(f"停用词文件不存在: {stop_words_path}")
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
                }
        except Exception as e:
            logger.error(f"加载停用词失败: {e}")
            stop_words = set()

        return stop_words

    def get_comment_list(self) -> List[List]:
        """获取评论数据 - 改进版"""
        try:
            df = query_dataframe(
                """
                SELECT articleId, created_at, content
                FROM comments
                WHERE content IS NOT NULL AND content != ''
                ORDER BY created_at DESC
                LIMIT 1000
                """
            )
            comment_list = df.values.tolist() if not df.empty else []
            if not comment_list:
                logger.warning("未获取到评论数据")
                return []

            logger.info(f"获取到 {len(comment_list)} 条评论数据")
            return comment_list

        except ImportError as e:
            logger.error(f"导入模块失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取评论数据失败: {e}")
            return []

    def clean_and_segment_text(self, comment_list: List[List]) -> str:
        """清洗和分词文本 - 修复版"""
        if not comment_list:
            logger.warning("评论列表为空")
            return ""

        try:
            texts = []
            for comment in comment_list:
                if len(comment) > 4 and comment[4]:
                    text = str(comment[4]).strip()
                    if text and len(text) > 1:
                        texts.append(text)

            if not texts:
                logger.warning("没有有效的评论文本")
                return ""

            combined_text = " ".join(texts)
            logger.info(f"合并文本长度: {len(combined_text)}")

            word_list = jieba.cut(combined_text, cut_all=False)

            filtered_words = []
            for word in word_list:
                word = word.strip()
                if (
                    word
                    and len(word) > 1
                    and word not in self.stop_words
                    and not re.match(r"^\d+$", word)
                    and not re.match(r"^\W+$", word)
                ):
                    filtered_words.append(word)

            result = " ".join(filtered_words)
            logger.info(f"分词完成，有效词数: {len(filtered_words)}")

            return result

        except Exception as e:
            logger.error(f"文本分词失败: {e}")
            return ""

    def write_segmented_text(self, segmented_text: str) -> bool:
        """写入分词结果 - 改进版"""
        if not segmented_text:
            logger.warning("分词文本为空，跳过写入")
            return False

        try:
            with open(self.target_txt, "w", encoding="utf-8") as f:
                f.write(segmented_text)

            logger.info(f"分词结果已保存到: {self.target_txt}")
            return True

        except Exception as e:
            logger.error(f"写入分词文件失败: {e}")
            return False

    def calculate_word_frequency(self, max_words: int = 300) -> bool:
        """计算词频 - 改进版"""
        if not self.target_txt.exists():
            logger.error(f"分词文件不存在: {self.target_txt}")
            return False

        try:
            with open(self.target_txt, encoding="utf8") as f:
                content = f.read()

            if not content.strip():
                logger.warning("分词文件为空")
                return False

            word_list = jieba.cut(content, cut_all=True)

            valid_words = []
            for word in word_list:
                word = word.strip()
                if (
                    word
                    and len(word) > 1
                    and not re.search(r"\d+", word)
                    and not re.search(r"\W+", word)
                ):
                    valid_words.append(word)

            if not valid_words:
                logger.warning("没有有效词语用于统计")
                return False

            word_count = {}
            unique_words = set(valid_words)
            for word in unique_words:
                word_count[word] = valid_words.count(word)

            sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)

            output_count = min(max_words, len(sorted_words))

            with open(self.freq_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                for i in range(output_count):
                    writer.writerow([sorted_words[i][0], sorted_words[i][1]])

            logger.info(f"词频统计完成，输出 {output_count} 个词语到: {self.freq_csv}")
            return True

        except Exception as e:
            logger.error(f"词频计算失败: {e}")
            return False

    def process_data_pipeline(self) -> bool:
        """完整的数据处理流水线 - 改进版"""
        logger.info("开始执行数据处理流水线...")

        try:
            comment_list = self.get_comment_list()
            if not comment_list:
                logger.error("无法获取评论数据，流水线终止")
                return False

            segmented_text = self.clean_and_segment_text(comment_list)
            if not segmented_text:
                logger.error("文本分词失败，流水线终止")
                return False

            if not self.write_segmented_text(segmented_text):
                logger.error("保存分词结果失败，流水线终止")
                return False

            if not self.calculate_word_frequency():
                logger.error("词频计算失败，流水线终止")
                return False

            logger.info("数据处理流水线执行成功")
            return True

        except Exception as e:
            logger.error(f"数据处理流水线异常: {e}")
            return False

    def cleanup_temp_files(self):
        """清理临时文件 - 安全版"""
        temp_files = [self.target_txt, self.target_csv, self.freq_csv]

        for file_path in temp_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"已删除临时文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败 {file_path}: {e}")


def main():
    """主函数 - 入口点"""
    processor = ModelDataProcessor()

    success = processor.process_data_pipeline()

    if success:
        logger.info("模型数据处理完成")
    else:
        logger.error("模型数据处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()

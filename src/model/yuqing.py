#!/usr/bin/env python3
"""
修复后的舆情分析主控制器
解决原有逻辑问题，提升安全性和稳定性
"""

import logging
import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from utils.query import query_dataframe

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """情感分析控制器 - 修复版本"""

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent
        self.model_path = self.model_dir / "best_sentiment_model.pkl"
        self.model = None

        self.target_csv = self.model_dir / "target.csv"
        self.freq_csv = self.model_dir / "comment_1_fenci_qutingyongci_cipin.csv"

        logger.info("情感分析器初始化完成")

    def load_model(self) -> bool:
        """加载训练好的模型 - 安全版"""
        try:
            if not self.model_path.exists():
                logger.error(f"模型文件不存在: {self.model_path}")
                return False

            with open(self.model_path, "rb") as f:
                self.model = pickle.load(f)

            logger.info(f"模型加载成功: {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False

    def get_comment_data(self) -> List[List]:
        """获取评论数据 - 改进版"""
        try:
            comment_df = query_dataframe(
                """
                SELECT articleId, created_at, content
                FROM comments
                WHERE content IS NOT NULL AND content != ''
                ORDER BY created_at DESC
                LIMIT 1000
                """
            )
            comment_list = comment_df.values.tolist() if not comment_df.empty else []
            if not comment_list:
                logger.warning("未获取到评论数据")
                return []

            logger.info(f"获取到 {len(comment_list)} 条评论数据")
            return comment_list

        except ImportError as e:
            logger.error(f"导入数据模块失败: {e}")
            return self._load_from_csv_backup()
        except Exception as e:
            logger.error(f"获取评论数据失败: {e}")
            return []

    def _load_from_csv_backup(self) -> List[List]:
        """从CSV文件读取数据作为备用方案"""
        try:
            csv_files = [
                self.model_dir.parent / "spider" / "commentsData.csv",
                self.model_dir.parent / "cache" / "comments.csv",
            ]

            for csv_file in csv_files:
                if csv_file.exists():
                    df = pd.read_csv(csv_file)
                    logger.info(f"从备用CSV文件读取数据: {csv_file}")
                    return df.values.tolist()

            logger.warning("未找到备用CSV文件")
            return []

        except Exception as e:
            logger.error(f"读取备用CSV文件失败: {e}")
            return []

    def preprocess_comments(self, comment_list: List[List]) -> List[str]:
        """预处理评论文本 - 改进版"""
        if not comment_list:
            logger.warning("评论列表为空")
            return []

        try:
            processed_texts = []

            for comment in comment_list:
                if len(comment) > 4 and comment[4]:
                    text = str(comment[4]).strip()

                    if text and len(text) > 2:
                        import re

                        text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9\s]", "", text)
                        text = re.sub(r"\s+", " ", text).strip()

                        if text:
                            processed_texts.append(text)

            logger.info(f"预处理完成，有效文本 {len(processed_texts)} 条")
            return processed_texts

        except Exception as e:
            logger.error(f"文本预处理失败: {e}")
            return []

    def analyze_sentiment(self, texts: List[str]) -> List[Dict[str, Any]]:
        """情感分析 - 改进版"""
        if not texts:
            logger.warning("文本列表为空")
            return []

        if not self.model:
            logger.error("模型未加载")
            return []

        try:
            results = []

            for i, text in enumerate(texts):
                try:
                    prediction = self.model.predict([text])
                    probability = self.model.predict_proba([text])

                    sentiment_map = {0: "负面", 1: "中性", 2: "正面"}
                    sentiment = sentiment_map.get(prediction[0], "未知")

                    confidence = float(np.max(probability))

                    results.append(
                        {
                            "text": text,
                            "sentiment": sentiment,
                            "confidence": confidence,
                            "raw_prediction": int(prediction[0]),
                        }
                    )

                except Exception as e:
                    logger.warning(f"分析第{i}条文本失败: {e}")
                    results.append(
                        {
                            "text": text,
                            "sentiment": "未知",
                            "confidence": 0.0,
                            "raw_prediction": -1,
                        }
                    )

            logger.info(f"情感分析完成，处理 {len(results)} 条文本")
            return results

        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            return []

    def save_analysis_results(self, results: List[Dict[str, Any]]) -> bool:
        """保存分析结果 - 安全版"""
        if not results:
            logger.warning("结果列表为空，跳过保存")
            return False

        try:
            df = pd.DataFrame(results)

            df["analysis_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            output_file = (
                self.model_dir
                / f"sentiment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            df.to_csv(output_file, index=False, encoding="utf-8")

            if self.target_csv.exists():
                backup_file = self.target_csv.with_suffix(".csv.bak")
                if self.target_csv.exists():
                    self.target_csv.rename(backup_file)

            df.to_csv(self.target_csv, index=False, encoding="utf-8")

            logger.info(f"分析结果已保存: {output_file}")
            logger.info(f"目标文件已更新: {self.target_csv}")
            return True

        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            return False

    def generate_summary_statistics(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成汇总统计 - 新增功能"""
        if not results:
            return {}

        try:
            total_count = len(results)
            sentiment_counts = {}
            confidence_sum = 0

            for result in results:
                sentiment = result.get("sentiment", "未知")
                confidence = result.get("confidence", 0)

                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                confidence_sum += confidence

            sentiment_ratios = {
                sentiment: count / total_count
                for sentiment, count in sentiment_counts.items()
            }

            summary = {
                "total_comments": total_count,
                "sentiment_counts": sentiment_counts,
                "sentiment_ratios": sentiment_ratios,
                "average_confidence": confidence_sum / total_count
                if total_count > 0
                else 0,
                "analysis_time": datetime.now().isoformat(),
            }

            logger.info(f"统计汇总完成: {summary}")
            return summary

        except Exception as e:
            logger.error(f"生成统计汇总失败: {e}")
            return {}

    def run_analysis_pipeline(self) -> bool:
        """运行完整分析流水线 - 主要接口"""
        logger.info("开始执行舆情分析流水线...")

        try:
            if not self.load_model():
                logger.error("模型加载失败，流水线终止")
                return False

            comment_list = self.get_comment_data()
            if not comment_list:
                logger.error("无法获取评论数据，流水线终止")
                return False

            processed_texts = self.preprocess_comments(comment_list)
            if not processed_texts:
                logger.error("文本预处理失败，流水线终止")
                return False

            analysis_results = self.analyze_sentiment(processed_texts)
            if not analysis_results:
                logger.error("情感分析失败，流水线终止")
                return False

            if not self.save_analysis_results(analysis_results):
                logger.error("保存结果失败，但分析已完成")

            summary = self.generate_summary_statistics(analysis_results)
            if summary:
                summary_file = self.model_dir / "analysis_summary.json"
                import json

                with open(summary_file, "w", encoding="utf-8") as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
                logger.info(f"统计汇总已保存: {summary_file}")

            logger.info("舆情分析流水线执行成功")
            return True

        except Exception as e:
            logger.error(f"分析流水线异常: {e}")
            return False

    def safe_cleanup(self, keep_results: bool = True):
        """安全清理临时文件"""
        temp_files = []

        if not keep_results:
            temp_files.extend(
                [
                    self.model_dir / "comment_1_fenci.txt",
                    self.model_dir / "temp_analysis.csv",
                ]
            )

        for file_path in temp_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"已删除临时文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除临时文件失败 {file_path}: {e}")


def main():
    """主函数 - 程序入口"""
    try:
        analyzer = SentimentAnalyzer()

        success = analyzer.run_analysis_pipeline()

        if success:
            logger.info("舆情分析完成!")
        else:
            logger.error("舆情分析失败!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

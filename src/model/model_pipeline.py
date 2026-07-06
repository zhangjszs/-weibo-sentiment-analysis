#!/usr/bin/env python3
"""
完整的模型处理流水线控制器
整合所有修复后的模块，提供统一的接口
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "utils"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            project_root / "logs" / "model_pipeline.log", encoding="utf-8"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ModelPipeline:
    """完整的模型处理流水线"""

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent
        self.project_root = self.model_dir.parent

        # 初始化子模块
        self.data_processor = None
        self.sentiment_analyzer = None
        self.frequency_analyzer = None

        # 流水线状态
        self.pipeline_status = {
            "data_processing": False,
            "sentiment_analysis": False,
            "frequency_analysis": False,
            "start_time": None,
            "end_time": None,
        }

        logger.info("模型流水线初始化完成")

    def _initialize_modules(self) -> bool:
        """初始化所有处理模块"""
        try:
            # 直接从同级模块导入（不再依赖不存在的 improved_* 包装）
            from .ciPingTotal import WordFrequencyAnalyzer
            from .index import ModelDataProcessor
            from .yuqing import SentimentAnalyzer

            # 创建实例
            self.data_processor = ModelDataProcessor(str(self.model_dir))
            self.sentiment_analyzer = SentimentAnalyzer(str(self.model_dir))
            self.frequency_analyzer = WordFrequencyAnalyzer(str(self.model_dir))

            logger.info("所有模块初始化成功")
            return True

        except ImportError as e:
            logger.error(f"模块导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"模块初始化失败: {e}")
            return False

    def run_data_processing(self) -> bool:
        """运行数据处理步骤"""
        logger.info("📊 开始数据处理...")

        try:
            if not self.data_processor:
                logger.error("数据处理器未初始化")
                return False

            success = self.data_processor.process_data_pipeline()
            self.pipeline_status["data_processing"] = success

            if success:
                logger.info("✅ 数据处理完成")
            else:
                logger.error("❌ 数据处理失败")

            return success

        except Exception as e:
            logger.error(f"数据处理异常: {e}")
            return False

    def run_sentiment_analysis(self) -> bool:
        """运行情感分析步骤"""
        logger.info("😊 开始情感分析...")

        try:
            if not self.sentiment_analyzer:
                logger.error("情感分析器未初始化")
                return False

            success = self.sentiment_analyzer.run_analysis_pipeline()
            self.pipeline_status["sentiment_analysis"] = success

            if success:
                logger.info("✅ 情感分析完成")
            else:
                logger.error("❌ 情感分析失败")

            return success

        except Exception as e:
            logger.error(f"情感分析异常: {e}")
            return False

    def run_frequency_analysis(self) -> bool:
        """运行词频分析步骤"""
        logger.info("📈 开始词频分析...")

        try:
            if not self.frequency_analyzer:
                logger.error("词频分析器未初始化")
                return False

            success = self.frequency_analyzer.run_frequency_analysis()
            self.pipeline_status["frequency_analysis"] = success

            if success:
                logger.info("✅ 词频分析完成")
            else:
                logger.error("❌ 词频分析失败")

            return success

        except Exception as e:
            logger.error(f"词频分析异常: {e}")
            return False

    def generate_pipeline_report(self) -> Dict[str, Any]:
        """生成流水线执行报告"""
        try:
            # 计算执行时间
            execution_time = None
            if self.pipeline_status["start_time"] and self.pipeline_status["end_time"]:
                execution_time = (
                    self.pipeline_status["end_time"]
                    - self.pipeline_status["start_time"]
                ).total_seconds()

            # 统计成功步骤
            successful_steps = sum(
                1 for status in self.pipeline_status.values() if status is True
            )
            total_steps = 3  # 数据处理、情感分析、词频分析

            # 收集文件信息
            output_files = []
            for file_path in [
                self.model_dir / "comment_1_fenci.txt",
                self.model_dir / "target.csv",
                self.model_dir / "comment_1_fenci_qutingyongci_cipin.csv",
                self.model_dir / "analysis_summary.json",
                self.model_dir / "frequency_report.json",
            ]:
                if file_path.exists():
                    output_files.append(
                        {
                            "file": str(file_path),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                        }
                    )

            report = {
                "pipeline_status": self.pipeline_status,
                "execution_time_seconds": execution_time,
                "success_rate": f"{successful_steps}/{total_steps}",
                "output_files": output_files,
                "timestamp": datetime.now().isoformat(),
            }

            return report

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return {}

    def save_pipeline_report(self, report: Dict[str, Any]) -> bool:
        """保存流水线报告"""
        try:
            import json

            report_file = (
                self.model_dir
                / f"pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"流水线报告已保存: {report_file}")
            return True

        except Exception as e:
            logger.error(f"保存报告失败: {e}")
            return False

    def run_complete_pipeline(self, skip_on_error: bool = False) -> bool:
        """运行完整的模型处理流水线"""
        logger.info("🚀 启动完整模型处理流水线...")

        try:
            # 记录开始时间
            self.pipeline_status["start_time"] = datetime.now()

            # 1. 初始化模块
            if not self._initialize_modules():
                logger.error("模块初始化失败，流水线终止")
                return False

            # 2. 数据处理
            data_success = self.run_data_processing()
            if not data_success and not skip_on_error:
                logger.error("数据处理失败，流水线终止")
                return False

            # 3. 情感分析
            sentiment_success = self.run_sentiment_analysis()
            if not sentiment_success and not skip_on_error:
                logger.error("情感分析失败，流水线终止")
                return False

            # 4. 词频分析
            frequency_success = self.run_frequency_analysis()
            if not frequency_success and not skip_on_error:
                logger.error("词频分析失败，流水线终止")
                return False

            # 记录结束时间
            self.pipeline_status["end_time"] = datetime.now()

            # 5. 生成和保存报告
            report = self.generate_pipeline_report()
            if report:
                self.save_pipeline_report(report)

            # 判断总体成功
            overall_success = all([data_success, sentiment_success, frequency_success])

            if overall_success:
                logger.info("🎉 完整模型流水线执行成功!")
            else:
                logger.warning("⚠️  流水线部分步骤失败，请检查日志")

            return overall_success

        except Exception as e:
            logger.error(f"流水线执行异常: {e}")
            self.pipeline_status["end_time"] = datetime.now()
            return False

    def run_step_by_step(self) -> bool:
        """逐步运行流水线（调试模式）"""
        logger.info("🔍 启动逐步执行模式...")

        try:
            # 初始化
            if not self._initialize_modules():
                return False

            self.pipeline_status["start_time"] = datetime.now()

            # 逐步执行
            steps = [
                ("数据处理", self.run_data_processing),
                ("情感分析", self.run_sentiment_analysis),
                ("词频分析", self.run_frequency_analysis),
            ]

            for step_name, step_func in steps:
                logger.info(f"👉 正在执行: {step_name}")

                try:
                    success = step_func()
                    if success:
                        logger.info(f"✅ {step_name} 完成")
                    else:
                        logger.error(f"❌ {step_name} 失败")

                        # 询问是否继续
                        user_input = input(
                            f"{step_name} 失败，是否继续下一步？(y/n): "
                        ).lower()
                        if user_input != "y":
                            logger.info("用户选择终止流水线")
                            return False

                except Exception as e:
                    logger.error(f"{step_name} 异常: {e}")
                    user_input = input(f"{step_name} 异常，是否继续？(y/n): ").lower()
                    if user_input != "y":
                        return False

            self.pipeline_status["end_time"] = datetime.now()

            # 生成报告
            report = self.generate_pipeline_report()
            if report:
                self.save_pipeline_report(report)

            logger.info("🎯 逐步执行模式完成")
            return True

        except KeyboardInterrupt:
            logger.info("用户中断执行")
            return False
        except Exception as e:
            logger.error(f"逐步执行异常: {e}")
            return False


def main():
    """主函数"""
    try:
        # 创建流水线
        pipeline = ModelPipeline()

        # 检查命令行参数
        import argparse

        parser = argparse.ArgumentParser(description="模型处理流水线")
        parser.add_argument(
            "--mode",
            choices=["complete", "step", "data", "sentiment", "frequency"],
            default="complete",
            help="执行模式",
        )
        parser.add_argument(
            "--skip-on-error", action="store_true", help="遇到错误时跳过继续执行"
        )

        args = parser.parse_args()

        # 根据模式执行
        if args.mode == "complete":
            success = pipeline.run_complete_pipeline(skip_on_error=args.skip_on_error)
        elif args.mode == "step":
            success = pipeline.run_step_by_step()
        elif args.mode == "data":
            pipeline._initialize_modules()
            success = pipeline.run_data_processing()
        elif args.mode == "sentiment":
            pipeline._initialize_modules()
            success = pipeline.run_sentiment_analysis()
        elif args.mode == "frequency":
            pipeline._initialize_modules()
            success = pipeline.run_frequency_analysis()
        else:
            logger.error(f"未知模式: {args.mode}")
            success = False

        if success:
            logger.info("🎉 执行成功!")
            sys.exit(0)
        else:
            logger.error("💥 执行失败!")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

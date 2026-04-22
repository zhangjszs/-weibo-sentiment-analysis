#!/usr/bin/env python3
"""
智能策略选择器模块
功能：根据文本特征选择最优情感分析策略，监控策略性能，实现自适应调整
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.tasks import analyze_text_sync

logger = logging.getLogger(__name__)


class StrategyPerformanceMonitor:
    """策略性能监控器"""

    def __init__(self):
        self.performance_dir = Path(__file__).parent / "../model" / "metrics"
        self.performance_dir.mkdir(exist_ok=True, parents=True)
        self.performance_file = self.performance_dir / "strategy_performance.json"
        self._ensure_performance_file()

    def _ensure_performance_file(self):
        """确保性能文件存在"""
        if not self.performance_file.exists():
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "strategies": {
                        "snownlp": {"total_calls": 0, "total_time": 0, "success_rate": 1.0, "accuracy": 0.8},
                        "llm": {"total_calls": 0, "total_time": 0, "success_rate": 0.9, "accuracy": 0.95},
                        "custom_model": {"total_calls": 0, "total_time": 0, "success_rate": 0.95, "accuracy": 0.9}
                    },
                    "history": []
                }, f, ensure_ascii=False, indent=2)

    def record_performance(self, strategy_name: str, latency: float, success: bool, accuracy: float = None):
        """记录策略性能

        Args:
            strategy_name: 策略名称
            latency: 执行时间（秒）
            success: 是否成功
            accuracy: 准确率（如果有）
        """
        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 更新策略性能统计
            if strategy_name in data["strategies"]:
                strategy_data = data["strategies"][strategy_name]
                strategy_data["total_calls"] += 1
                strategy_data["total_time"] += latency
                
                # 更新成功率
                if success:
                    strategy_data["success_rate"] = (
                        (strategy_data["success_rate"] * (strategy_data["total_calls"] - 1) + 1.0) / 
                        strategy_data["total_calls"]
                    )
                else:
                    strategy_data["success_rate"] = (
                        (strategy_data["success_rate"] * (strategy_data["total_calls"] - 1) + 0.0) / 
                        strategy_data["total_calls"]
                    )
                
                # 更新准确率（如果提供）
                if accuracy is not None:
                    if "total_accuracy" not in strategy_data:
                        strategy_data["total_accuracy"] = 0.0
                    strategy_data["total_accuracy"] += accuracy
                    strategy_data["accuracy"] = strategy_data["total_accuracy"] / strategy_data["total_calls"]

            # 添加历史记录
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy_name,
                "latency": latency,
                "success": success,
                "accuracy": accuracy
            }
            data["history"].append(history_entry)
            # 只保留最近1000条历史记录
            data["history"] = data["history"][-1000:]

            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"记录策略性能失败: {e}")

    def get_strategy_performance(self) -> Dict[str, Dict]:
        """获取策略性能数据

        Returns:
            dict: 策略性能数据
        """
        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data["strategies"]
        except Exception as e:
            logger.error(f"获取策略性能数据失败: {e}")
            return {
                "snownlp": {"total_calls": 0, "total_time": 0, "success_rate": 1.0, "accuracy": 0.8},
                "llm": {"total_calls": 0, "total_time": 0, "success_rate": 0.9, "accuracy": 0.95},
                "custom_model": {"total_calls": 0, "total_time": 0, "success_rate": 0.95, "accuracy": 0.9}
            }

    def get_strategy_score(self, strategy_name: str) -> float:
        """计算策略得分

        Args:
            strategy_name: 策略名称

        Returns:
            float: 策略得分（0-1）
        """
        performance = self.get_strategy_performance()
        if strategy_name not in performance:
            return 0.5

        data = performance[strategy_name]
        success_rate = data.get("success_rate", 0.5)
        accuracy = data.get("accuracy", 0.5)
        avg_time = data.get("total_time", 1.0) / max(data.get("total_calls", 1), 1)
        
        # 时间权重（越快越好）
        time_score = max(0.1, 1.0 - min(1.0, avg_time / 2.0))
        
        # 综合得分
        score = (success_rate * 0.3 + accuracy * 0.5 + time_score * 0.2)
        return score


class TextFeatureAnalyzer:
    """文本特征分析器"""

    @staticmethod
    def analyze(text: str) -> Dict[str, any]:
        """分析文本特征

        Args:
            text: 待分析文本

        Returns:
            dict: 文本特征
        """
        features = {
            "length": len(text),
            "word_count": len(text.split()),
            "has_emoji": TextFeatureAnalyzer._has_emoji(text),
            "has_sarcasm": TextFeatureAnalyzer._has_sarcasm(text),
            "has_negation": TextFeatureAnalyzer._has_negation(text),
            "has_internet_slang": TextFeatureAnalyzer._has_internet_slang(text),
            "complexity_score": TextFeatureAnalyzer._calculate_complexity(text)
        }
        return features

    @staticmethod
    def _has_emoji(text: str) -> bool:
        """检测文本是否包含emoji"""
        emoji_patterns = [
            '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '😍', '😘',
            '😗', '😙', '😚', '😋', '😛', '😝', '🤩', '🥳', '👍', '👌',
            '✌️', '🤞', '🤟', '🤘', '😢', '😭', '😞', '😔', '😟', '😕',
            '🙁', '☹️', '😤', '😠', '😡', '🤬', '😰', '😥', '😓', '😨',
            '😱', '🤢', '🤮', '😴', '🤔', '😐', '😑'
        ]
        return any(emoji in text for emoji in emoji_patterns)

    @staticmethod
    def _has_sarcasm(text: str) -> bool:
        """检测文本是否包含讽刺或反语"""
        sarcasm_patterns = [
            '呵呵', '太棒了', '真的', '一点都不', '可真是', '绝了',
            '服了', '醉了', '吐了', '无语', '讽刺', '反语'
        ]
        return any(pattern in text for pattern in sarcasm_patterns)

    @staticmethod
    def _has_negation(text: str) -> bool:
        """检测文本是否包含否定词"""
        negation_patterns = [
            '不', '没', '无', '非', '未', '别', '不要', '没有',
            '不是', '不会', '不能', '不行', '不好'
        ]
        return any(pattern in text for pattern in negation_patterns)

    @staticmethod
    def _has_internet_slang(text: str) -> bool:
        """检测文本是否包含网络用语"""
        internet_slang = [
            'yyds', '永远的神', '绝绝子', '666', 'nb', '牛批', '牛逼',
            '奥利给', '给力', 'nice', '赞', '好评', '种草', '安利',
            '真香', '爱了', '破防', '破防了', '崩溃', '绝望', '难受'
        ]
        return any(slang in text for slang in internet_slang)

    @staticmethod
    def _calculate_complexity(text: str) -> float:
        """计算文本复杂度

        Returns:
            float: 复杂度得分（0-1）
        """
        if not text:
            return 0.0
        
        # 基于长度的复杂度
        length_score = min(1.0, len(text) / 200)
        
        # 基于句子数量的复杂度
        sentence_count = text.count('。') + text.count('！') + text.count('？') + text.count('!') + text.count('?')
        sentence_score = min(1.0, sentence_count / 5)
        
        # 基于词汇多样性的复杂度
        words = text.split()
        if words:
            unique_words = set(words)
            diversity_score = len(unique_words) / len(words)
        else:
            diversity_score = 0.0
        
        # 综合复杂度得分
        complexity = (length_score * 0.4 + sentence_score * 0.3 + diversity_score * 0.3)
        return complexity


class SmartStrategySelector:
    """智能策略选择器"""

    def __init__(self):
        self.performance_monitor = StrategyPerformanceMonitor()
        self.feature_analyzer = TextFeatureAnalyzer()

    def select_strategy(self, text: str) -> str:
        """根据文本特征选择最优策略

        Args:
            text: 待分析文本

        Returns:
            str: 选择的策略名称
        """
        if not text or not text.strip():
            return "snownlp"  # 空文本使用简单策略

        # 分析文本特征
        features = self.feature_analyzer.analyze(text)
        
        # 获取策略性能数据
        performance = self.performance_monitor.get_strategy_performance()
        
        # 计算各策略得分
        strategy_scores = {}
        for strategy_name in ["snownlp", "llm", "custom_model"]:
            # 基础性能得分
            performance_score = self.performance_monitor.get_strategy_score(strategy_name)
            
            # 根据文本特征调整得分
            feature_score = self._calculate_feature_score(strategy_name, features)
            
            # 综合得分
            strategy_scores[strategy_name] = performance_score * 0.6 + feature_score * 0.4

        # 选择得分最高的策略
        best_strategy = max(strategy_scores, key=strategy_scores.get)
        logger.debug(f"策略选择: {best_strategy}, 得分: {strategy_scores[best_strategy]:.4f}")
        return best_strategy

    def _calculate_feature_score(self, strategy_name: str, features: Dict[str, any]) -> float:
        """根据文本特征计算策略得分

        Args:
            strategy_name: 策略名称
            features: 文本特征

        Returns:
            float: 特征得分（0-1）
        """
        score = 0.5

        if strategy_name == "snownlp":
            # SnowNLP适合短文本、简单结构
            if features["length"] < 100 and features["complexity_score"] < 0.5:
                score = 0.9
            elif features["length"] > 500 or features["complexity_score"] > 0.8:
                score = 0.3

        elif strategy_name == "llm":
            # LLM适合复杂文本、包含emoji、网络用语、讽刺等
            if features["has_emoji"] or features["has_sarcasm"] or features["has_internet_slang"]:
                score = 0.9
            elif features["complexity_score"] > 0.7:
                score = 0.8
            elif features["length"] < 50:
                score = 0.5  # 短文本不需要LLM

        elif strategy_name == "custom_model":
            # 自定义模型适合中等复杂度的文本
            if 0.3 < features["complexity_score"] < 0.8 and 50 <= features["length"] <= 500:
                score = 0.9
            elif features["length"] > 1000:
                score = 0.4  # 过长文本可能效果不好

        return score

    def analyze_with_strategy(self, text: str, strategy_name: str) -> dict:
        """使用指定策略进行分析

        Args:
            text: 待分析文本
            strategy_name: 策略名称

        Returns:
            dict: 分析结果
        """
        start_time = time.time()
        success = True
        result = None

        try:
            # 对于nlp_service，我们使用默认的分析方法
            result = analyze_text_sync(text, strategy_name)
        except Exception as e:
            logger.error(f"策略执行失败 {strategy_name}: {e}")
            success = False
            # 降级到默认分析
            result = analyze_text_sync(text, "custom")

        # 计算执行时间
        latency = time.time() - start_time

        # 记录性能
        # 注意：这里的准确率是模拟的，实际应用中需要根据人工标注或其他方式计算
        accuracy = self._estimate_accuracy(result, text)
        self.performance_monitor.record_performance(strategy_name, latency, success, accuracy)

        return result

    def _estimate_accuracy(self, result: dict, text: str) -> float:
        """估计分析准确率

        Args:
            result: 分析结果
            text: 原始文本

        Returns:
            float: 估计准确率（0-1）
        """
        # 基于文本特征和结果一致性估计准确率
        features = self.feature_analyzer.analyze(text)
        
        # 简单的准确率估计逻辑
        if features["complexity_score"] < 0.3:
            # 简单文本准确率较高
            return 0.9
        elif features["complexity_score"] > 0.7:
            # 复杂文本准确率较低
            return 0.7
        else:
            # 中等复杂度文本
            return 0.8

    def get_strategy_recommendations(self) -> Dict[str, str]:
        """获取策略推荐

        Returns:
            dict: 策略推荐
        """
        performance = self.performance_monitor.get_strategy_performance()
        recommendations = {}

        for strategy_name, data in performance.items():
            avg_time = data.get("total_time", 1.0) / max(data.get("total_calls", 1), 1)
            success_rate = data.get("success_rate", 0.5)
            accuracy = data.get("accuracy", 0.5)

            if success_rate < 0.8:
                recommendations[strategy_name] = "成功率低，建议检查配置"
            elif avg_time > 1.0:
                recommendations[strategy_name] = "响应时间过长，建议优化"
            elif accuracy < 0.8:
                recommendations[strategy_name] = "准确率低，建议重新训练模型"
            else:
                recommendations[strategy_name] = "性能良好"

        return recommendations

    def analyze(self, text: str) -> dict:
        """智能分析文本情感

        Args:
            text: 待分析文本

        Returns:
            dict: 分析结果
        """
        # 选择最优策略
        strategy_name = self.select_strategy(text)
        
        # 使用选择的策略进行分析
        result = self.analyze_with_strategy(text, strategy_name)
        
        # 增强结果，添加策略信息
        result["source"] = f"{strategy_name}_smart"
        
        return result


class AdaptiveStrategyManager:
    """自适应策略管理器"""

    def __init__(self):
        self.selector = SmartStrategySelector()
        self.performance_monitor = self.selector.performance_monitor

    def analyze(self, text: str) -> Dict:
        """执行情感分析

        Args:
            text: 待分析文本

        Returns:
            dict: 分析结果
        """
        result = self.selector.analyze(text)
        return result

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """批量分析文本

        Args:
            texts: 文本列表

        Returns:
            list: 分析结果列表
        """
        results = []
        for text in texts:
            try:
                result = self.analyze(text)
                results.append(result)
            except Exception as e:
                logger.error(f"批量分析失败: {e}")
                # 失败时返回中性结果
                results.append({
                    "score": 0.5,
                    "label": "neutral",
                    "reasoning": "分析失败",
                    "emotion": "未知",
                    "keywords": [],
                    "error": True,
                    "source": "error"
                })
        return results

    def get_performance_stats(self) -> Dict[str, any]:
        """获取性能统计信息

        Returns:
            dict: 性能统计信息
        """
        performance = self.performance_monitor.get_strategy_performance()
        recommendations = self.selector.get_strategy_recommendations()

        stats = {
            "strategies": {},
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }

        for strategy_name, data in performance.items():
            avg_time = data.get("total_time", 1.0) / max(data.get("total_calls", 1), 1)
            stats["strategies"][strategy_name] = {
                "total_calls": data.get("total_calls", 0),
                "average_time": round(avg_time, 4),
                "success_rate": round(data.get("success_rate", 0.0), 4),
                "accuracy": round(data.get("accuracy", 0.0), 4)
            }

        return stats

    def get_health_status(self) -> Dict[str, any]:
        """获取系统健康状态

        Returns:
            dict: 健康状态信息
        """
        performance = self.performance_monitor.get_strategy_performance()
        status = "healthy"
        issues = []

        for strategy_name, data in performance.items():
            success_rate = data.get("success_rate", 0.0)
            avg_time = data.get("total_time", 1.0) / max(data.get("total_calls", 1), 1)

            if success_rate < 0.7:
                issues.append(f"{strategy_name} 成功率过低: {success_rate:.2f}")
                status = "degraded"
            if avg_time > 2.0:
                issues.append(f"{strategy_name} 响应时间过长: {avg_time:.2f}s")
                status = "degraded"

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "issues": issues,
            "strategy_stats": self.get_performance_stats()
        }

"""
模型监控模块
功能：监控模型性能、收集评估指标、提供健康检查
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

logger = logging.getLogger(__name__)


class ModelMonitor:
    """模型监控器"""

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent
        self.metrics_dir = self.model_dir / "metrics"
        self.metrics_dir.mkdir(exist_ok=True)
        self.metrics_file = self.metrics_dir / "model_metrics.json"
        self.request_logs_file = self.metrics_dir / "request_logs.json"
        
        # 确保日志文件存在
        self._ensure_log_files()

    def _ensure_log_files(self):
        """确保日志文件存在"""
        for file_path in [self.metrics_file, self.request_logs_file]:
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)

    def log_prediction(self, text: str, prediction: str, score: float, latency: float):
        """记录预测请求
        
        Args:
            text: 输入文本
            prediction: 预测结果
            score: 预测分数
            latency: 处理延迟（秒）
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "text": text[:100],  # 只记录前100个字符
            "prediction": prediction,
            "score": score,
            "latency": latency,
        }
        
        try:
            with open(self.request_logs_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            logs.append(log_entry)
            # 只保留最近1000条记录
            logs = logs[-1000:]
            
            with open(self.request_logs_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"记录预测请求失败: {e}")

    def evaluate_model(self, test_data: pd.DataFrame, model) -> Dict[str, float]:
        """评估模型性能
        
        Args:
            test_data: 测试数据，包含text和label列
            model: 要评估的模型
            
        Returns:
            dict: 性能指标
        """
        try:
            X_test = test_data["text"]
            y_test = test_data["label"]
            
            # 记录评估开始时间
            start_time = time.time()
            y_pred = model.predict(X_test)
            evaluation_time = time.time() - start_time
            
            # 计算评估指标
            metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "f1_macro": f1_score(y_test, y_pred, average="macro"),
                "f1_positive": f1_score(y_test, y_pred, average="binary", pos_label="positive"),
                "f1_negative": f1_score(y_test, y_pred, average="binary", pos_label="negative"),
                "precision": precision_score(y_test, y_pred, average="macro"),
                "recall": recall_score(y_test, y_pred, average="macro"),
                "evaluation_time": evaluation_time,
                "sample_count": len(test_data),
                "timestamp": datetime.now().isoformat(),
            }
            
            # 保存评估结果
            self._save_metrics(metrics)
            
            return metrics
        except Exception as e:
            logger.error(f"评估模型失败: {e}")
            return {}

    def _save_metrics(self, metrics: Dict[str, float]):
        """保存评估指标"""
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            history.append(metrics)
            # 只保留最近50条记录
            history = history[-50:]
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存评估指标失败: {e}")

    def get_metrics_history(self) -> List[Dict]:
        """获取评估指标历史
        
        Returns:
            list: 评估指标历史记录
        """
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return history
        except Exception as e:
            logger.error(f"读取评估指标历史失败: {e}")
            return []

    def get_request_stats(self) -> Dict[str, any]:
        """获取请求统计信息
        
        Returns:
            dict: 请求统计信息
        """
        try:
            with open(self.request_logs_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            if not logs:
                return {
                    "total_requests": 0,
                    "average_latency": 0,
                    "predictions": {},
                    "recent_requests": []
                }
            
            # 计算统计信息
            total_requests = len(logs)
            average_latency = sum(log.get("latency", 0) for log in logs) / total_requests
            
            # 预测分布
            predictions = {}
            for log in logs:
                pred = log.get("prediction", "unknown")
                predictions[pred] = predictions.get(pred, 0) + 1
            
            # 最近10条请求
            recent_requests = logs[-10:]
            
            return {
                "total_requests": total_requests,
                "average_latency": average_latency,
                "predictions": predictions,
                "recent_requests": recent_requests
            }
        except Exception as e:
            logger.error(f"获取请求统计信息失败: {e}")
            return {}

    def check_model_health(self) -> Dict[str, any]:
        """检查模型健康状态
        
        Returns:
            dict: 健康状态信息
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "issues": []
        }
        
        # 检查评估指标
        metrics_history = self.get_metrics_history()
        if metrics_history:
            recent_metrics = metrics_history[-1]
            health_status["metrics"] = recent_metrics
            
            # 检查性能是否下降
            if len(metrics_history) >= 2:
                previous_metrics = metrics_history[-2]
                f1_current = recent_metrics.get("f1_macro", 0)
                f1_previous = previous_metrics.get("f1_macro", 0)
                
                if f1_current < f1_previous * 0.9:
                    health_status["issues"].append("模型性能下降超过10%")
                    health_status["status"] = "degraded"
        else:
            health_status["issues"].append("缺少评估指标")
            health_status["status"] = "unknown"
        
        # 检查请求统计
        request_stats = self.get_request_stats()
        if request_stats.get("total_requests", 0) > 0:
            avg_latency = request_stats.get("average_latency", 0)
            if avg_latency > 1.0:
                health_status["issues"].append("平均响应时间超过1秒")
                health_status["status"] = "degraded"
        
        return health_status

    def get_performance_trend(self, metric: str = "f1_macro", days: int = 7) -> List[Dict]:
        """获取性能趋势
        
        Args:
            metric: 要查看的指标
            days: 查看的天数
            
        Returns:
            list: 性能趋势数据
        """
        metrics_history = self.get_metrics_history()
        trend_data = []
        
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        
        for metrics in metrics_history:
            timestamp = metrics.get("timestamp")
            if timestamp:
                metric_time = datetime.fromisoformat(timestamp).timestamp()
                if metric_time >= cutoff_time:
                    trend_data.append({
                        "timestamp": timestamp,
                        "value": metrics.get(metric, 0)
                    })
        
        return trend_data


def monitor_prediction(model, text: str) -> Dict[str, any]:
    """监控模型预测
    
    Args:
        model: 模型实例
        text: 输入文本
        
    Returns:
        dict: 预测结果和监控信息
    """
    monitor = ModelMonitor()
    
    # 记录开始时间
    start_time = time.time()
    
    # 执行预测
    try:
        prediction = model.predict([text])[0]
        
        # 获取概率（如果支持）
        score = 0.5
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba([text])[0]
            score = float(max(probs))
        
        # 计算延迟
        latency = time.time() - start_time
        
        # 记录预测
        monitor.log_prediction(text, prediction, score, latency)
        
        return {
            "prediction": prediction,
            "score": score,
            "latency": latency,
            "status": "success"
        }
    except Exception as e:
        latency = time.time() - start_time
        monitor.log_prediction(text, "error", 0.0, latency)
        return {
            "prediction": "error",
            "score": 0.0,
            "latency": latency,
            "status": "error",
            "error": str(e)
        }

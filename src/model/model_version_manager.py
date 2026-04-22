"""
模型版本管理模块
功能：管理模型版本、自动更新和性能监控
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import pandas as pd
from sklearn.metrics import f1_score

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """模型版本管理器"""

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent
        self.versions_dir = self.model_dir / "versions"
        self.versions_dir.mkdir(exist_ok=True)
        self.current_version_path = self.model_dir / "current_version.json"
        self.performance_history = self.model_dir / "performance_history.json"
        
        # 确保历史记录文件存在
        if not self.performance_history.exists():
            with open(self.performance_history, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _get_version_name(self) -> str:
        """生成版本名称"""
        return datetime.now().strftime("v%Y%m%d_%H%M%S")

    def save_model_version(self, model, performance: Dict[str, float], metadata: Dict = None) -> str:
        """保存模型版本
        
        Args:
            model: 训练好的模型
            performance: 模型性能指标
            metadata: 模型元数据
            
        Returns:
            str: 版本名称
        """
        version_name = self._get_version_name()
        version_dir = self.versions_dir / version_name
        version_dir.mkdir(exist_ok=True)
        
        # 保存模型
        model_path = version_dir / "model.pkl"
        joblib.dump(model, model_path)
        
        # 保存元数据
        metadata = metadata or {}
        metadata.update({
            "version": version_name,
            "performance": performance,
            "created_at": datetime.now().isoformat(),
            "model_path": str(model_path),
        })
        
        metadata_path = version_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 更新性能历史
        self._update_performance_history(version_name, performance)
        
        logger.info(f"模型版本 {version_name} 已保存")
        return version_name

    def _update_performance_history(self, version_name: str, performance: Dict[str, float]):
        """更新性能历史"""
        with open(self.performance_history, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        history.append({
            "version": version_name,
            "performance": performance,
            "timestamp": datetime.now().isoformat(),
        })
        
        # 只保留最近20个记录
        history = history[-20:]
        
        with open(self.performance_history, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def list_versions(self) -> List[Dict]:
        """列出所有模型版本"""
        versions = []
        
        for version_dir in sorted(self.versions_dir.iterdir(), reverse=True):
            if version_dir.is_dir():
                metadata_path = version_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        versions.append(metadata)
                    except Exception as e:
                        logger.error(f"读取版本 {version_dir.name} 元数据失败: {e}")
        
        return versions

    def get_current_version(self) -> Optional[str]:
        """获取当前使用的模型版本"""
        if self.current_version_path.exists():
            try:
                with open(self.current_version_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('version')
            except Exception as e:
                logger.error(f"读取当前版本失败: {e}")
        return None

    def set_current_version(self, version_name: str) -> bool:
        """设置当前使用的模型版本
        
        Args:
            version_name: 版本名称
            
        Returns:
            bool: 是否设置成功
        """
        version_dir = self.versions_dir / version_name
        if not version_dir.exists():
            logger.error(f"版本 {version_name} 不存在")
            return False
        
        # 复制模型到主路径
        src_model = version_dir / "model.pkl"
        dst_model = self.model_dir / "best_sentiment_model.pkl"
        
        try:
            shutil.copy2(src_model, dst_model)
            
            # 更新当前版本记录
            with open(self.current_version_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "version": version_name,
                    "updated_at": datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"当前模型版本已切换到 {version_name}")
            return True
        except Exception as e:
            logger.error(f"切换模型版本失败: {e}")
            return False

    def rollback_to_version(self, version_name: str) -> bool:
        """回滚到指定版本"""
        return self.set_current_version(version_name)

    def get_best_version(self, metric: str = "f1_macro") -> Optional[str]:
        """获取性能最佳的模型版本
        
        Args:
            metric: 评估指标
            
        Returns:
            str: 最佳版本名称
        """
        versions = self.list_versions()
        if not versions:
            return None
        
        best_version = None
        best_score = -1
        
        for version in versions:
            score = version.get("performance", {}).get(metric, 0)
            if score > best_score:
                best_score = score
                best_version = version.get("version")
        
        return best_version

    def check_model_performance(self, test_data: pd.DataFrame) -> Dict[str, float]:
        """检查当前模型性能
        
        Args:
            test_data: 测试数据，包含text和label列
            
        Returns:
            dict: 性能指标
        """
        model_path = self.model_dir / "best_sentiment_model.pkl"
        if not model_path.exists():
            logger.error("模型文件不存在")
            return {}
        
        try:
            model = joblib.load(model_path)
            X_test = test_data["text"]
            y_test = test_data["label"]
            
            y_pred = model.predict(X_test)
            
            performance = {
                "accuracy": (y_pred == y_test).mean(),
                "f1_macro": f1_score(y_test, y_pred, average="macro"),
                "f1_positive": f1_score(y_test, y_pred, average="binary", pos_label="positive"),
                "f1_negative": f1_score(y_test, y_pred, average="binary", pos_label="negative"),
                "sample_count": len(test_data),
            }
            
            return performance
        except Exception as e:
            logger.error(f"检查模型性能失败: {e}")
            return {}

    def should_update_model(self, current_performance: Dict[str, float], threshold: float = 0.1) -> bool:
        """判断是否需要更新模型
        
        Args:
            current_performance: 当前模型性能
            threshold: 性能下降阈值
            
        Returns:
            bool: 是否需要更新
        """
        # 获取历史性能
        with open(self.performance_history, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        if len(history) < 2:
            return False
        
        # 比较最近两次的性能
        recent_performance = history[-1]["performance"]
        previous_performance = history[-2]["performance"]
        
        # 检查关键指标是否下降
        key_metrics = ["f1_macro", "accuracy"]
        for metric in key_metrics:
            if metric in current_performance and metric in previous_performance:
                current = current_performance[metric]
                previous = previous_performance[metric]
                if current < previous * (1 - threshold):
                    logger.warning(f"模型性能下降: {metric} 从 {previous:.4f} 下降到 {current:.4f}")
                    return True
        
        return False

    def cleanup_old_versions(self, keep: int = 5):
        """清理旧版本模型
        
        Args:
            keep: 保留的版本数量
        """
        versions = sorted(self.versions_dir.iterdir(), reverse=True)
        versions_to_delete = versions[keep:]
        
        for version_dir in versions_to_delete:
            if version_dir.is_dir():
                try:
                    shutil.rmtree(version_dir)
                    logger.info(f"已删除旧版本: {version_dir.name}")
                except Exception as e:
                    logger.error(f"删除旧版本 {version_dir.name} 失败: {e}")


def load_model_with_versioning(model_dir: str = None) -> Tuple[Optional[any], Dict]:
    """加载模型，支持版本管理
    
    Args:
        model_dir: 模型目录
        
    Returns:
        tuple: (模型, 元数据)
    """
    mvm = ModelVersionManager(model_dir)
    model_path = Path(model_dir or "") / "best_sentiment_model.pkl"
    
    if not model_path.exists():
        logger.error("模型文件不存在")
        return None, {}
    
    try:
        model = joblib.load(model_path)
        current_version = mvm.get_current_version()
        
        metadata = {
            "loaded": True,
            "current_version": current_version,
            "model_path": str(model_path),
            "loaded_at": datetime.now().isoformat(),
        }
        
        return model, metadata
    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        return None, {"error": str(e)}

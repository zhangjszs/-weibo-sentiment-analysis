#!/usr/bin/env python3
"""
模型超参数优化模块
功能：使用GridSearchCV和Optuna进行超参数调优
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)
from sklearn.model_selection import (
    GridSearchCV,
    RandomizedSearchCV,
    StratifiedKFold,
    train_test_split,
)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

logger = logging.getLogger(__name__)


def parse_ngram_range(value: str) -> tuple[int, int]:
    options = {
        "(1,1)": (1, 1),
        "(1,2)": (1, 2),
        "(1,3)": (1, 3),
    }
    return options.get(value, (1, 1))


try:
    import optuna

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna未安装，将使用GridSearchCV进行优化")


def load_data(csv_path: str | Path) -> pd.DataFrame:
    """读取csv为DataFrame"""
    return (
        pd.read_csv(csv_path, header=None, names=["text", "label"])
        .dropna(subset=["text", "label"])
        .drop_duplicates()
        .reset_index(drop=True)
    )


class HyperparameterOptimizer:
    """超参数优化器"""

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent
        self.best_params = {}
        self.best_score = 0
        self.best_model_name = None
        self.optimization_history = []

        self.param_grids = {
            "NaiveBayes": {
                "tfidf__max_features": [3000, 5000, 7000],
                "tfidf__ngram_range": [(1, 1), (1, 2), (1, 3)],
                "tfidf__min_df": [1, 2, 3],
                "clf__alpha": [0.1, 0.5, 1.0, 2.0],
            },
            "LogReg": {
                "tfidf__max_features": [3000, 5000, 7000],
                "tfidf__ngram_range": [(1, 1), (1, 2)],
                "clf__C": [0.1, 0.5, 1.0, 2.0, 5.0],
                "clf__max_iter": [500, 1000],
            },
            "LinearSVM": {
                "tfidf__max_features": [3000, 5000, 7000],
                "tfidf__ngram_range": [(1, 1), (1, 2)],
                "clf__C": [0.1, 0.5, 1.0, 2.0],
            },
            "RandomForest": {
                "tfidf__max_features": [3000, 5000],
                "tfidf__ngram_range": [(1, 1), (1, 2)],
                "clf__n_estimators": [100, 200, 300],
                "clf__max_depth": [10, 20, 30, None],
            },
        }

        self.base_models = {
            "NaiveBayes": MultinomialNB(),
            "LogReg": LogisticRegression(class_weight="balanced"),
            "LinearSVM": LinearSVC(class_weight="balanced"),
            "RandomForest": RandomForestClassifier(
                n_jobs=-1, random_state=42, class_weight="balanced"
            ),
        }

    def build_pipeline(self, model_name: str) -> Pipeline:
        """构建模型流水线"""
        return Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer()),
                ("clf", self.base_models[model_name]),
            ]
        )

    def grid_search_optimize(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_names: list = None,
        cv_folds: int = 5,
        scoring: str = "f1_macro",
        n_jobs: int = -1,
    ) -> Dict[str, Any]:
        """
        使用GridSearchCV进行超参数优化

        Args:
            X_train: 训练数据
            y_train: 训练标签
            model_names: 要优化的模型列表
            cv_folds: 交叉验证折数
            scoring: 评估指标
            n_jobs: 并行数

        Returns:
            dict: 优化结果
        """
        if model_names is None:
            model_names = list(self.base_models.keys())

        results = {}
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)

        for model_name in model_names:
            logger.info(f"正在优化 {model_name}...")

            try:
                pipeline = self.build_pipeline(model_name)
                param_grid = self.param_grids.get(model_name, {})

                if not param_grid:
                    logger.warning(f"{model_name} 没有定义参数网格，跳过")
                    continue

                grid_search = GridSearchCV(
                    pipeline,
                    param_grid,
                    cv=cv,
                    scoring=scoring,
                    n_jobs=n_jobs,
                    verbose=1,
                    refit=True,
                )

                grid_search.fit(X_train, y_train)

                results[model_name] = {
                    "best_params": grid_search.best_params_,
                    "best_score": grid_search.best_score_,
                    "best_estimator": grid_search.best_estimator_,
                }

                self.optimization_history.append(
                    {
                        "model": model_name,
                        "method": "GridSearchCV",
                        "score": grid_search.best_score_,
                        "params": grid_search.best_params_,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                logger.info(f"{model_name} 最佳得分: {grid_search.best_score_:.4f}")
                logger.info(f"{model_name} 最佳参数: {grid_search.best_params_}")

            except Exception as e:
                logger.error(f"优化 {model_name} 失败: {e}")
                results[model_name] = {"error": str(e)}

        return results

    def random_search_optimize(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_names: list = None,
        n_iter: int = 20,
        cv_folds: int = 5,
        scoring: str = "f1_macro",
        n_jobs: int = -1,
    ) -> Dict[str, Any]:
        """
        使用RandomizedSearchCV进行超参数优化（更快）
        """
        if model_names is None:
            model_names = list(self.base_models.keys())

        results = {}
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)

        for model_name in model_names:
            logger.info(f"正在优化 {model_name} (RandomSearch)...")

            try:
                pipeline = self.build_pipeline(model_name)
                param_grid = self.param_grids.get(model_name, {})

                if not param_grid:
                    continue

                random_search = RandomizedSearchCV(
                    pipeline,
                    param_grid,
                    n_iter=n_iter,
                    cv=cv,
                    scoring=scoring,
                    n_jobs=n_jobs,
                    verbose=1,
                    random_state=42,
                    refit=True,
                )

                random_search.fit(X_train, y_train)

                results[model_name] = {
                    "best_params": random_search.best_params_,
                    "best_score": random_search.best_score_,
                    "best_estimator": random_search.best_estimator_,
                }

                logger.info(f"{model_name} 最佳得分: {random_search.best_score_:.4f}")

            except Exception as e:
                logger.error(f"优化 {model_name} 失败: {e}")
                results[model_name] = {"error": str(e)}

        return results

    def optuna_optimize(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        n_trials: int = 50,
        timeout: int = 600,
    ) -> Dict[str, Any]:
        """
        使用Optuna进行贝叶斯优化（需要安装optuna）
        """
        if not OPTUNA_AVAILABLE:
            logger.error("Optuna未安装，请使用 pip install optuna 安装")
            return {"error": "Optuna not available"}

        def objective(trial):
            model_name = trial.suggest_categorical(
                "model", ["NaiveBayes", "LogReg", "LinearSVM"]
            )

            max_features = trial.suggest_int("max_features", 2000, 8000)
            ngram_range = trial.suggest_categorical(
                "ngram_range", ["(1,1)", "(1,2)", "(1,3)"]
            )
            ngram_tuple = parse_ngram_range(ngram_range)

            pipeline = self.build_pipeline(model_name)
            pipeline.set_params(
                tfidf__max_features=max_features,
                tfidf__ngram_range=ngram_tuple,
            )

            if model_name == "NaiveBayes":
                alpha = trial.suggest_float("alpha", 0.01, 2.0, log=True)
                pipeline.set_params(clf__alpha=alpha)
            elif model_name == "LogReg":
                C = trial.suggest_float("C", 0.01, 10.0, log=True)
                pipeline.set_params(clf__C=C)
            elif model_name == "LinearSVM":
                C = trial.suggest_float("C_svm", 0.01, 10.0, log=True)
                pipeline.set_params(clf__C=C)

            cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
            scores = []

            for train_idx, val_idx in cv.split(X_train, y_train):
                X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
                y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

                pipeline.fit(X_tr, y_tr)
                pred = pipeline.predict(X_val)
                scores.append(f1_score(y_val, pred, average="macro"))

            return np.mean(scores)

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, timeout=timeout)

        return {
            "best_value": study.best_value,
            "best_params": study.best_params,
            "best_trial": study.best_trial.number,
        }

    def select_best_model(
        self, results: Dict[str, Any], X_test: np.ndarray, y_test: np.ndarray
    ) -> Tuple[str, Any, float]:
        """
        从优化结果中选择最佳模型
        """
        best_model_name = None
        best_estimator = None
        best_test_score = 0

        for model_name, result in results.items():
            if "error" in result:
                continue

            estimator = result.get("best_estimator")
            if estimator is None:
                continue

            y_pred = estimator.predict(X_test)
            test_score = f1_score(y_test, y_pred, average="macro")

            if test_score > best_test_score:
                best_test_score = test_score
                best_model_name = model_name
                best_estimator = estimator

        self.best_model_name = best_model_name
        self.best_score = best_test_score

        return best_model_name, best_estimator, best_test_score

    def save_best_model(self, estimator, model_name: str = None) -> bool:
        """保存最佳模型"""
        import joblib

        try:
            model_name = model_name or self.best_model_name or "best_model"
            output_path = self.model_dir / "best_sentiment_model.pkl"

            joblib.dump(estimator, output_path)

            meta_path = self.model_dir / "model_metadata.json"
            import json

            metadata = {
                "model_name": model_name,
                "score": self.best_score,
                "saved_at": datetime.now().isoformat(),
                "optimization_history": self.optimization_history[-5:],
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"模型已保存: {output_path}")
            return True

        except Exception as e:
            logger.error(f"保存模型失败: {e}")
            return False

    def run_full_optimization(
        self,
        data_path: str = None,
        method: str = "random",
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """
        运行完整的优化流程

        Args:
            data_path: 数据文件路径
            method: 优化方法
            test_size: 测试集比例

        Returns:
            dict: 优化结果
        """
        logger.info(f"开始超参数优化, method={method}")

        data_path = data_path or self.model_dir / "target.csv"
        df = load_data(data_path)

        logger.info(f"加载数据: {len(df)} 条")

        X = df["text"]
        y = df["label"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=42
        )

        if method == "grid":
            results = self.grid_search_optimize(X_train, y_train)
        elif method == "random":
            results = self.random_search_optimize(X_train, y_train, n_iter=15)
        elif method == "optuna" and OPTUNA_AVAILABLE:
            results = self.optuna_optimize(X_train, y_train)
        else:
            results = self.random_search_optimize(X_train, y_train, n_iter=10)

        best_name, best_estimator, best_score = self.select_best_model(
            results, X_test, y_test
        )

        if best_estimator:
            self.save_best_model(best_estimator, best_name)

            y_pred = best_estimator.predict(X_test)
            report = classification_report(y_test, y_pred, output_dict=True)

            results["summary"] = {
                "best_model": best_name,
                "test_f1_score": best_score,
                "test_accuracy": accuracy_score(y_test, y_pred),
                "classification_report": report,
            }

        return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="模型超参数优化")
    parser.add_argument(
        "--method",
        choices=["grid", "random", "optuna"],
        default="random",
        help="优化方法",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="训练数据路径",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=30,
        help="Optuna试验次数",
    )

    args = parser.parse_args()

    optimizer = HyperparameterOptimizer()
    results = optimizer.run_full_optimization(
        data_path=args.data,
        method=args.method,
    )

    if "summary" in results:
        print("\n" + "=" * 50)
        print("优化结果摘要")
        print("=" * 50)
        print(f"最佳模型: {results['summary']['best_model']}")
        print(f"测试F1分数: {results['summary']['test_f1_score']:.4f}")
        print(f"测试准确率: {results['summary']['test_accuracy']:.4f}")

    return results


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""下载 Erlangshen-Roberta-110M-Sentiment 并导出为 ONNX 格式。

Phase 3.4：BertBackend 推理所需的模型产物由本脚本生成。

用法
----
    # 默认下载到 src/model/bert_sentiment_onnx/
    python scripts/download_bert_model.py

    # 自定义模型与输出路径（环境变量）
    BERT_MODEL_NAME=IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment \
    BERT_MODEL_PATH=src/model/bert_sentiment_onnx \
    python scripts/download_bert_model.py

产物
----
输出目录下包含：
- ``model.onnx``：ONNX Runtime 可直接加载的图
- ``tokenizer.json`` / ``vocab.txt`` / ``tokenizer_config.json``：tokenizer 文件
- ``config.json``：模型配置（含 id2label）
- ``special_tokens_map.json``

依赖
----
- transformers
- optimum[onnxruntime]
- torch（CPU 即可）
- sentencepiece（Erlangshen 系列需要）

如首次安装 torch CPU 版本：
    pip install torch --index-url https://download.pytorch.org/whl/cpu
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# 把 src 加入 sys.path 以读取 Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from config.settings import Config
except ImportError:  # pragma: no cover - 允许无 Config 时退化到环境变量
    Config = None  # type: ignore


def _resolve_paths() -> tuple[str, str]:
    if Config is not None:
        model_name = os.getenv("BERT_MODEL_NAME", Config.BERT_MODEL_NAME)
        out_dir = os.getenv("BERT_MODEL_PATH", Config.BERT_MODEL_PATH)
    else:
        model_name = os.getenv(
            "BERT_MODEL_NAME", "IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment"
        )
        out_dir = os.getenv(
            "BERT_MODEL_PATH",
            str(PROJECT_ROOT / "src" / "model" / "bert_sentiment_onnx"),
        )
    return model_name, out_dir


def main() -> int:
    try:
        from transformers import AutoTokenizer
        from optimum.onnxruntime import ORTModelForSequenceClassification
    except ImportError as e:
        print(
            f"缺少依赖: {e}。请先安装: "
            "pip install transformers optimum[onnxruntime] torch sentencepiece",
            file=sys.stderr,
        )
        return 2

    model_name, out_dir = _resolve_paths()
    print(f"[download_bert_model] 模型: {model_name}")
    print(f"[download_bert_model] 输出: {out_dir}")

    Path(out_dir).mkdir(parents=True, exist_ok=True)

    print("[download_bert_model] 下载 tokenizer ...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    print("[download_bert_model] 下载模型并导出 ONNX（首次约 400MB）...")
    model = ORTModelForSequenceClassification.from_pretrained(model_name, export=True)

    print(f"[download_bert_model] 保存到 {out_dir} ...")
    tokenizer.save_pretrained(out_dir)
    model.save_pretrained(out_dir)

    # 校验产物
    expected_files = ["model.onnx", "tokenizer_config.json", "config.json"]
    missing = [f for f in expected_files if not (Path(out_dir) / f).exists()]
    if missing:
        print(f"[download_bert_model] 警告: 缺失文件 {missing}", file=sys.stderr)
        return 1

    print("[download_bert_model] 完成。")
    print(f"  backend: optimum.onnxruntime.ORTModelForSequenceClassification")
    print(f"  id2label: {model.config.id2label}")
    print(f"  设置 SENTIMENT_BACKEND=bert 即可启用 BERT 推理。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

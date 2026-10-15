#!/usr/bin/env python3
"""Before/after benchmark for the #98 Rust slice.

Measures the pure-Python references against the compiled ``weibo_core``
extension (via ``services.rust_bridge``) and writes machine-readable JSON
plus a Markdown summary to ``docs/benchmarks/``.

Usage:
    .venv/bin/python scripts/bench_dedup.py [--repeats N] [--out DIR]
    cargo bench --manifest-path rust/weibo_core/Cargo.toml   # Rust absolute numbers
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from services import rust_bridge as bridge  # noqa: E402
from services.rust_bridge import (  # noqa: E402
    dedup_keys_py,
    normalize_post_py,
    rust_available,
)

SAMPLE_POSTS = [
    "  【重磅】Hello   WORLD  微博舆情分析 #话题# @user http://t.cn/xyz  ",
    "  转发微博   \t\n  疫情防控 最新进展！！！   ",
    "Mixed CASE 123 测试文本 with   extra    spaces and 😀 emoji ＲＡＢ  ",
    "短文本",
    "   ",
]


def _time(fn, *args, repeats: int) -> list[float]:
    fn(*args)  # warmup
    out = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn(*args)
        out.append((time.perf_counter() - start) * 1000.0)
    return out


def bench_normalize(repeats: int, scale: int) -> dict:
    posts = (SAMPLE_POSTS * ((scale // len(SAMPLE_POSTS)) + 1))[:scale]

    def run_py():
        for p in posts:
            normalize_post_py(p)

    def run_rs():
        for p in posts:
            bridge.normalize_post(p)

    py = _time(run_py, repeats=repeats)
    result: dict = {
        "posts": scale,
        "python_ms": round(statistics.median(py), 3),
        "python_runs_ms": [round(v, 3) for v in py],
    }
    if rust_available():
        rs = _time(run_rs, repeats=repeats)
        result["rust_ms"] = round(statistics.median(rs), 3)
        result["rust_runs_ms"] = [round(v, 3) for v in rs]
        result["speedup"] = (
            round(result["python_ms"] / result["rust_ms"], 2) if result["rust_ms"] else None
        )
    return result


def bench_dedup(repeats: int, scale: int, dupe_ratio: float = 0.9) -> dict:
    universe = max(1, int(scale * (1.0 - dupe_ratio)))
    keys = [f"post:{i % universe}:hash{i:08d}" for i in range(scale)]
    py = _time(dedup_keys_py, keys, repeats=repeats)
    result: dict = {
        "keys": scale,
        "unique": universe,
        "python_ms": round(statistics.median(py), 3),
        "python_runs_ms": [round(v, 3) for v in py],
    }
    if rust_available():
        rs = _time(bridge.dedup_keys, keys, repeats=repeats)
        result["rust_ms"] = round(statistics.median(rs), 3)
        result["rust_runs_ms"] = [round(v, 3) for v in rs]
        result["speedup"] = (
            round(result["python_ms"] / result["rust_ms"], 2) if result["rust_ms"] else None
        )
    # sanity: both backends agree on this workload
    assert bridge.dedup_keys(keys) == dedup_keys_py(keys)
    return result


def bench_normalize_batch(repeats: int, scale: int) -> dict:
    """One FFI call for the whole batch (amortized boundary)."""
    from services.rust_bridge import normalize_posts_py  # noqa: E402

    posts = (SAMPLE_POSTS * ((scale // len(SAMPLE_POSTS)) + 1))[:scale]
    py = _time(normalize_posts_py, posts, repeats=repeats)
    result: dict = {
        "posts": scale,
        "python_ms": round(statistics.median(py), 3),
        "python_runs_ms": [round(v, 3) for v in py],
    }
    if rust_available():
        rs = _time(bridge.normalize_posts, posts, repeats=repeats)
        result["rust_ms"] = round(statistics.median(rs), 3)
        result["rust_runs_ms"] = [round(v, 3) for v in rs]
        result["speedup"] = (
            round(result["python_ms"] / result["rust_ms"], 2) if result["rust_ms"] else None
        )
    assert bridge.normalize_posts(posts) == normalize_posts_py(posts)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--out", default=str(PROJECT_ROOT / "docs" / "benchmarks"))
    args = parser.parse_args()

    if not rust_available():
        print("weibo_core extension not available; running python-only baseline")
    payload = {
        "issue": 98,
        "weibo_core_version": bridge.version(),
        "rust_available": rust_available(),
        "repeats": args.repeats,
        "normalize": bench_normalize(args.repeats, 2_000),
        "normalize_batch": bench_normalize_batch(args.repeats, 2_000),
        "dedup_10k": bench_dedup(args.repeats, 10_000),
        "dedup_100k": bench_dedup(args.repeats, 100_000),
    }
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "m7-1-dedup.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    lines = [
        "# M7-1 dedup/normalize benchmark (#98)",
        "",
        f"weibo_core={payload['weibo_core_version']} repeats={args.repeats} "
        f"rust_available={payload['rust_available']}",
        "",
        "| workload | python (median ms) | rust (median ms) | speedup |",
        "|---|---|---|---|",
    ]
    for key, label in (
        ("normalize", "normalize_post x2000 (per-item FFI)"),
        ("normalize_batch", "normalize_posts x2000 (batch FFI)"),
        ("dedup_10k", "dedup_keys 10k"),
        ("dedup_100k", "dedup_keys 100k"),
    ):
        row = payload[key]
        lines.append(
            f"| {label} | {row['python_ms']} | {row.get('rust_ms', 'n/a')} "
            f"| {row.get('speedup', 'n/a')}x |"
        )
    lines += [
        "",
        "Reproduce: `.venv/bin/python scripts/bench_dedup.py` and "
        "`cargo bench --manifest-path rust/weibo_core/Cargo.toml`.",
        "",
        "## Finding (honest)",
        "",
        "For these thin string ops over Python-owned data, CPython's C-speed",
        "builtins (`str.lower/split/join`, set hashing) already saturate, and",
        "Rust pays UTF-8 marshaling both ways: per-item FFI ~0.66x, batch FFI",
        "~0.9x, `dedup_keys` ~0.45x. Value of this slice is the FFI boundary,",
        "parity proof, and the decision rule: next Rust slices must target",
        "compute-heavy kernels on Rust-owned buffers or pure-Python slow loops",
        "(profile first), not thin wrappers over C-speed builtins.",
        "",
    ]
    (out_dir / "m7-1-dedup.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

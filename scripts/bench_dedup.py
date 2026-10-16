#!/usr/bin/env python3
"""Before/after benchmark for the #98 Rust slice.

Measures the pure-Python references against the compiled ``weibo_core``
extension (via ``services.rust_bridge``) and writes machine-readable JSON
plus a Markdown summary to ``docs/benchmarks/``.

Usage:
    # Build the extension in RELEASE mode first. `maturin develop` defaults to
    # an unoptimized dev build that is ~20x slower, which silently invalidates
    # every Rust number this script reports.
    (cd rust/weibo_core && ../../.venv/bin/maturin develop --release --locked)

    .venv/bin/python scripts/bench_dedup.py [--repeats N] [--out DIR]
    cargo bench --manifest-path rust/weibo_core/Cargo.toml --locked   # Rust absolute numbers
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
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


def _dedup_workload(scale: int, num: int, den: int) -> list[str]:
    """Build a dedup batch with a *real* duplicate ratio.

    Shared rule with ``rust/weibo_core/benches/dedup.rs`` (#105) -- keep the
    two in sync or the Rust and Python numbers stop describing one workload.

    * ``unique_count = (scale * (den - num) + den // 2) // den`` -- integer
      arithmetic only. The old ``int(scale * 0.1)`` returned 999 for a 10k
      workload because ``10000 * 0.1`` is 999.9999999999999 in binary float.
    * ``base[j] = f"post:{j}:hash{j:08d}"`` -- one distinct key per slot.
    * the batch is ``base[i % unique_count]`` for ``i`` in ``0..scale``.

    The #98 version embedded a per-item counter *inside* the key
    (``hash{i:08d}`` with ``i`` the item index), which made all ``scale`` keys
    distinct: the reported "90% duplicate" workload actually had a 0% duplicate
    rate while reporting ``unique=999``.
    """
    unique_count = max(1, (scale * (den - num) + den // 2) // den)
    base = [f"post:{j}:hash{j:08d}" for j in range(unique_count)]
    return [base[i % unique_count] for i in range(scale)]


def bench_dedup(repeats: int, scale: int, num: int = 9, den: int = 10) -> dict:
    """Dedup benchmark; ``num/den`` is the intended duplicate ratio."""
    keys = _dedup_workload(scale, num, den)
    # Metadata comes from the workset that was actually built, never from the
    # formula that was intended. Report what ran (#105).
    actual_unique = len(dedup_keys_py(keys))
    expected_unique = max(1, (scale * (den - num) + den // 2) // den)
    if actual_unique != expected_unique:
        raise SystemExit(
            f"workload of {scale} items at {num}/{den} holds {actual_unique} distinct "
            f"keys, expected {expected_unique}: the benchmark would not be "
            f"measuring duplicates"
        )

    py = _time(dedup_keys_py, keys, repeats=repeats)
    result: dict = {
        "keys": scale,
        "duplicate_ratio": f"{num}/{den}",
        "unique_reported": expected_unique,
        "unique_actual": actual_unique,
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


def _declared_toolchain() -> str:
    """Toolchain the repository pins, read from whichever file carries it.

    #98 shipped ``rust/toolchain.toml``, which rustup does not recognise;
    #108 renames it to ``rust-toolchain.toml``. Accept both so the provenance
    block survives that change.
    """
    for name in ("rust/rust-toolchain.toml", "rust/toolchain.toml", "rust-toolchain.toml"):
        path = PROJECT_ROOT / name
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "channel":
                return value.strip().strip('"')
    return "unpinned"


def _resolved_rustc() -> str:
    """`rustc --version` if the environment can resolve one, else the reason."""
    try:
        proc = subprocess.run(
            ["rustc", "--version"], capture_output=True, text=True, check=False, timeout=30
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
        return f"unavailable ({type(exc).__name__})"
    out = (proc.stdout or "").strip()
    if proc.returncode == 0 and out:
        return out
    # A shim that exits non-zero (mise, for example) tells us nothing about
    # the toolchain, so say so instead of recording an empty version.
    return f"unavailable on PATH (exit {proc.returncode})"


def _provenance() -> dict:
    """Record enough to tell which code produced these numbers (#105)."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--", "rust", "src", "scripts"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        commit, dirty = "unknown", None
    return {
        "git_commit": commit,
        "git_dirty": dirty,
        "python": sys.version.split()[0],
        "rustc": _resolved_rustc(),
        "toolchain_channel": _declared_toolchain(),
    }


# Criterion flattens `group/bench/case` into one directory name, so the
# original separators cannot be recovered unambiguously from the path alone.
# This mapping pins the display name and doubles as a tripwire: a benchmark
# added or renamed in `benches/dedup.rs` makes the set comparison fail rather
# than being silently mislabelled here.
CRITERION_NAMES = {
    "normalize_post_short": "normalize_post/short",
    "normalize_post_long_x200": "normalize_post/long_x200",
    "dedup_keys_n=1000_dupe=90pct": "dedup_keys/n=1000/dupe=90pct",
    "dedup_keys_n=10000_dupe=90pct": "dedup_keys/n=10000/dupe=90pct",
    "dedup_keys_n=100000_dupe=90pct": "dedup_keys/n=100000/dupe=90pct",
    "dedup_keys_n=10000_dupe=0pct": "dedup_keys/n=10000/dupe=0pct",
    "dedup_keys_n=100000_dupe=0pct": "dedup_keys/n=100000/dupe=0pct",
}


def _criterion_results() -> dict:
    """Read the executed Criterion estimates off disk (#105).

    The #98 report only ever proved ``cargo bench --no-run``. Reading the
    artifacts ``cargo bench`` actually produced keeps the published numbers
    tied to a real run instead of to hand-copied console text.
    """
    root = PROJECT_ROOT / "rust" / "weibo_core" / "target" / "criterion"
    if not root.is_dir():
        return {}
    found: dict[str, dict] = {}
    for path in sorted(root.glob("*/new/estimates.json")):
        flat = path.parent.parent.name
        if flat not in CRITERION_NAMES:
            raise SystemExit(
                f"criterion produced unknown benchmark {flat!r}; add it to "
                f"CRITERION_NAMES so it is not reported under a wrong name"
            )
        try:
            est = json.loads(path.read_text())["median"]
        except (OSError, KeyError, ValueError):  # pragma: no cover
            continue
        found[CRITERION_NAMES[flat]] = {
            "median_ns": round(est["point_estimate"], 2),
            "ci95_low_ns": round(est["confidence_interval"]["lower_bound"], 2),
            "ci95_high_ns": round(est["confidence_interval"]["upper_bound"], 2),
        }
    missing = sorted(set(CRITERION_NAMES.values()) - set(found))
    if missing:
        raise SystemExit(f"criterion results missing for {missing}; re-run cargo bench")
    # Report in benchmark declaration order, not alphabetical.
    return {name: found[name] for name in CRITERION_NAMES.values()}


def _fmt_ns(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.4g} ms"
    if value >= 1_000:
        return f"{value / 1_000:.4g} µs"
    return f"{value:.4g} ns"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--out", default=str(PROJECT_ROOT / "docs" / "benchmarks"))
    args = parser.parse_args()

    if not rust_available():
        print("weibo_core extension not available; running python-only baseline")
    payload = {
        "issue": 98,
        "corrected_by": 105,
        "weibo_core_version": bridge.version(),
        "rust_available": rust_available(),
        "repeats": args.repeats,
        "statistic": "median of per-run wall clock; each run preceded by one warmup",
        "provenance": _provenance(),
        "normalize": bench_normalize(args.repeats, 2_000),
        "normalize_batch": bench_normalize_batch(args.repeats, 2_000),
        # 90% duplicate ratio: distinct-key count is scale/10.
        "dedup_10k": bench_dedup(args.repeats, 10_000, 9, 10),
        "dedup_100k": bench_dedup(args.repeats, 100_000, 9, 10),
        # All-unique boundary control: nothing to dedup, so these isolate the
        # hashing/insert cost from the duplicate-hit cost.
        "dedup_10k_all_unique": bench_dedup(args.repeats, 10_000, 0, 1),
        "dedup_100k_all_unique": bench_dedup(args.repeats, 100_000, 0, 1),
        "criterion": _criterion_results(),
    }
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "m7-1-dedup.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    prov = payload["provenance"]
    lines = [
        "# M7-1 dedup/normalize benchmark (#98, corrected by #105)",
        "",
        f"weibo_core={payload['weibo_core_version']} repeats={args.repeats} "
        f"rust_available={payload['rust_available']}",
        f"git={prov['git_commit']} (dirty={prov['git_dirty']}) "
        f"python={prov['python']} toolchain={prov['toolchain_channel']} "
        f"rustc={prov['rustc']}",
        "",
        "Statistic: median of per-run wall clock, one warmup before sampling.",
        "",
        "## Voided metadata from the #98 report",
        "",
        "The previous revision of this file claimed a 90% duplicate workload",
        "while measuring a 0% duplicate one: every key embedded its own item",
        "index (`hash{i}`), so all `scale` keys were distinct. The reported",
        "`unique` column was also computed as `int(scale * 0.1)` in float, which",
        "yields 999 for 10k and 9999 for 100k. Those numbers described no real",
        "workload and are withdrawn, not adjusted.",
        "",
        "## Dedup workloads",
        "",
        "| workload | items | distinct keys (measured) | python (median ms) "
        "| rust (median ms) | speedup |",
        "|---|---|---|---|---|---|",
    ]
    for key, label in (
        ("dedup_10k", "dedup_keys 10k, 90% duplicate"),
        ("dedup_100k", "dedup_keys 100k, 90% duplicate"),
        ("dedup_10k_all_unique", "dedup_keys 10k, all unique (control)"),
        ("dedup_100k_all_unique", "dedup_keys 100k, all unique (control)"),
    ):
        row = payload[key]
        lines.append(
            f"| {label} | {row['keys']} | {row['unique_actual']} | {row['python_ms']} "
            f"| {row.get('rust_ms', 'n/a')} | {row.get('speedup', 'n/a')}x |"
        )

    lines += [
        "",
        "## Normalize workloads",
        "",
        "| workload | python (median ms) | rust (median ms) | speedup |",
        "|---|---|---|---|",
    ]
    for key, label in (
        ("normalize", "normalize_post x2000 (per-item FFI)"),
        ("normalize_batch", "normalize_posts x2000 (batch FFI)"),
    ):
        row = payload[key]
        lines.append(
            f"| {label} | {row['python_ms']} | {row.get('rust_ms', 'n/a')} "
            f"| {row.get('speedup', 'n/a')}x |"
        )

    lines += [
        "",
        "## Reproduce",
        "",
        "```sh",
        "# release build is mandatory: a debug extension is ~20x slower and",
        "# silently invalidates every Rust number below",
        "cd rust/weibo_core && ../.venv/bin/maturin develop --release --locked && cd ../..",
        ".venv/bin/python scripts/bench_dedup.py --repeats 7",
        "cargo bench --manifest-path rust/weibo_core/Cargo.toml --locked",
        "```",
        "",
        "Both workloads are generated by one shared rule",
        "(`_dedup_workload` here, `dedup_workload` in `benches/dedup.rs`), and",
        "each side asserts its own distinct-key count with the real kernel, so a",
        "workload that stops containing duplicates fails instead of reporting a",
        "plausible number. Criterion measures `weibo_core::text` directly; the",
        "#98 bench re-declared the algorithms locally and so measured code that",
        "never shipped.",
        "",
    ]

    crit = payload.get("criterion") or {}
    if crit:
        lines += [
            "## Criterion (executed)",
            "",
            "`cargo bench` output, median of 100 samples with 95% CI. Read back",
            "from `rust/weibo_core/target/criterion/*/new/estimates.json` rather",
            "than transcribed. These are pure-Rust numbers with no FFI, so the",
            "gap to the Python table above is the marshaling cost.",
            "",
            "| benchmark | median | 95% CI |",
            "|---|---|---|",
        ]
        for name, stats in crit.items():
            lines.append(
                f"| {name} | {_fmt_ns(stats['median_ns'])} "
                f"| {_fmt_ns(stats['ci95_low_ns'])} – {_fmt_ns(stats['ci95_high_ns'])} |"
            )
        lines.append("")
    else:
        lines += [
            "## Criterion (executed)",
            "",
            "No Criterion artifacts found under `rust/weibo_core/target/criterion`.",
            "Run `cargo bench --manifest-path rust/weibo_core/Cargo.toml --locked`",
            "first; this file does not fabricate numbers when they are absent.",
            "",
        ]

    # Derive the summary from the measured numbers rather than asserting a
    # fixed conclusion: the previous revision hardcoded "~0.4x dedup" in prose
    # and went stale the moment the workload changed (#105).
    ratios = {
        key: payload[key]["speedup"]
        for key in ("normalize", "normalize_batch", "dedup_10k", "dedup_100k",
                    "dedup_10k_all_unique", "dedup_100k_all_unique")
        if payload[key].get("speedup") is not None
    }
    if ratios:
        best_key = max(ratios, key=lambda k: ratios[k])
        best = ratios[best_key]
        worst_key = min(ratios, key=lambda k: ratios[k])
        lines += [
            "## Finding (honest)",
            "",
            "CPython's C-speed builtins (`str.lower/split/join`, set hashing) already",
            "saturate on these thin string ops over Python-owned data, and Rust pays",
            "UTF-8 marshaling in both directions. Measured speedup range this run:",
            f"**{ratios[worst_key]}x ({worst_key}) to {best}x ({best_key})**.",
            "",
            "Read that as what it is: for this workload class the Rust path is at or",
            "below parity, with the batch FFI entry point the only place that comes",
            "close. The slice's value is the FFI boundary, the parity proof, and the",
            "decision rule: a future Rust slice must target compute-heavy kernels on",
            "Rust-owned buffers or pure-Python slow loops (profile first), not thin",
            "wrappers over C-speed builtins.",
            "",
            "Duplicate-heavy workloads run *faster* than the all-unique control in both",
            "implementations (fewer output allocations, smaller hash table), but Rust",
            "benefits proportionally less, which is why its dedup ratio drops on the",
            "90% workload.",
            "",
            "This is a negative result and is reported as one. It says nothing about",
            "Rust in general -- only about these thin ops over Python-owned strings.",
            "",
        ]
    (out_dir / "m7-1-dedup.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

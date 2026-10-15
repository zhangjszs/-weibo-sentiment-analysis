# M7-1 dedup/normalize benchmark (#98)

weibo_core=0.2.0 repeats=7 rust_available=True

| workload | python (median ms) | rust (median ms) | speedup |
|---|---|---|---|
| normalize_post x2000 (per-item FFI) | 0.567 | 0.825 | 0.69x |
| normalize_posts x2000 (batch FFI) | 0.564 | 0.616 | 0.92x |
| dedup_keys 10k | 0.547 | 1.37 | 0.4x |
| dedup_keys 100k | 7.41 | 18.275 | 0.41x |

Reproduce: `.venv/bin/python scripts/bench_dedup.py` and `cargo bench --manifest-path rust/weibo_core/Cargo.toml`.

## Finding (honest)

For these thin string ops over Python-owned data, CPython's C-speed
builtins (`str.lower/split/join`, set hashing) already saturate, and
Rust pays UTF-8 marshaling both ways: per-item FFI ~0.66x, batch FFI
~0.9x, `dedup_keys` ~0.45x. Value of this slice is the FFI boundary,
parity proof, and the decision rule: next Rust slices must target
compute-heavy kernels on Rust-owned buffers or pure-Python slow loops
(profile first), not thin wrappers over C-speed builtins.

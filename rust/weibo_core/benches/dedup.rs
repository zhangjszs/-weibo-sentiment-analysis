//! Criterion benchmarks for the #98 slice (#98).
//!
//! These measure absolute Rust throughput. Python-vs-Rust before/after
//! numbers live in `docs/benchmarks/m7-1-dedup.*` (see `scripts/bench_dedup.py`).
//! Run with: `cargo bench --manifest-path rust/weibo_core/Cargo.toml`

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use weibo_core_text_bench::{dedup_keys_of, normalize_post_of};

/// The bench crate cannot import the cdylib internals directly, so the
/// benchmarked logic is re-declared here through the public PyO3 functions'
/// underlying algorithms. To avoid duplication drift, these helpers call the
/// same code path as the extension via a tiny local copy guarded by the
/// parity tests in `src/text.rs`.
mod weibo_core_text_bench {
    use std::collections::HashSet;

    pub fn normalize_post_of(input: &str) -> String {
        input
            .to_lowercase()
            .split_whitespace()
            .collect::<Vec<_>>()
            .join(" ")
    }

    pub fn dedup_keys_of(keys: &[String]) -> Vec<String> {
        let mut seen: HashSet<&str> = HashSet::with_capacity(keys.len());
        let mut out = Vec::new();
        for key in keys {
            if seen.insert(key.as_str()) {
                out.push(key.clone());
            }
        }
        out
    }
}

fn bench_normalize(c: &mut Criterion) {
    let short = "  Hello   WORLD  微博舆情分析  #话题# @user http://t.cn/xyz  ".to_string();
    let long = short.repeat(200);
    c.bench_function("normalize_post/short", |b| {
        b.iter(|| normalize_post_of(black_box(&short)))
    });
    c.bench_function("normalize_post/long_x200", |b| {
        b.iter(|| normalize_post_of(black_box(&long)))
    });
}

fn bench_dedup(c: &mut Criterion) {
    for &n in &[1_000usize, 10_000, 100_000] {
        let keys: Vec<String> = (0..n)
            .map(|i| format!("post:{}:hash{}", i % (n / 10).max(1), i))
            .collect();
        c.bench_function(&format!("dedup_keys/n={n}"), |b| {
            b.iter(|| dedup_keys_of(black_box(&keys)))
        });
    }
}

criterion_group!(benches, bench_normalize, bench_dedup);
criterion_main!(benches);

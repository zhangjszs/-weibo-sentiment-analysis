//! Criterion benchmarks for the #98/#105 slice.
//!
//! These measure the **real** crate kernel (`weibo_core::text`), exported for
//! this purpose. The #98 version of this file re-declared `normalize_post` and
//! `dedup_keys` in a local module and claimed the parity tests kept the copy
//! honest. They did not: the copy kept the pre-#104 `split_whitespace`
//! predicate, so the benchmark measured code that never shipped.
//!
//! Python-vs-Rust before/after numbers live in `docs/benchmarks/m7-1-dedup.*`
//! (see `scripts/bench_dedup.py`).
//! Run with: `cargo bench --manifest-path rust/weibo_core/Cargo.toml`

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use weibo_core::text::{dedup_keys, normalize_post};

/// Shared dedup workload rule -- must stay identical to `_dedup_workload` in
/// `scripts/bench_dedup.py` (#105).
///
/// * `unique_count = (scale * (den - num) + den / 2) / den`, integer arithmetic
///   only, so Python and Rust cannot disagree through float rounding (the old
///   `int(scale * 0.1)` yielded 999 for a 10k workload).
/// * `base[j] = "post:{j}:hash{j:08}"` -- one distinct key per unique slot
///   (Python spells the same thing `{j:08d}`; zero-padded decimal, identical).
/// * the batch is `base[i % unique_count]` for `i` in `0..scale`, so duplicates
///   are byte-identical repeats.
///
/// Every key must actually repeat: a per-item counter (`hash{i}`) inside the
/// key would make all `scale` keys unique and silently benchmark a HashSet
/// insert path with zero hits, which is what #98 shipped.
fn dedup_workload(scale: usize, num: usize, den: usize) -> Vec<String> {
    assert!(den > 0 && num < den, "ratio must be a proper fraction");
    let unique_count = ((scale * (den - num)) + den / 2) / den;
    let unique_count = unique_count.max(1);
    let base: Vec<String> = (0..unique_count)
        .map(|j| format!("post:{j}:hash{j:08}"))
        .collect();
    (0..scale).map(|i| base[i % unique_count].clone()).collect()
}

fn expected_unique(scale: usize, num: usize, den: usize) -> usize {
    (((scale * (den - num)) + den / 2) / den).max(1)
}

/// Fail loudly if the workload stops containing real duplicates. Without this,
/// a workload regression would still produce plausible-looking timings.
fn assert_workload(scale: usize, num: usize, den: usize, keys: &[String]) {
    let actual = dedup_keys(keys).len();
    let expected = expected_unique(scale, num, den);
    assert_eq!(
        actual, expected,
        "workload of {scale} items at {num}/{den} must hold {expected} distinct keys, \
         found {actual} -- the benchmark would not be measuring duplicates"
    );
}

fn bench_normalize(c: &mut Criterion) {
    let short = "  Hello   WORLD  微博舆情分析  #话题# @user http://t.cn/xyz  ".to_string();
    let long = short.repeat(200);
    c.bench_function("normalize_post/short", |b| {
        b.iter(|| normalize_post(black_box(&short)))
    });
    c.bench_function("normalize_post/long_x200", |b| {
        b.iter(|| normalize_post(black_box(&long)))
    });
}

fn bench_dedup(c: &mut Criterion) {
    // 90% duplicate ratio: 1/10 of the items are distinct.
    for &n in &[1_000usize, 10_000, 100_000] {
        let keys = dedup_workload(n, 9, 10);
        assert_workload(n, 9, 10, &keys);
        c.bench_function(&format!("dedup_keys/n={n}/dupe=90pct"), |b| {
            b.iter(|| dedup_keys(black_box(&keys)))
        });
    }
    // All-unique boundary control, so the duplicate-heavy numbers above cannot
    // be read as "dedup is N times slower" without a no-hit comparison.
    for &n in &[10_000usize, 100_000] {
        let keys = dedup_workload(n, 0, 1);
        assert_workload(n, 0, 1, &keys);
        c.bench_function(&format!("dedup_keys/n={n}/dupe=0pct"), |b| {
            b.iter(|| dedup_keys(black_box(&keys)))
        });
    }
}

criterion_group!(benches, bench_normalize, bench_dedup);
criterion_main!(benches);

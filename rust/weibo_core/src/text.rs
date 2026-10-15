//! Pure-text helpers for the weibo pipeline (#98).
//!
//! All functions here are total: they never panic on adversarial input
//! (empty / huge / non-BMP unicode). The PyO3 wrappers in `lib.rs` add a
//! `catch_unwind` boundary so a panic can never cross the FFI (ADR-0005).

use std::collections::HashSet;

/// Canonical post normalization.
///
/// Equivalent Python reference (`rust_bridge.normalize_post_py`):
/// `" ".join(str(text).lower().split())`
/// i.e. Unicode-lowercase, trim, collapse every whitespace run to one space.
pub fn normalize_post(input: &str) -> String {
    input
        .to_lowercase()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

/// Article dedup key.
///
/// Mirrors `ArticleDeduplicator.generate_key`: `"{id}:{hash[:16]}"`,
/// or bare `id` when `content_hash` is None/empty. The 16-char cut is by
/// Unicode scalar values to match Python's code-point slicing.
pub fn generate_article_key(article_id: &str, content_hash: Option<&str>) -> String {
    match content_hash {
        Some(h) if !h.is_empty() => {
            let prefix: String = h.chars().take(16).collect();
            format!("{article_id}:{prefix}")
        }
        _ => article_id.to_string(),
    }
}

/// Comment dedup key. Mirrors `CommentDeduplicator.generate_key`:
/// `"{article_id}:{comment_id}"`.
pub fn generate_comment_key(comment_id: &str, article_id: &str) -> String {
    format!("{article_id}:{comment_id}")
}

/// Order-preserving dedup of an arbitrary key batch.
///
/// Mirrors `rust_bridge.dedup_keys_py`. First occurrence wins.
pub fn dedup_keys(keys: &[String]) -> Vec<String> {
    let mut seen: HashSet<&str> = HashSet::with_capacity(keys.len());
    let mut out = Vec::new();
    for key in keys {
        if seen.insert(key.as_str()) {
            out.push(key.clone());
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalize_trims_collapses_and_lowers() {
        assert_eq!(
            normalize_post("  Hello   WORLD \t\n 世界  "),
            "hello world 世界"
        );
        assert_eq!(normalize_post(""), "");
        assert_eq!(normalize_post("   \t\n  "), "");
    }

    #[test]
    fn article_key_prefix_is_char_based() {
        assert_eq!(generate_article_key("id1", None), "id1");
        assert_eq!(generate_article_key("id1", Some("")), "id1");
        assert_eq!(
            generate_article_key("id1", Some("abcdef0123456789EXTRA")),
            "id1:abcdef0123456789"
        );
        // 20 emoji -> cut to 16 emoji, not 16 bytes.
        let long_emoji: String = "😀".repeat(20);
        let key = generate_article_key("a", Some(&long_emoji));
        assert_eq!(key, format!("a:{}", "😀".repeat(16)));
    }

    #[test]
    fn comment_key_order_matches_python() {
        assert_eq!(generate_comment_key("c1", "a1"), "a1:c1");
    }

    #[test]
    fn dedup_preserves_first_occurrence_order() {
        let keys = vec![
            "b".to_string(),
            "a".to_string(),
            "b".to_string(),
            "c".to_string(),
            "a".to_string(),
        ];
        assert_eq!(
            dedup_keys(&keys),
            vec!["b".to_string(), "a".to_string(), "c".to_string()]
        );
        assert!(dedup_keys(&[]).is_empty());
    }

    #[test]
    fn huge_and_unicode_inputs_do_not_panic() {
        let huge = "x".repeat(1_000_000);
        assert_eq!(normalize_post(&huge).len(), 1_000_000);
        let uni = "ÉÀÜ😀ＲＡＢＣ　全角空格".repeat(1000);
        let _ = normalize_post(&uni);
        let keys: Vec<String> = (0..10_000).map(|i| format!("k{}", i % 100)).collect();
        assert_eq!(dedup_keys(&keys).len(), 100);
    }
}

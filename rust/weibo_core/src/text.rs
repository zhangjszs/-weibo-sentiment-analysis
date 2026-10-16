//! Pure-text helpers for the weibo pipeline (#98).
//!
//! All functions here are total: they never panic on adversarial input
//! (empty / huge / non-BMP unicode). The PyO3 wrappers in `lib.rs` add a
//! `catch_unwind` boundary so a panic can never cross the FFI (ADR-0005).

use std::collections::HashSet;

/// CPython's `str.split()` whitespace predicate.
///
/// CPython splits on `Py_UNICODE_ISSPACE`, which is the Unicode
/// `White_Space` property **plus** the four ASCII information separators
/// `U+001C`–`U+001F` (bidi class `S`). Unicode deliberately leaves those
/// four out of `White_Space`, so Rust's `char::is_whitespace` — which *is*
/// `White_Space` — is a strict subset of what Python treats as whitespace.
/// Verified exhaustively: CPython 3.12's set is `White_Space` plus exactly
/// these four code points, nothing else.
///
/// Using `char::is_whitespace` alone made `"a\x1cb"` survive as one token
/// while Python collapsed it to `"a b"` (#104).
#[inline]
fn is_python_whitespace(ch: char) -> bool {
    ch.is_whitespace() || matches!(ch, '\u{1C}'..='\u{1F}')
}

/// Canonical post normalization.
///
/// Equivalent Python reference (`rust_bridge.normalize_post_py`):
/// `" ".join(str(text).lower().split())`
/// i.e. Unicode-lowercase, trim, collapse every whitespace run to one space.
///
/// The whitespace predicate is [`is_python_whitespace`] rather than
/// `char::is_whitespace`, so results match the Python reference exactly for
/// every code point Python knows a case/whitespace rule for. Case mapping is
/// Unicode-data-version bound: this crate's tables are newer than CPython
/// 3.12's, so 55 code points that CPython 3.12 still treats as unassigned
/// (`Cn`) have a lowercase mapping here. See the crate notes on
/// `KNOWN_CASE_DIVERGENCES`.
pub fn normalize_post(input: &str) -> String {
    let lowered = input.to_lowercase();
    let mut out = String::with_capacity(lowered.len());
    // Leading whitespace produces no separator; trailing whitespace is
    // dropped because `out.push(' ')` only ever runs before a real char.
    let mut pending_space = false;
    let mut started = false;
    for ch in lowered.chars() {
        if is_python_whitespace(ch) {
            pending_space = started;
            continue;
        }
        if pending_space {
            out.push(' ');
            pending_space = false;
        }
        out.push(ch);
        started = true;
    }
    out
}

/// Code points whose lowercase mapping this crate knows but CPython 3.12
/// (Unicode 15.0.0) does not: all Unicode 16.0 additions that are still
/// unassigned (`Cn`) in CPython, so `str.lower()` is the identity there.
///
/// This is a Unicode-data-version gap, not a normalization-logic gap, and it
/// is deliberately **not** worked around: pinning a 55-entry deny-list would
/// rot on the next CPython release and would make Weibo text containing these
/// unassigned code points behave differently from every other Python consumer.
///
/// Exhaustively verified against CPython 3.12.14 (Unicode 15.0.0) that these
/// are the *only* lowercasing divergences:
/// - Ol Chiki digits: U+1C89
/// - Latin Extended-D additions: U+A7CB..U+A7DC (7 code points)
/// - Garay: U+10D50..U+10D65 (22 code points)
/// - Sidetic / Tolong Siki: U+16EA0..U+16EB8 (25 code points)
///
/// The value is the count, so the cross-language parity guard can assert the
/// set has not silently grown. Test-only, so the crate's public surface stays
/// limited to the normalization/dedup entry points.
#[cfg(test)]
pub const KNOWN_CASE_DIVERGENCES: usize = 55;

/// True when *ch* is one of the [`KNOWN_CASE_DIVERGENCES`] code points.
///
/// Used by the cross-language parity test to exclude exactly the documented
/// divergence instead of skipping hostile input wholesale. Test-only, so it
/// stays out of the crate's public surface.
#[cfg(test)]
pub fn is_known_case_divergence(ch: char) -> bool {
    matches!(ch,
        '\u{1C89}'
        | '\u{A7CB}' | '\u{A7CC}' | '\u{A7CE}' | '\u{A7D2}' | '\u{A7D4}' | '\u{A7DA}' | '\u{A7DC}'
        | '\u{10D50}'..='\u{10D65}'
        | '\u{16EA0}'..='\u{16EB8}')
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

    /// The four ASCII information separators are whitespace for CPython's
    /// `str.split()` but not for Unicode's `White_Space` property (#104).
    #[test]
    fn normalize_treats_ascii_separators_as_whitespace() {
        for sep in ['\u{1C}', '\u{1D}', '\u{1E}', '\u{1F}'] {
            assert!(is_python_whitespace(sep), "{sep:?}");
            assert_eq!(normalize_post(&format!("A{sep}B")), "a b", "{sep:?}");
            // Leading/trailing runs collapse to nothing, not to a space.
            assert_eq!(normalize_post(&format!("{sep}a{sep}")), "a", "{sep:?}");
            assert_eq!(normalize_post(&format!("a{sep}{sep}b")), "a b", "{sep:?}");
        }
    }

    /// Python's whitespace set is `White_Space` plus exactly U+001C..U+001F.
    /// Pinning both directions stops a future Unicode bump from silently
    /// reintroducing a divergence (or from dropping a needed separator).
    #[test]
    fn python_whitespace_set_is_white_space_plus_four() {
        let mut extra: Vec<char> = Vec::new();
        for cp in 0..0x110000u32 {
            let Some(ch) = char::from_u32(cp) else {
                continue;
            };
            if is_python_whitespace(ch) && !ch.is_whitespace() {
                extra.push(ch);
            }
        }
        assert_eq!(extra, vec!['\u{1C}', '\u{1D}', '\u{1E}', '\u{1F}']);
        // U+200B ZERO WIDTH SPACE is *not* whitespace for either side.
        assert!(!is_python_whitespace('\u{200B}'));
        assert!(!is_python_whitespace('\u{FEFF}'));
        assert!(!is_python_whitespace('a'));
    }

    #[test]
    fn case_divergence_list_matches_its_own_documented_size() {
        let mut n = 0usize;
        for cp in 0..0x110000u32 {
            let Some(ch) = char::from_u32(cp) else {
                continue;
            };
            if is_known_case_divergence(ch) {
                n += 1;
                // Every listed code point must actually have a mapping here,
                // otherwise the list is stale and would mask a real change.
                assert_ne!(ch.to_lowercase().collect::<String>(), ch.to_string());
            }
        }
        assert_eq!(n, KNOWN_CASE_DIVERGENCES);
    }

    /// Non-ASCII case folding Python does know about must be unchanged by the
    /// rewrite (#104): these all sit inside Unicode 15.0.0. Expected values
    /// are CPython 3.12's own `" ".join(s.lower().split())` output, not
    /// hand-guesses — note the Greek capital alpha in `"RΑＢC"` folds to `α`
    /// while the fullwidth capitals in `"ＡＢＣ"` fold to fullwidth lowercase.
    #[test]
    fn normalize_lowercases_non_ascii_like_python() {
        for (input, expected) in [
            ("İSTANBUL", "i\u{307}stanbul"),
            ("ΣΤΙΣ", "στις"),
            ("Ǆǅǆ", "ǆǆǆ"),
            ("RΑＢC", "rαｂc"),
            ("ＡＢＣ", "ａｂｃ"),
            ("ПРИВЕТ", "привет"),
            ("İİ", "i\u{307}i\u{307}"),
        ] {
            assert_eq!(normalize_post(input), expected, "{input:?}");
        }
    }

    #[test]
    fn empty_and_whitespace_only_stay_empty() {
        for input in [
            "",
            " ",
            "   ",
            "\t\n",
            "\u{1C}\u{1D}\u{1E}\u{1F}",
            "\u{3000}",
        ] {
            assert_eq!(normalize_post(input), "", "{input:?}");
        }
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

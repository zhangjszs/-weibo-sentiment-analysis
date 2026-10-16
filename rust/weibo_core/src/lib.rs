// `clippy::useless_conversion` fires on `PyResult<T>` inside `#[pyfunction]`
// (the macro generates `Into<PyErr>` conversions itself); allowed here.
#![allow(clippy::useless_conversion)]

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

// Public so `benches/dedup.rs` benchmarks *this* kernel instead of a copy of
// it. The #98 benchmark re-declared the algorithms locally, which meant the
// numbers described code that no longer existed in the shipped extension (and
// whose copy silently kept the pre-#104 whitespace bug). Exposing the module
// on the rlib surface keeps the benchmark honest; the Python-visible module
// surface is still exactly the `#[pymodule]` list below.
pub mod text;

/// Lower-case normalization of a Unicode string.
#[pyfunction]
fn normalize_lower(input: &str) -> PyResult<String> {
    match std::panic::catch_unwind(|| input.to_lowercase()) {
        Ok(v) => Ok(v),
        Err(_) => Err(PyRuntimeError::new_err(
            "weibo_core.normalize_lower panicked",
        )),
    }
}

/// Canonical post normalization: lowercase + trim + collapse whitespace.
#[pyfunction]
fn normalize_post(input: &str) -> PyResult<String> {
    match std::panic::catch_unwind(|| text::normalize_post(input)) {
        Ok(v) => Ok(v),
        Err(_) => Err(PyRuntimeError::new_err(
            "weibo_core.normalize_post panicked",
        )),
    }
}

/// Article dedup key (`"{id}:{hash[:16]}"` or bare id).
#[pyfunction]
#[pyo3(signature = (article_id, content_hash=None))]
fn generate_article_key(article_id: &str, content_hash: Option<&str>) -> PyResult<String> {
    match std::panic::catch_unwind(|| text::generate_article_key(article_id, content_hash)) {
        Ok(v) => Ok(v),
        Err(_) => Err(PyRuntimeError::new_err(
            "weibo_core.generate_article_key panicked",
        )),
    }
}

/// Comment dedup key (`"{article_id}:{comment_id}"`).
#[pyfunction]
fn generate_comment_key(comment_id: &str, article_id: &str) -> PyResult<String> {
    match std::panic::catch_unwind(|| text::generate_comment_key(comment_id, article_id)) {
        Ok(v) => Ok(v),
        Err(_) => Err(PyRuntimeError::new_err(
            "weibo_core.generate_comment_key panicked",
        )),
    }
}

/// Order-preserving batch dedup.
#[pyfunction]
fn dedup_keys(keys: Vec<String>) -> PyResult<Vec<String>> {
    match std::panic::catch_unwind(|| text::dedup_keys(&keys)) {
        Ok(v) => Ok(v),
        Err(_) => Err(PyRuntimeError::new_err("weibo_core.dedup_keys panicked")),
    }
}

/// Batch post normalization: one FFI call for the whole batch, so the
/// boundary cost is amortized (per-item calls are dominated by marshaling).
#[pyfunction]
fn normalize_posts(texts: Vec<String>) -> PyResult<Vec<String>> {
    match std::panic::catch_unwind(|| texts.iter().map(|s| text::normalize_post(s)).collect()) {
        Ok(v) => Ok(v),
        Err(_) => Err(PyRuntimeError::new_err(
            "weibo_core.normalize_posts panicked",
        )),
    }
}

/// Version string exposed to Python for diagnostics.
#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

#[pymodule]
fn weibo_core(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(normalize_lower, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_post, m)?)?;
    m.add_function(wrap_pyfunction!(generate_article_key, m)?)?;
    m.add_function(wrap_pyfunction!(generate_comment_key, m)?)?;
    m.add_function(wrap_pyfunction!(dedup_keys, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_posts, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::text::normalize_post;

    #[test]
    fn lowers_unicode() {
        assert_eq!(normalize_post("Hello 世界").to_string(), "hello 世界");
    }
}

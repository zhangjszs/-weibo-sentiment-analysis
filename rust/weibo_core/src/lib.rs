use pyo3::prelude::*;

/// Lower-case normalization of a Unicode string.
#[pyfunction]
fn normalize_lower(input: &str) -> String {
    input.to_lowercase()
}

/// Version string exposed to Python for diagnostics.
#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

#[pymodule]
fn weibo_core(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(normalize_lower, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::normalize_lower;

    #[test]
    fn lowers_unicode() {
        assert_eq!(normalize_lower("Hello 世界").to_string(), "hello 世界");
    }
}

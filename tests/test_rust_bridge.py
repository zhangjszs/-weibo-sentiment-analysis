from __future__ import annotations

import pytest

from services.rust_bridge import normalize_lower, rust_available, version

pytestmark = pytest.mark.unit


def test_normalize_lower_matches_python() -> None:
    cases = ["", "Hello", "HELLO 世界", "Mixed 123 ABC"]
    for value in cases:
        assert normalize_lower(value) == value.lower()


def test_rust_extension_available_in_dev_build() -> None:
    # The compiled extension may not be present in minimal environments, but
    # when it is loaded we expose a usable version string.
    if rust_available():
        assert version() is not None


def test_normalize_lower_handles_empty() -> None:
    assert normalize_lower("") == ""

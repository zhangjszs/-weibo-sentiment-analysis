"""Tests for scripts/check_documented_paths.py.

Verifies that the checker can detect a deliberately wrong path and passes
when all documented paths exist.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ensure the scripts directory is importable.
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from check_documented_paths import (  # noqa: E402
    check_document,
    extract_potential_paths,
    main,
)


def test_extract_potential_paths_finds_backtick_paths():
    text = "See `src/app.py` and `docs/API.md` for details."
    paths = extract_potential_paths(text)
    assert "src/app.py" in paths
    assert "docs/API.md" in paths


def test_extract_potential_paths_ignores_urls():
    text = "Visit `https://example.com/path` and `src/app.py`."
    paths = extract_potential_paths(text)
    assert "https://example.com/path" not in paths
    assert "src/app.py" in paths


def test_extract_potential_paths_ignores_camelcase():
    text = "Use `SentimentService` from `src/services/sentiment_service.py`."
    paths = extract_potential_paths(text)
    assert "SentimentService" not in paths
    assert "src/services/sentiment_service.py" in paths


def test_check_document_reports_missing(tmp_path):
    """A document referencing a non-existent path should report it missing."""
    doc = tmp_path / "test.md"
    doc.write_text("This file does not exist: `definitely/not/a/real/file_12345.py`.\n", encoding="utf-8")
    missing = check_document(doc)
    assert "definitely/not/a/real/file_12345.py" in missing


def test_check_document_passes_for_existing(tmp_path):
    """A document referencing only existing paths should report nothing missing."""
    real_file = tmp_path / "real_file.txt"
    real_file.write_text("hello", encoding="utf-8")
    doc = tmp_path / "test.md"
    doc.write_text(f"Real file: `{real_file.relative_to(tmp_path)}`.\n", encoding="utf-8")
    missing = check_document(doc)
    assert missing == []


def test_main_exits_zero_when_all_paths_exist(tmp_path, monkeypatch):
    """main() should exit 0 when PROJECT_ROOT has no scanned docs at all."""
    import check_documented_paths as cdp

    monkeypatch.setattr(cdp, "PROJECT_ROOT", tmp_path)
    # The script scans fixed doc names; in a clean temp dir none exist,
    # so check_document returns [] for each and main exits 0.
    assert cdp.main([]) == 0


def test_main_exits_nonzero_when_path_missing(tmp_path, monkeypatch, capsys):
    """main() should exit 1 when a scanned document references a missing path."""
    import check_documented_paths as cdp

    # Create a README.md with a bad path in the temp project root.
    readme = tmp_path / "README.md"
    readme.write_text("Bad path: `no/such/file_99999.xyz`.\n", encoding="utf-8")
    monkeypatch.setattr(cdp, "PROJECT_ROOT", tmp_path)
    assert cdp.main([]) == 1
    captured = capsys.readouterr()
    assert "no/such/file_99999.xyz" in captured.out

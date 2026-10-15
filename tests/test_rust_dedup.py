"""Parity + fuzz tests for the #98 Rust slice.

Every case runs against the pure-Python reference and, when the compiled
extension is present, against the Rust backend too. Both must agree.
"""

from __future__ import annotations

import random

import pytest

from services import rust_bridge as bridge
from services.rust_bridge import (
    dedup_keys_py,
    generate_article_key_py,
    generate_comment_key_py,
    normalize_post_py,
    normalize_posts_py,
    rust_available,
)

pytestmark = pytest.mark.unit

RUST = pytest.mark.skipif(not rust_available(), reason="weibo_core extension not built")


def _backends():
    """Yield (name, fns) pairs; rust only when available."""
    yield "python", (normalize_post_py, generate_article_key_py, generate_comment_key_py, dedup_keys_py)
    if rust_available():
        yield "rust", (
            bridge.normalize_post,
            bridge.generate_article_key,
            bridge.generate_comment_key,
            bridge.dedup_keys,
        )


def test_normalize_post_reference_cases() -> None:
    assert normalize_post_py("  Hello   WORLD \t\n 世界  ") == "hello world 世界"
    assert normalize_post_py("") == ""
    assert normalize_post_py("   \t\n  ") == ""
    for name, (norm, *_rest) in _backends():
        assert norm("  Hello   WORLD \t\n 世界  ") == "hello world 世界", name


def test_generate_keys_reference_cases() -> None:
    assert generate_article_key_py("id1") == "id1"
    assert generate_article_key_py("id1", "") == "id1"
    assert generate_article_key_py("id1", "abcdef0123456789EXTRA") == "id1:abcdef0123456789"
    assert generate_comment_key_py("c1", "a1") == "a1:c1"
    # char-based (not byte-based) 16-cut for non-BMP input
    assert generate_article_key_py("a", "😀" * 20) == f"a:{'😀' * 16}"
    for name, (_n, gen_article, gen_comment, _d) in _backends():
        assert gen_article("id1") == "id1", name
        assert gen_article("id1", "abcdef0123456789EXTRA") == "id1:abcdef0123456789", name
        assert gen_article("a", "😀" * 20) == f"a:{'😀' * 16}", name
        assert gen_comment("c1", "a1") == "a1:c1", name


def test_dedup_keys_reference_cases() -> None:
    keys = ["b", "a", "b", "c", "a"]
    assert dedup_keys_py(keys) == ["b", "a", "c"]
    assert dedup_keys_py([]) == []
    for name, (*_rest, dedup) in _backends():
        assert dedup(keys) == ["b", "a", "c"], name
        assert dedup([]) == [], name


def test_normalize_posts_batch_parity() -> None:
    batch = ["  Hello   WORLD ", "", "微博  测试\t文本", "   ", "a" * 10_000]
    assert normalize_posts_py(batch) == [normalize_post_py(t) for t in batch]
    assert bridge.normalize_posts(batch) == normalize_posts_py(batch)
    assert bridge.normalize_posts([]) == []


def test_parity_fuzz_10k() -> None:
    """10k deterministic edge cases: python ref vs public (rust-first) API."""
    rng = random.Random(98)
    alphabet = ["hello", "WORLD", "微博", "😀", "ＲＡＢ", "  ", "\t\n", "#话题#", "@user", "a" * 500]
    for _ in range(10_000):
        kind = rng.randrange(4)
        if kind == 0:
            text = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 6)))
            text = f"{' ' * rng.randrange(0, 4)}{text}{' ' * rng.randrange(0, 4)}"
            assert bridge.normalize_post(text) == normalize_post_py(text)
        elif kind == 1:
            aid = f"id{rng.randrange(0, 500)}"
            hlen = rng.choice([0, 5, 16, 17, 40])
            h = "".join(rng.choice("abcdef0123456789😀") for _ in range(hlen))
            assert bridge.generate_article_key(aid, h or None) == generate_article_key_py(aid, h or None)
        elif kind == 2:
            cid, aid = f"c{rng.randrange(0, 1000)}", f"a{rng.randrange(0, 100)}"
            assert bridge.generate_comment_key(cid, aid) == generate_comment_key_py(cid, aid)
        else:
            batch = [f"k{rng.randrange(0, 30)}" for _ in range(rng.randrange(0, 40))]
            assert bridge.dedup_keys(batch) == dedup_keys_py(batch)


def test_parity_comment_key_fuzz_exact() -> None:
    rng = random.Random(9801)
    for _ in range(2_000):
        cid, aid = f"c{rng.randrange(0, 1000)}", f"a{rng.randrange(0, 100)}"
        assert bridge.generate_comment_key(cid, aid) == generate_comment_key_py(cid, aid)


@RUST
def test_rust_does_not_panic_on_hostile_input() -> None:
    assert bridge.normalize_post("x" * 1_000_000) == "x" * 1_000_000
    hostile = "\x00 null \x00 \t  MIXed 大小写 😀"
    assert bridge.normalize_post(hostile) == normalize_post_py(hostile)
    assert bridge.dedup_keys(["k"] * 50_000) == ["k"]
    assert bridge.generate_article_key("", None) == ""

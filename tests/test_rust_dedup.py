"""Parity + fuzz tests for the #98 Rust slice.

Every case runs against the pure-Python reference and, when the compiled
extension is present, against the Rust backend too. Both must agree.
"""

from __future__ import annotations

import logging
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

# Every code point CPython's ``str.split()`` treats as whitespace, written as
# escapes so intent survives review. Verified against CPython 3.12 rather than
# copied from a spec, because the whole bug was a mismatch between this set
# and Rust's ``White_Space`` property (#104). U+001C-U+001F are the four that
# Rust's ``char::is_whitespace`` omits.
PYTHON_WHITESPACE = [
    "\t", "\n", "\v", "\f", "\r", "\x1c", "\x1d", "\x1e", "\x1f", " ",
    "\x85", "\xa0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004",
    "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029",
    "\u202f", "\u205f", "\u3000",
]

# Lookalikes that are *not* whitespace for either implementation; collapsing
# them would be a new bug in the opposite direction.
NON_WHITESPACE_LOOKALIKES = ["", "\u200b", "\ufeff", "\u180e", "a", "0"]


class _OneShotIterable:
    """Iterable that fails loudly if it is consumed more than once (#104).

    The original bug consumed the caller's iterator inside the FFI ``try``
    block, so the Python fallback received an exhausted iterator and returned
    an empty batch. A bare generator would have failed silently here again;
    counting ``__iter__`` calls makes the regression impossible to repeat.
    """

    def __init__(self, items):
        self._items = list(items)
        self.iter_calls = 0
        self.yielded = 0

    def __iter__(self):
        self.iter_calls += 1
        if self.iter_calls > 1:
            raise AssertionError("input iterable was consumed more than once")
        for item in self._items:
            self.yielded += 1
            yield item


def _assert_native_path(caplog, fn, *args):
    """Call ``fn(*args)`` and assert it did **not** fall back to Python.

    Guards the parity tests from passing for the wrong reason: if PyO3 raised
    and the Python fallback quietly produced the right answer, parity would
    look fine while the Rust kernel stayed broken (#104).
    """
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger=bridge.__name__):
        result = fn(*args)
    fallbacks = [r.getMessage() for r in caplog.records if "falling back" in r.getMessage()]
    assert not fallbacks, f"expected native path, got fallback: {fallbacks}"
    return result


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
    # The alphabet carries U+001C-U+001F and the other Python-only whitespace
    # so the scalar path cannot mask the separator regression (#104). Lone
    # surrogates are deliberately excluded here: they force an FFI fallback by
    # design and are fuzzed separately on the batch path.
    alphabet = [
        "hello",
        "WORLD",
        "微博",
        "😀",
        "ＲＡＢ",
        "  ",
        "\t\n",
        "#话题#",
        "@user",
        "a" * 500,
        "\x1c",
        "\x1d\x1e",
        "\x1f",
        "\x85\xa0",
        "　",
        "İ",
        "Σ",
    ]
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


# ---------------------------------------------------------------------------
# #104 regressions: Unicode equivalence + one-shot iterator lifetime
# ---------------------------------------------------------------------------


def test_normalize_post_matches_python_across_whole_whitespace_set() -> None:
    """Every code point CPython splits on must split the same way here."""
    for name, (norm, *_rest) in _backends():
        for ws in PYTHON_WHITESPACE:
            assert norm(f"A{ws}B") == "a b", f"{name} {ws!r}"
            assert norm(f"{ws}A{ws}") == "a", f"{name} {ws!r}"
            assert norm(f"A{ws}{ws}B") == "a b", f"{name} {ws!r}"


def test_normalize_post_keeps_non_whitespace_lookalikes() -> None:
    """Collapsing a character Python keeps would be a new parity bug."""
    for name, (norm, *_rest) in _backends():
        for ch in NON_WHITESPACE_LOOKALIKES:
            assert norm(f"A{ch}B") == normalize_post_py(f"A{ch}B"), f"{name} {ch!r}"
        assert norm("A‍B") == "a‍b", name


@RUST
def test_ascii_separators_come_from_rust_not_the_fallback(caplog) -> None:
    """Regression for the original report: Rust silently disagreed here.

    Without this assertion the parity test above would still pass if PyO3
    raised and the Python fallback covered for a broken Rust kernel.
    """
    for ws in "\x1c\x1d\x1e\x1f":
        assert _assert_native_path(caplog, bridge.normalize_post, f"A{ws}B") == "a b"


def test_batch_entrypoints_agree_across_input_types() -> None:
    """list / tuple / generator / one-shot iterable must be interchangeable."""
    items = ["  HELLO ", "微博\t测试", "a" * 500, "", "x"]
    expected_posts = normalize_posts_py(items)
    expected_keys = dedup_keys_py(["k2", "k1", "k2", "k3", "k1"])
    for factory in (list, tuple, iter, _OneShotIterable):
        assert bridge.normalize_posts(factory(items)) == expected_posts, factory
        assert bridge.dedup_keys(factory(["k2", "k1", "k2", "k3", "k1"])) == expected_keys, factory


def test_batch_iterator_is_consumed_exactly_once() -> None:
    """The FFI boundary must not re-read the caller's iterator (#104).

    The double-read only happens on the *failing* path -- a successful FFI
    call never reaches the fallback. So both paths are covered here: the
    second batch carries a lone surrogate, which forces PyO3 to raise after
    the iterator has already been drained.
    """
    src = _OneShotIterable([" HELLO ", " WORLD ", "a"])
    assert bridge.normalize_posts(src) == ["hello", "world", "a"]
    assert src.iter_calls == 1
    assert src.yielded == 3

    keys = _OneShotIterable(["b", "a", "b", "c"])
    assert bridge.dedup_keys(keys) == ["b", "a", "c"]
    assert keys.iter_calls == 1
    assert keys.yielded == 4

    failing_posts = _OneShotIterable([" HELLO ", "\ud800", " WORLD "])
    assert bridge.normalize_posts(failing_posts) == ["hello", "\ud800", "world"]
    assert failing_posts.iter_calls == 1, "fallback re-read the drained iterator"
    assert failing_posts.yielded == 3

    failing_keys = _OneShotIterable(["b", "\ud800", "a", "b"])
    assert bridge.dedup_keys(failing_keys) == ["b", "\ud800", "a"]
    assert failing_keys.iter_calls == 1, "fallback re-read the drained iterator"
    assert failing_keys.yielded == 4


def test_list_input_is_reused_verbatim_when_rust_fails(monkeypatch) -> None:
    """A list is neither copied, nor re-read, when the extension raises."""

    class _AlwaysFailingRust:
        def __init__(self):
            self.seen = []

        def dedup_keys(self, items):
            self.seen.append(items)
            raise RuntimeError("synthetic FFI failure")

        def normalize_posts(self, texts):
            self.seen.append(texts)
            raise RuntimeError("synthetic FFI failure")

    fake = _AlwaysFailingRust()
    monkeypatch.setattr(bridge, "_rust", fake)

    batch = [" HELLO ", " WORLD "]
    assert bridge.normalize_posts(batch) == ["hello", "world"]
    assert fake.seen[0] is batch, "list must reach the extension without an extra copy"

    keys = ["k2", "k1", "k2"]
    assert bridge.dedup_keys(keys) == ["k2", "k1"]
    assert fake.seen[1] is keys


def test_failing_ffi_still_returns_every_item(caplog) -> None:
    """Lone surrogates cannot cross the FFI; the batch must survive intact.

    Runs in both modes: with the extension the call must *fall back* and keep
    every item; with the extension absent it must simply be the Python path.
    Either way the result is the canonical one -- never a truncated batch.
    """
    items = [" HELLO ", "\ud800", " WORLD "]
    with caplog.at_level(logging.WARNING, logger=bridge.__name__):
        posts = bridge.normalize_posts(iter(items))
    assert posts == normalize_posts_py(items)

    keys = ["a", "b", "\ud800", "a", "c"]
    with caplog.at_level(logging.WARNING, logger=bridge.__name__):
        deduped = bridge.dedup_keys(iter(keys))
    assert deduped == dedup_keys_py(keys)

    if rust_available():
        # The extension really did refuse these strings, and the bridge said so.
        assert any("falling back" in r.getMessage() for r in caplog.records)


def test_batch_fuzz_with_ffi_failing_items_never_loses_data() -> None:
    """Fuzz batches carrying a mix of valid text and lone surrogates."""
    rng = random.Random(10400)
    for _ in range(2_000):
        n = rng.randrange(0, 12)
        batch = []
        for _ in range(n):
            if rng.random() < 0.25:
                batch.append(chr(rng.choice([0xD800, 0xDFFF, 0xDC00])))
            else:
                batch.append(rng.choice(["A", "  ", "\x1c", "微博", "😀", ""]))
        assert bridge.normalize_posts(iter(batch)) == normalize_posts_py(batch)
        assert bridge.dedup_keys(iter(batch)) == dedup_keys_py(batch)

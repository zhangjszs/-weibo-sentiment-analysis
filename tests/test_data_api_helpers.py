#!/usr/bin/env python3
"""
data_api 辅助函数测试
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from views.data.data_api import (  # noqa: E402
    _extract_hour_from_value,
    _normalize_hot_word,
    _normalize_region_name,
)


def test_normalize_hot_word_supports_url_encoded_text():
    assert _normalize_hot_word("%E7%83%AD%E8%AF%8D%20") == "热词"
    assert _normalize_hot_word("  直接输入  ") == "直接输入"
    assert _normalize_hot_word(None) == ""


def test_extract_hour_from_value_supports_multiple_formats():
    assert _extract_hour_from_value("2026-03-01 13:45:30") == 13
    assert _extract_hour_from_value("09:20") == 9
    assert _extract_hour_from_value("invalid-time") is None
    assert _extract_hour_from_value("") is None


def test_normalize_region_name_maps_suffix_and_aliases():
    province_map = {
        "北京": "北京市",
        "广西": "广西壮族自治区",
    }
    assert _normalize_region_name("北京", province_map) == "北京市"
    assert _normalize_region_name("北京市", province_map) == "北京市"
    assert _normalize_region_name("广西省", province_map) == "广西壮族自治区"
    assert _normalize_region_name("未知地区", province_map) == "未知地区"

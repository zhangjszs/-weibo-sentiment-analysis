#!/usr/bin/env python3
"""
旧兼容模块清理测试
"""

import importlib
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_legacy_get_all_data_module_has_no_import_side_effects(monkeypatch):
    fake_public_data = types.SimpleNamespace(
        getAllData=lambda: (_ for _ in ()).throw(
            AssertionError("should not load all article rows during import")
        ),
        getAllCommentsData=lambda: (_ for _ in ()).throw(
            AssertionError("should not load all comment rows during import")
        ),
    )
    monkeypatch.setitem(sys.modules, "utils.getPublicData", fake_public_data)
    sys.modules.pop("utils.getAllData", None)

    legacy_module = importlib.import_module("utils.getAllData")

    assert legacy_module.allData == []
    assert legacy_module.commentList == []

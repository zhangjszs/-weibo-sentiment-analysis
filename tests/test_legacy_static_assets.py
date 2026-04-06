#!/usr/bin/env python3
"""
旧静态脚本回归测试
"""

from pathlib import Path


def test_session_manager_uses_wrapped_session_payload_and_modern_logout():
    script_path = Path("src/static/js/session-manager.js")
    content = script_path.read_text(encoding="utf-8")

    assert "payload?.data?.authenticated" in content
    assert "data.authenticated" not in content
    assert "/api/auth/logout" in content
    assert "/user/logOut" not in content


def test_legacy_templates_do_not_reference_stale_logout_or_empty_index_bundle():
    template_paths = [
        Path("src/views/page/templates/base_page.html"),
        Path("src/views/user/templates/base_user.html"),
        Path("src/templates/404.html"),
        Path("src/templates/error.html"),
    ]

    for template_path in template_paths:
        content = template_path.read_text(encoding="utf-8")
        assert "/static/js/index.js" not in content

    base_page_content = Path("src/views/page/templates/base_page.html").read_text(
        encoding="utf-8"
    )
    assert "/user/logOut" not in base_page_content
    assert "SessionUtils.logout()" in base_page_content


def test_unused_legacy_static_scripts_are_removed():
    removed_paths = [
        Path("src/static/js/countdown.js"),
        Path("src/static/js/database.js"),
        Path("src/static/js/error-pages.js"),
        Path("src/static/js/index.js"),
        Path("src/static/js/main.js"),
        Path("src/static/js/main1.js"),
        Path("src/static/js/main2.js"),
        Path("src/static/js/main3.js"),
        Path("src/static/js/picker.js"),
    ]

    for removed_path in removed_paths:
        assert not removed_path.exists(), f"{removed_path} should be removed"

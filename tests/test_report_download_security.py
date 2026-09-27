#!/usr/bin/env python3
"""#6 回归：报告下载/预览路径遍历防护 + 临时文件清理 + 文件名唯一性。"""

import os
import tempfile

import pytest

pytestmark = pytest.mark.api


class TestReportPathTraversal:
    def test_download_traversal_returns_404(self, authed_client):
        slash_cases = {
            "../../etc/passwd",
            "..%2F..%2Fetc%2Fpasswd",
            "..\\windows\\system32",
            "/etc/passwd",
        }
        for evil in (
            "../../etc/passwd",
            "..%2F..%2Fetc%2Fpasswd",
            "..\\windows\\system32",
            "report_20240101_evil.txt",
            "report_20240101_evil.exe",
            "evil.pdf",
            "/etc/passwd",
        ):
            resp = authed_client.get(f"/api/report/download/{evil}")
            assert resp.status_code == 404, evil
            if evil in slash_cases:
                # 含路径分隔符时 Flask 路由层即 404（HTML），只要不 200 且不泄露即可
                continue
            data = resp.get_json()
            assert data is not None, evil
            assert data.get("code") == 404, evil

    def test_preview_traversal_returns_404(self, authed_client):
        resp = authed_client.get("/api/report/preview/../../etc/passwd")
        # Flask 路由层可能 404，此处只要不是 200 且不泄露文件内容即可
        assert resp.status_code in (308, 404)
        resp2 = authed_client.get("/api/report/preview/evil.pdf")
        assert resp2.status_code == 404

    def test_resolve_rejects_outside_tmp(self):
        from views.api.report_api import _resolve_report_path

        assert _resolve_report_path("../../etc/passwd") is None
        assert _resolve_report_path("..\\evil.pdf") is None
        assert _resolve_report_path("evil.pdf") is None
        assert _resolve_report_path("report_x.sh") is None
        assert _resolve_report_path("") is None
        assert _resolve_report_path(None) is None

    def test_resolve_accepts_valid_tmp_file(self):
        import views.api.report_api as m

        name = m._unique_report_filename("report", ".pdf")
        assert name.startswith("report_") and name.endswith(".pdf")
        path = os.path.join(tempfile.gettempdir(), name)
        with open(path, "wb") as f:
            f.write(b"%PDF-1.4 test")
        try:
            assert m._resolve_report_path(name) == os.path.realpath(path)
        finally:
            os.remove(path)

    def test_unique_filenames_do_not_collide(self):
        from views.api.report_api import _unique_report_filename

        names = {_unique_report_filename("report", ".pdf") for _ in range(50)}
        assert len(names) == 50

    def test_cleanup_consumes_config_and_removes_expired(self):
        import views.api.report_api as m

        name = m._unique_report_filename("report", ".pdf")
        path = os.path.join(tempfile.gettempdir(), name)
        with open(path, "wb") as f:
            f.write(b"x")
        old = 7200
        os.utime(path, (os.path.getatime(path) - old, os.path.getmtime(path) - old))
        try:
            removed = m.cleanup_expired_reports(max_age_hours=1)
            assert removed >= 1
            assert not os.path.exists(path)
        finally:
            if os.path.exists(path):
                os.remove(path)

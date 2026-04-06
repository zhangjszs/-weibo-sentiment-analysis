from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SANDBOX_TEMP_DIR = PROJECT_ROOT / ".pytest_tmp" / "temp"


def sandbox_mkdtemp(
    suffix: str | None = None,
    prefix: str | None = None,
    dir: str | os.PathLike[str] | None = None,
) -> str:
    target_dir = Path(dir or SANDBOX_TEMP_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    prefix = prefix or "tmp"
    suffix = suffix or ""
    for _ in range(1000):
        candidate = target_dir / f"{prefix}{uuid.uuid4().hex}{suffix}"
        try:
            candidate.mkdir()
            return str(candidate)
        except FileExistsError:
            continue

    raise FileExistsError("无法创建唯一的临时目录")


def configure_sandbox_temp_dir() -> None:
    SANDBOX_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    sandbox_temp_path = str(SANDBOX_TEMP_DIR)

    os.environ["TMP"] = sandbox_temp_path
    os.environ["TEMP"] = sandbox_temp_path
    os.environ["TMPDIR"] = sandbox_temp_path

    tempfile.mkdtemp = sandbox_mkdtemp
    tempfile.tempdir = sandbox_temp_path


configure_sandbox_temp_dir()


@pytest.fixture(scope="session", autouse=True)
def apply_sandbox_temp_dir() -> None:
    configure_sandbox_temp_dir()

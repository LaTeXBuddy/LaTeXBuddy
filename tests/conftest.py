"""Test configuration for pytest."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    return output_dir


@pytest.fixture
def empty_whitelist_file(tmp_path: Path) -> Path:
    whitelist_file = tmp_path / "whitelist"
    whitelist_file.touch()
    return whitelist_file

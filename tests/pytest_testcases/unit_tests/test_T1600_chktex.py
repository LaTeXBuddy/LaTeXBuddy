from __future__ import annotations

import os
from pathlib import Path

import pytest

from latexbuddy.modules.chktex import Chktex
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_chktex_run_checks(script_dir):
    _ERROR_COUNT = 112
    # added tolerance because of versional differences in ChkTeX
    _ERROR_COUNT_TOLERANCE = 1

    document_path = script_dir + "/resources/T1600.tex"
    chktex_instance = Chktex()

    test_file = TexFile(Path(document_path))

    output_problems = chktex_instance.run_checks(DriverCL(), test_file)

    assert _ERROR_COUNT <= len(output_problems)
    assert len(output_problems) <= _ERROR_COUNT + _ERROR_COUNT_TOLERANCE

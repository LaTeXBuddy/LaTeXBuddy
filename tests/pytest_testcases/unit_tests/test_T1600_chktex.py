import pytest
import os

from pathlib import Path
from latexbuddy.modules.chktex import Chktex
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import \
    ConfigLoader as DriverCL


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_chktex_run_checks(script_dir):

    _ERROR_COUNT = 3
    document_path = script_dir + "/resources/T1600.tex"
    chktex_instance = Chktex()

    test_file = TexFile(Path(document_path))

    output_problems = chktex_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) > 0

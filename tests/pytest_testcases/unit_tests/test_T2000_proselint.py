import os

from pathlib import Path

import pytest

from latexbuddy.modules.proselint_checker import ProseLint
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_proselint_run_checks(script_dir):

    _ERROR_COUNT = 7
    document_path = script_dir + "/resources/ConfoundedLearning/main.tex"
    proselint_checker_instance = ProseLint()

    test_file = TexFile(Path(document_path))

    output_problems = proselint_checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == _ERROR_COUNT
    assert str(output_problems[0]) == "Grammar warning on 79:180: o.  : Inconsistent " \
                                      "spacing after period (1 vs. 2 spaces).."
    assert str(output_problems[1]) == "Grammar warning on 85:376: s.  : Inconsistent " \
                                      "spacing after period (1 vs. 2 spaces).."
    assert str(output_problems[2]) == "Grammar warning on 335:45:  in the long run: " \
                                      "'in the long run' is a cliché.."

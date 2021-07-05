import pytest
import os

from pathlib import Path
from latexbuddy.modules.diction import Diction
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import \
    ConfigLoader as DriverCL


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_diction_run_checks(script_dir):

    _ERROR_COUNT = 2
    document_path = script_dir + "/resources/T1700.txt"
    diction_instance = Diction()

    test_file = TexFile(Path(document_path))

    output_problems = diction_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == _ERROR_COUNT
    assert output_problems[0].text == "This Sentence cause a double double Word Error."
    assert output_problems[1].text == "This Sentence causes a Error, thats why its " \
                                      "important."

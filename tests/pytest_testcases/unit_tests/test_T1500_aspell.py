import pytest
import os

from pathlib import Path
from latexbuddy.modules.aspell import Aspell
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import ConfigLoader as DriverCL


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_run_checks(script_dir):

    ERROR_COUNT = 3  # From aspell commandline output
    document_path = script_dir + "/resources/T1500.txt"
    aspell_instance = Aspell()

    test_file = TexFile(Path(document_path))

    output_problems = aspell_instance.run_checks(DriverCL(), test_file)

    assert output_problems[0].text == "speeek"
    assert output_problems[1].text == "tike"
    assert output_problems[2].text == "mesage"
    assert len(output_problems) > 0
    assert len(output_problems) == ERROR_COUNT

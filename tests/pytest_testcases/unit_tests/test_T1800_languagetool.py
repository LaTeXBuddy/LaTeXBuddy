import pytest
import os

from pathlib import Path
from latexbuddy.modules.languagetool import LanguageTool
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import ConfigLoader as DriverCL


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_run_checks_languagetool(script_dir):

    ERROR_COUNT = 2
    document_path = script_dir + "/resources/ConfoundedLearning/main.tex"
    languagetool_instance = LanguageTool()

    test_file = TexFile(Path(document_path))

    output_problems = languagetool_instance.run_checks(DriverCL(), test_file)
    for p in output_problems:
        print(str(p))

    assert len(output_problems) > 0

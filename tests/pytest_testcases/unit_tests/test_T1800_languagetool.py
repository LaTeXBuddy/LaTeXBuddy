import os

from pathlib import Path

import pytest

from latexbuddy.modules.languagetool import LanguageTool
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_languagetool_run_checks(script_dir):
    _ERROR_COUNT = 16
    document_path = script_dir + "/resources/test_paper.tex"
    languagetool_instance = LanguageTool()

    test_file = TexFile(Path(document_path))

    output_problems = languagetool_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == _ERROR_COUNT
    assert (
        str(output_problems[0]) == "Grammar error on 15:43:   : Whitespace "
        "repetition (bad formatting)."
    )
    assert str(output_problems[1]) == 'Grammar error on 19:276: ": Smart quotes (“”).'
    assert str(output_problems[2]) == 'Grammar error on 19:286: ": Smart quotes (“”).'

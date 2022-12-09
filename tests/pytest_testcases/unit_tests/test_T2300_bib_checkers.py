import os

from pathlib import Path

import pytest

from latexbuddy.modules.bib_checkers import BibtexDuplicates, NewerPublications
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_bib_checkers_run_checks(script_dir):

    _ERROR_COUNT_DUP = 2
    _ERROR_COUNT_NEW = 2

    bib_dup_instance = BibtexDuplicates()
    bib_new_instance = NewerPublications()

    document_path = script_dir + "/resources/T2300.tex"
    test_file = TexFile(Path(document_path))

    output_problems_dup = bib_dup_instance.run_checks(DriverCL(), test_file)
    output_problems_new = bib_new_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems_dup) == _ERROR_COUNT_DUP
    assert len(output_problems_dup) == _ERROR_COUNT_NEW

    assert output_problems_dup[0].text == "FirecrackerGithub <=> FirecrackerBlog"
    assert output_problems_dup[1].text == "StatefulDataflow:2014 <=> SFDF"

    assert output_problems_new[0].text == "werner2018serverless"
    assert output_problems_new[1].text == "Anna:2019"

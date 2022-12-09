import os

from pathlib import Path

import pytest

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules.yalafi_checker import YaLafi
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_yalafi_detex_run_checks(script_dir):

    test_document = Path(script_dir + "/resources/T2100_test_document.tex")
    tf = TexFile(test_document)
    cl = ConfigLoader()

    problems = YaLafi().run_checks(cl, tf)

    assert len(problems) == 2
    assert len(problems) == len(tf._parse_problems)

    assert problems == [
        Problem(
            position=(4, 1),
            text="\\verb argument",
            checker=YaLafi,
            p_type="tex2txt",
            file=test_document,
            severity=ProblemSeverity.ERROR,
            category="latex",
            key=YaLafi.display_name + "_tex2txt",
        ),
        Problem(
            position=(6, 7),
            text="missing end of maths",
            checker=YaLafi,
            p_type="tex2txt",
            file=test_document,
            severity=ProblemSeverity.ERROR,
            category="latex",
            key=YaLafi.display_name + "_tex2txt",
        ),
    ]

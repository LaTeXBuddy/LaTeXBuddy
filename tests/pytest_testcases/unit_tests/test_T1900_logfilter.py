import re

import pytest
import os

from pathlib import Path
from tempfile import mkstemp
from tests.pytest_testcases.tools import execute_and_collect
from latexbuddy.modules.logfilter import LogFilter
from latexbuddy.texfile import TexFile
from resources.dummy_config_loader import ConfigLoader


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_all_problems_in_texfilt(script_dir):
    # config_path = script_dir + "/resources/T1900_config.py"
    document_path = Path(script_dir + "/resources/T1900.tex")
    texfilt_path = script_dir + "/latexbuddy/modules/texfilt.awk"
    log_filter = LogFilter()
    config_loader = ConfigLoader()
    tex_file = TexFile(document_path)
    descriptor, raw_problems_path = mkstemp(
        prefix="latexbuddy", suffix="raw_log_errors"
    )

    problems = log_filter.run_checks(config_loader, tex_file)

    cmd = [
        "awk", "-f",
        texfilt_path,
        f"{str(tex_file.log_file)} > {raw_problems_path}",
    ]
    result = execute_and_collect(*cmd)  # not used
    raw_problems = Path(raw_problems_path).read_text()

    test = True
    for problem in problems:
        if not problem.description is None:
            test = test and problem.description in raw_problems
    assert test


def test_unit_all_texfilt_in_problems(script_dir):
    # config_path = script_dir + "/resources/T1900_config.py"
    document_path = Path(script_dir + "/resources/T1900.tex")
    texfilt_path = script_dir + "/latexbuddy/modules/texfilt.awk"
    log_filter = LogFilter()
    config_loader = ConfigLoader()
    tex_file = TexFile(document_path)
    descriptor, raw_problems_path = mkstemp(
        prefix="latexbuddy", suffix="raw_log_errors"
    )

    problems = log_filter.run_checks(config_loader, tex_file)
    problem_line_nos = []
    for problem in problems:
        problem_line_nos.append(problem.position[0])

    cmd = [
        "awk", "-f",
        texfilt_path,
        f"{str(tex_file.log_file)} > {raw_problems_path}",
    ]
    result = execute_and_collect(*cmd)  # not used
    raw_problems = Path(raw_problems_path).read_text()
    texfilt_problems_split = raw_problems.split(' ')
    problem_re = re.compile(
        r"(?P<line_no>\d+):"
    )

    test = True
    for problem in texfilt_problems_split:
        match = problem_re.match(problem)
        if not match:
            continue
        line_no = match.group('line_no')
        test = test and line_no in problem_line_nos
    assert test


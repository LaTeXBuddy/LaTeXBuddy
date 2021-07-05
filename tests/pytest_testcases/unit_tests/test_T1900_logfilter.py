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


def test_all_problems_in_texfilt(script_dir):
    # config_path = script_dir + "/resources/T1900_config.py"
    document_path = script_dir + "/resources/T1900.tex"
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


def test_all_texfilt_in_problems(script_dir):
    # config_path = script_dir + "/resources/T1900_config.py"
    document_path = script_dir + "/resources/T1900.tex"
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


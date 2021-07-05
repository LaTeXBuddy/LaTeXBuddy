import pytest
import os

from pathlib import Path
from tests.pytest_testcases.tools import execute_and_collect


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_run_checks(script_dir):
    config_path = script_dir + "/resources/T1900_config.py"
    document_path = script_dir + "/resources/T1900.tex"

    output_path = script_dir + "../../../latexbuddy_html/latexbuddy_output.json"

    buddy_run = [
        "latexbuddy",
        "--config", config_path,
        "--format", "JSON",
        document_path,
    ]
    run_output = execute_and_collect(*buddy_run)
    Path('output_T1900.test').write_text(run_output)
    assert len(run_output) > 0

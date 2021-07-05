import pytest
import os

from pathlib import Path
from tests.pytest_testcases.tools import execute_and_collect

@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])

def test_run_checks(script_dir):
    config_path = script_dir + "/resources/T1900_config.py"
    document_path = script_dir + "/resources/T1900_test_document.tex"

    output_path = script_dir + "../../../latexbuddy_html"

    buddy_run = [
        "latexbuddy",
        "--config", config_path,
        "--format", "JSON",
        "--output", output_path,
        document_path,
    ]
    run_output = execute_and_collect(*buddy_run)    # not used
    assert len(run_output) > 0
    output_json = [
        'cat',
        output_path + '/T1900_test_document.json'
    ]
    json_output = execute_and_collect(*output_json)
    assert len(json_output) > 0

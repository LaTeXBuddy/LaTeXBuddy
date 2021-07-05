import pytest
from tests.pytest_testcases.tools import execute_and_collect


def test_run_checks(script_dir):
    config_path = script_dir + "/resources/T1900_config.py"
    document_path = script_dir + "/resources/T1900_test_document.tex"

    output_path = script_dir + "../../../latexbuddy_html"

    cmd = [
        "latexbuddy",
        "--verbose",
        "--config", config_path,
        "--format", "JSON",
        "--output", output_path,
        document_path,
    ]
    result = execute_and_collect(*cmd)

import os

from pathlib import Path

import pytest

from tests.pytest_testcases.tools import execute_and_collect


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_integration_buddy_cli(script_dir):
    config_path = script_dir + "/resources/T700_config.py"
    whitelist_path = script_dir + "/resources/T700_whitelist"
    document_path = script_dir + "/resources/T700_test_document.tex"

    output_path = script_dir + "../../../latexbuddy_html"

    cmd = [
        "latexbuddy",
        "--verbose",
        "--config",
        config_path,
        "--whitelist",
        whitelist_path,
        "--output",
        output_path,
        document_path,
    ]
    result = execute_and_collect(*cmd)

    # asserting that both driver modules have been executed correctly
    assert "FirstDriver started checks" in result
    assert "SecondDriver started checks" in result
    assert "FirstDriver finished after" in result
    assert "SecondDriver finished after" in result

    # asserting that the whitelist-check has been executed correctly
    assert "Beginning whitelist-check..." in result
    assert "Finished whitelist-check in" in result

    # asserting that the output file was saved correctly
    assert "Output saved to " in result

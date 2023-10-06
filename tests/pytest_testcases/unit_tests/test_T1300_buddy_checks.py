import argparse
import os
import tempfile

from pathlib import Path
from typing import List

import pytest

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleProvider
from latexbuddy.modules import Module
from tests.pytest_testcases.unit_tests.resources.T1300_dummy_modules.dummy_module import (
    DummyModule0,
    DummyModule1,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


@pytest.fixture
def temp_dir():
    return tempfile.mkdtemp()


@pytest.fixture
def config_loader(script_dir, temp_dir):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=str)
    parser.add_argument("--format", type=str)

    return ConfigLoader(
        parser.parse_args(
            [
                "--config",
                script_dir + "/resources/nonexistent_config.py",
                "--output",
                temp_dir,
                "--format",
                "JSON",
            ]
        )
    )


class DriverModuleProvider(ModuleProvider):
    def load_selected_modules(self, cfg: ConfigLoader) -> List[Module]:
        return [DummyModule0(), DummyModule1()]


def test_unit_buddy_checks(script_dir, config_loader):
    file_str = script_dir + "/resources/T1300_test_document.tex"
    file = Path(file_str)

    LatexBuddy.init(
        config_loader,
        DriverModuleProvider(),
        file,
        [file],
    )

    LatexBuddy.run_tools()
    LatexBuddy.output_file()

    temp_dir = config_loader.get_config_option(LatexBuddy, "output")

    with open(temp_dir + "/latexbuddy_output.json") as f:
        json_contents = f.read()

    assert (
        "\n" + json_contents + "\n"
        == """
[
    {
        "position": [
            1,
            1
        ],
        "text": "text",
        "checker": "DummyModule0",
        "p_type": "my_problem_id",
        "file": "{file_str}",
        "severity": "error",
        "length": 4,
        "category": "dumb mistakes",
        "description": "this is a test error, please ignore it...",
        "context": [
            "",
            "totally made up"
        ],
        "suggestions": [
            "idk",
            "try harder next time"
        ],
        "key": "my_very_unique_key"
    },
    {
        "position": [
            1,
            2
        ],
        "text": "text2",
        "checker": "DummyModule0",
        "p_type": "",
        "file": "{file_str}",
        "severity": "warning",
        "length": 5,
        "category": null,
        "description": null,
        "context": [
            "",
            ""
        ],
        "suggestions": [],
        "key": "DummyModule0__text2"
    }
]
""".replace(
            "{file_str}", file_str
        )
    )

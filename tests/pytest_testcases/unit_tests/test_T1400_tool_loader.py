import argparse
import os

from pathlib import Path

import pytest

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleLoader
from tests.pytest_testcases.unit_tests.resources.T1400_dummy_modules.dummy_module_0 import (
    DummyModule0,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


@pytest.fixture
def config_loader(script_dir):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)

    return ConfigLoader(
        parser.parse_args(
            ["--config", script_dir + "/resources/T1400_config.py"],
        ),
    )


def test_unit_tool_loader(config_loader):

    module_loader = ModuleLoader(
        Path("tests/pytest_testcases/unit_tests/resources/T1400_dummy_modules/"),
    )

    modules = module_loader.load_selected_modules(config_loader)

    assert len(modules) == 1
    assert type(modules[0]) == DummyModule0

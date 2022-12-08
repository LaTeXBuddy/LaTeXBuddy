import argparse
import os
import tempfile

from pathlib import Path
from typing import AnyStr

import pytest

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules.aspell import Aspell
from latexbuddy.problem import Problem, ProblemSeverity
from tests.pytest_testcases.integration_tests.resources.T800_driver_ModuleProvider import (
    DriverModuleProvider,
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

    return ConfigLoader(
        parser.parse_args(
            [
                "--config", script_dir + "/resources/T1000_config.py",
                "--output", temp_dir,
            ],
        ),
    )


@pytest.fixture
def problem_list(script_dir):
    return (
        [
            Problem(
                (4, 7),
                "document",
                Aspell,
                Path(script_dir + "/resources/T1000_test_document.tex"),
                ProblemSeverity.ERROR,
                description="Hi, I am a problem...",
                suggestions=["ldkjfnglsdbliv"],
            ),
            Problem(
                (5, 21),
                "packages",
                Aspell,
                Path(script_dir + "/resources/T1000_test_document.tex"),
                ProblemSeverity.WARNING,
                description="Hi, I am a problem too...",
                suggestions=["goijsfzchbsrlt"],
            ),
        ], ["ldkjfnglsdbliv", "goijsfzchbsrlt"],
    )


def test_integration_buddy_frontend(script_dir, problem_list, config_loader):

    LatexBuddy.init(
        config_loader,
        DriverModuleProvider(),
        Path(script_dir + "/resources/T1000_test_document.tex"),
        [Path(script_dir + "/resources/T1000_test_document.tex")],
    )

    for problem in problem_list[0]:
        LatexBuddy.add_error(problem)

    LatexBuddy.output_html()

    temp_dir = config_loader.get_config_option(LatexBuddy, "output", verify_type=AnyStr)

    with open(temp_dir + "/output_T1000_test_document.html") as file:
        contents = file.read()

        for suggestion_code in problem_list[1]:
            assert suggestion_code in contents

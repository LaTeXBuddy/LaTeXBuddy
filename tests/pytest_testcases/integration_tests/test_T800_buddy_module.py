import os

from logging import DEBUG
from pathlib import Path

import pytest

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem, ProblemSeverity
from tests.pytest_testcases.integration_tests.resources.T800_driver_ModuleProvider import (
    DriverModule1,
    DriverModuleProvider,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


@pytest.fixture
def default_config_loader():
    return ConfigLoader()


def test_integration_buddy_module(script_dir, caplog, default_config_loader):
    # initializing logger on DEBUG level
    caplog.set_level(DEBUG)

    LatexBuddy.init(
        default_config_loader,
        DriverModuleProvider(),
        Path(script_dir + "/resources/T800_test_document.tex"),
        [Path(script_dir + "/resources/T800_test_document.tex")],
    )

    LatexBuddy.run_tools()

    records = "\n".join([record.message for record in caplog.records])

    # asserting that buddy-module communication worked and checks have been started
    assert "Returning scripted module instances." in records
    assert "Using multiprocessing pool with " in records

    # asserting that the correct problem has been returned (unfortunately, due to the
    # checking process being parallelized, the logs during the checks are unavailable)

    problem_list = [problem for uid, problem in LatexBuddy.instance.errors.items()]
    assert len(problem_list) == 1

    assert problem_list[0] == Problem(
        position=None,
        text="just a general problem",
        checker=DriverModule1,
        file=LatexBuddy.instance.tex_file.plain_file,
        severity=ProblemSeverity.INFO,
    )

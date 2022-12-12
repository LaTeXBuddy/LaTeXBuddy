from __future__ import annotations

import os
from logging import DEBUG
from pathlib import Path

import pytest

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleLoader


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


@pytest.fixture
def default_config_loader():
    return ConfigLoader()


def test_integration_buddy_tool_loader(script_dir, caplog, default_config_loader):
    # initializing logger on DEBUG level
    caplog.set_level(DEBUG)

    LatexBuddy.init(
        default_config_loader,
        ModuleLoader(Path("latexbuddy/modules/")),
        Path(script_dir + "/resources/T900_test_document.tex"),
        [Path(script_dir + "/resources/T900_test_document.tex")],
    )

    LatexBuddy.run_tools()

    records = "\n".join([record.message for record in caplog.records])

    # asserting that all available modules are being executed (since there is no
    # config file that disables any modules)

    assert (
        "Executing the following modules in parallel: ['Aspell', "
        "'BibtexDuplicates', 'NewerPublications', 'Chktex', 'Diction', "
        "'LanguageTool', 'LogFilter', 'CheckFigureResolution', 'EmptySections',"
        " 'NativeUseOfRef', 'SiUnitx', 'URLCheck', 'UnreferencedFigures',"
        " 'ProseLint', 'YaLafi']" in records
    )

#  LaTeXBuddy - a LaTeX checking tool
#  Copyright (c) 2023  LaTeXBuddy
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleProvider
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile


class DummyModule0(Module):
    def __init__(self):
        pass

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        return [
            Problem(
                (1, 1),
                "text",
                DummyModule0,
                file.tex_file,
                ProblemSeverity.ERROR,
                "my_problem_id",
                category="dumb mistakes",
                description="this is a test error, please ignore it...",
                context=("", "totally made up"),
                suggestions=["idk", "try harder next time"],
                key="my_very_unique_key",
            ),
        ]


class DummyModule1(Module):
    def __init__(self):
        pass

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        return [
            Problem(
                (1, 2),
                "text2",
                DummyModule0,
                file.tex_file,
                ProblemSeverity.WARNING,
            ),
        ]


_DOCUMENT_CONTENTS = R"""\documentclass{article}

\begin{document}
First document. This is a simple example, with no
extra parameters or packages included.
\end{document}
"""


@pytest.fixture
def file(tmp_path: Path) -> Path:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return document


@pytest.fixture
def config_loader(tmp_path, tmp_path_factory) -> ConfigLoader:
    return


class DriverModuleProvider(ModuleProvider):
    def load_selected_modules(self, cfg: ConfigLoader) -> list[Module]:
        return [DummyModule0(), DummyModule1()]


@pytest.mark.xfail(
    reason="Integration test may fail if unit tests do",
    strict=False,
)
def test_run_checks(
    tmp_path: Path,
    output_dir, file: Path,
) -> None:
    config_loader = ConfigLoader(
        Namespace(
            config=(tmp_path / 'config_does_not_exist.py'),
            output=str(output_dir),
            format="JSON",
        ),
    )
    LatexBuddy.init(
        config_loader,
        DriverModuleProvider(),
        file,
        [file],
        compile_tex=False,
    )
    LatexBuddy.run_tools()
    LatexBuddy.output_file()

    parsed_output_dir = config_loader.get_config_option(LatexBuddy, "output")
    output_file = (Path(parsed_output_dir) / "latexbuddy_output.json")
    with output_file.open() as f:
        actual = json.load(f)

    assert actual == [
        {
            "position": [
                1,
                1,
            ],
            "text": "text",
            "checker": "DummyModule0",
            "p_type": "my_problem_id",
            "file": str(file),
            "severity": "error",
            "length": 4,
            "category": "dumb mistakes",
            "description": "this is a test error, please ignore it...",
            "context": [
                "",
                "totally made up",
            ],
            "suggestions": [
                "idk",
                "try harder next time",
            ],
            "key": "my_very_unique_key",
        },
        {
            "position": [
                1,
                2,
            ],
            "text": "text2",
            "checker": "DummyModule0",
            "p_type": "",
            "file": str(file),
            "severity": "warning",
            "length": 5,
            "category": None,
            "description": None,
            "context": [
                "",
                "",
            ],
            "suggestions": [],
            "key": "DummyModule0__text2",
        },
    ]

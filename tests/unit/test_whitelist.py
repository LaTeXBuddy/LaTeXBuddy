# LaTeXBuddy tests
# Copyright (C) 2021-2022  LaTeXBuddy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleProvider
from latexbuddy.modules import Module
from latexbuddy.modules.aspell import Aspell
from latexbuddy.problem import Problem

_DOCUMENT_CONTENTS = r"""\documentclass{article}
\begin{document}
First document. This is a simple example, with no
extra parameters or packages included.
\end{document}
"""

_WHITELIST_CONTENTS = r"""en_spelling_Dongbei
"""

_CONFIG_CONTENTS = r"""main = {
    "language": "en",
    "language_country": "GB",
    "whitelist": "{{WHITELIST}}",
    "output": "{{OUTPUT}}",
}

modules = {}
"""


@pytest.fixture
def document(tmp_path: Path) -> Path:
    document = tmp_path / "document.tex"
    document.write_text(_DOCUMENT_CONTENTS)
    return document


@pytest.fixture(scope="function")
def whitelist(tmp_path: Path) -> Path:
    whitelist = tmp_path / "whitelist.txt"
    whitelist.write_text(_WHITELIST_CONTENTS)
    return whitelist


@pytest.fixture(scope="function")
def config(tmp_path: Path, whitelist: Path) -> Path:
    config = tmp_path / "config.py"
    config.write_text(
        _CONFIG_CONTENTS
        .replace("{{WHITELIST}}", str(whitelist.resolve()))
        .replace("{{OUTPUT}}", str(tmp_path.resolve())),
    )
    return config


@pytest.fixture
def config_loader(config: Path, tmp_path: Path) -> ConfigLoader:
    return ConfigLoader(
        argparse.Namespace(
            config=config,
            output=tmp_path,
        ),
    )


@pytest.fixture
def module_provider() -> ModuleProvider:
    class DummyModuleProvider(ModuleProvider):
        def load_selected_modules(self, cfg: ConfigLoader) -> list[Module]:
            return []

    return DummyModuleProvider()


@pytest.fixture
def buddy(
    document: Path,
    config_loader: ConfigLoader,
    module_provider: ModuleProvider,
) -> LatexBuddy:
    LatexBuddy.init(
        config_loader,
        module_provider,
        document,
        [document],
        compile_tex=False,
    )
    return LatexBuddy.instance


def init_buddy(
    source_dir: Path,
    config_loader: ConfigLoader,
    module_provider: ModuleProvider,
) -> None:
    file = source_dir / "resources/T1200_test_document.tex"

    LatexBuddy.init(
        config_loader,
        module_provider,
        file,
        [file],
        compile_tex=False,
    )


@pytest.mark.parametrize(
    "to_apply,expected_post", [
        (True, 0),
        (False, 1),
    ],
)
def test_whitelist_filter(
    buddy: LatexBuddy,
    document: Path,
    to_apply: bool,
    expected_post: int,
) -> None:
    word = "Dongbei" if to_apply else "Dongbeiii"
    buddy.add_error(
        Problem(
            (1, 1),
            word,
            Aspell,
            document,
            key=f"en_spelling_{word}",
        ),
    )

    assert len(buddy.errors) == 1

    buddy.check_whitelist()

    assert len(buddy.errors) == expected_post


@pytest.mark.parametrize(
    "add_uid,expected_post,line_diff", [
        (True, 0, 1),
        (False, 1, 0),
    ],
)
def test_add_to_whitelist(
    buddy: LatexBuddy,
    add_uid: bool,
    expected_post: int,
    line_diff: int,
) -> None:
    assert buddy.whitelist_file is not None
    old_whitelist = buddy.whitelist_file.read_text().splitlines()
    old_line_count = len(old_whitelist)

    problem = Problem(
        (1, 1),
        "Dongbeiii",
        Aspell,
        Path("/"),
        key="en_spelling_Dongbeiii",
    )
    buddy.add_error(problem)

    assert len(buddy.errors) == 1

    buddy.add_to_whitelist(
        list(buddy.errors.keys())[0] if add_uid else "invalid",
    )

    assert len(LatexBuddy.instance.errors) == expected_post

    new_whitelist = buddy.whitelist_file.read_text().splitlines()
    new_line_count = len(new_whitelist)

    # If the uid was correct, its key was added to the whitelist.
    # Else, the whitelist shouldn't have changed.
    assert new_line_count == old_line_count + line_diff
    for line in old_whitelist:
        assert line in new_whitelist
    if add_uid:
        assert problem.key in new_whitelist
